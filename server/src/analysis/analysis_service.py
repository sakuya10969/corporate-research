"""AnalysisService — 要約・SWOT・スコアリング・レポート生成

既存の analysis/service.py の _generate_summary_and_scores() をラップし、
分析結果（summary, scores, markdown_page, diff_report）を生成・保存する。
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.analysis.schemas import (
    SourceInfo,
    StructuredData,
)
from src.analysis.service import _generate_summary_and_scores
from src.db.models import AnalysisResult as AnalysisResultModel
from src.db.models import AnalysisRun, Page, PageVersion
from src.db.repository import (
    AnalysisResultRepository,
    AnalysisRunRepository,
    CompanyRepository,
)
from src.extraction.service import ExtractionService
from src.shared.config import get_settings
from src.shared.exceptions import AnalysisError
from src.shared.logger import logger
from src.shared.text import generate_diff_report, generate_markdown_report


class AnalysisService:
    """要約・SWOT・スコアリング・レポート生成を担うサービス層。

    既存の _generate_summary_and_scores() をラップし、分析結果を
    analysis_results テーブルに保存する。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._company_repo = CompanyRepository(session)
        self._result_repo = AnalysisResultRepository(session)
        self._run_repo = AnalysisRunRepository(session)

    async def analyze(
        self,
        company_id: uuid.UUID,
        run_id: uuid.UUID,
        template: str = "general",
        structured: StructuredData | None = None,
    ) -> AnalysisResultModel:
        """構造化データから要約・スコア・レポートを生成し、結果を保存する。

        1. Company レコードから primary_url を取得
        2. structured が未指定の場合、page_versions から再抽出
        3. _generate_summary_and_scores() で要約・スコアを生成
        4. markdown_page を生成
        5. 前回結果がある場合は diff_report を生成
        6. analysis_results に保存
        7. Company の last_analyzed_at, analysis_count を更新

        Args:
            company_id: 対象企業の ID
            run_id: 紐づく AnalysisRun の ID
            template: 分析テンプレート
            structured: 構造化データ（省略時は page_versions から再抽出）

        Returns:
            AnalysisResultModel: 保存された分析結果

        Raises:
            AnalysisError: 分析に失敗した場合
        """
        # 1. 企業レコード取得
        company = await self._company_repo.find_by_id(company_id)
        if company is None:
            raise AnalysisError(f"企業が見つかりません: {company_id}")

        logger.info(
            "分析開始: company_id={}, url={}, template={}",
            company_id,
            company.primary_url,
            template,
        )

        # 2. structured が未指定の場合、ExtractionService で再抽出
        if structured is None:
            extraction_service = ExtractionService(self._session)
            structured = await extraction_service.extract(company_id, run_id)

        start_ms = time.monotonic()

        # 3. 既存の _generate_summary_and_scores() で要約・スコアを生成
        summary, scores = await _generate_summary_and_scores(
            company.primary_url, structured, template
        )

        elapsed_ms = int((time.monotonic() - start_ms) * 1000)

        structured_dict = structured.model_dump()
        summary_dict = summary.model_dump()

        # 4. ソース情報を page_versions から構築
        sources, sources_dict = await self._build_sources(company_id, run_id)

        # 5. markdown_page を生成
        markdown_page = generate_markdown_report(
            company_url=company.primary_url,
            structured=structured_dict,
            summary=summary_dict,
            sources=sources_dict,
        )

        # 6. diff_report を生成（前回結果がある場合）
        diff_report = await self._generate_diff(company_id, structured_dict)

        # 7. 企業名が抽出できた場合は display_name を更新
        if structured.company_profile.name:
            company.display_name = structured.company_profile.name

        # 8. analysis_results に保存
        settings = get_settings()
        result_model = AnalysisResultModel(
            company_id=company_id,
            run_id=run_id,
            template=template,
            llm_model=settings.azure_deployment,
            llm_api_version=settings.api_version,
            structured=structured_dict,
            summary=summary_dict,
            scores=scores.model_dump() if scores else None,
            diff_report=diff_report or None,
            sources=sources_dict,
            raw_sources=[],
            pages_used=len(sources_dict),
            markdown_page=markdown_page,
            quality_metrics={
                "processing_ms": elapsed_ms,
            },
        )
        result_model = await self._result_repo.save(result_model)

        # 9. Company の last_analyzed_at, analysis_count を更新
        now = datetime.now(timezone.utc)
        company.last_analyzed_at = now
        company.analysis_count = (company.analysis_count or 0) + 1
        await self._session.flush()

        logger.info(
            "分析完了: company_id={}, result_id={}, {}ms",
            company_id,
            result_model.result_id,
            elapsed_ms,
        )

        return result_model

    async def run_deep_analysis(
        self,
        company_id: uuid.UUID,
        template: str,
    ) -> AnalysisResultModel:
        """蓄積データに対するテンプレート別再分析。フルクロールなし。

        1. Company レコードの存在確認
        2. 新しい AnalysisRun（run_type="deep_analysis"）を作成
        3. ExtractionService で蓄積 page_versions から構造化データを抽出
        4. analyze() で要約・スコア・レポートを生成・保存
        5. AnalysisRun を completed に更新

        Args:
            company_id: 対象企業の ID
            template: 分析テンプレート

        Returns:
            AnalysisResultModel: 保存された分析結果

        Raises:
            AnalysisError: 分析に失敗した場合
        """
        # 1. 企業レコードの存在確認
        company = await self._company_repo.find_by_id(company_id)
        if company is None:
            raise AnalysisError(f"企業が見つかりません: {company_id}")

        logger.info(
            "Deep Analysis 開始: company_id={}, template={}",
            company_id,
            template,
        )

        # 2. 新しい AnalysisRun を作成
        run = AnalysisRun(
            company_id=company_id,
            run_type="deep_analysis",
            template=template,
            status="running",
            started_at=datetime.now(timezone.utc),
            input_params={
                "template": template,
                "deep_analysis": True,
            },
        )
        run = await self._run_repo.create(run)

        try:
            # 3. ExtractionService で蓄積データから構造化データを抽出
            extraction_service = ExtractionService(self._session)
            structured = await extraction_service.extract(company_id, run.run_id)

            # 4. analyze() で要約・スコア・レポートを生成・保存
            result = await self.analyze(
                company_id=company_id,
                run_id=run.run_id,
                template=template,
                structured=structured,
            )

            # 5. AnalysisRun を completed に更新
            await self._run_repo.update_status(
                run,
                "completed",
                collection_summary={
                    "deep_analysis": True,
                    "template": template,
                },
            )

            logger.info(
                "Deep Analysis 完了: company_id={}, run_id={}, result_id={}",
                company_id,
                run.run_id,
                result.result_id,
            )

            return result

        except Exception as e:
            # エラー時は AnalysisRun を failed に更新
            error_code = "ANALYSIS_ERROR"
            if isinstance(e, AnalysisError):
                error_code = "ANALYSIS_ERROR"
            await self._run_repo.update_status(
                run,
                "failed",
                error_code=error_code,
                error_message=str(e),
            )
            logger.error(
                "Deep Analysis 失敗: company_id={}, error={}",
                company_id,
                e,
            )
            raise

    async def _build_sources(
        self,
        company_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> tuple[list[SourceInfo], list[dict]]:
        """page_versions からソース情報を構築する。

        run_id に紐づく page_versions を優先的に取得し、
        ない場合は各ページの最新バージョンを取得する。

        Returns:
            tuple: (SourceInfo リスト, dict リスト)
        """
        # run_id に紐づく page_versions を取得
        result = await self._session.execute(
            select(PageVersion)
            .join(Page, PageVersion.page_id == Page.page_id)
            .options(selectinload(PageVersion.page))
            .where(
                Page.company_id == company_id,
                PageVersion.fetch_run_id == run_id,
            )
            .order_by(PageVersion.fetched_at.desc())
        )
        versions = list(result.scalars().all())

        if not versions:
            # run_id に紐づくバージョンがない場合、各ページの最新バージョンを取得
            result = await self._session.execute(
                select(Page)
                .options(selectinload(Page.versions))
                .where(Page.company_id == company_id, Page.is_active.is_(True))
            )
            pages = list(result.scalars().all())
            versions = []
            for page in pages:
                if page.versions:
                    latest = max(page.versions, key=lambda v: v.fetched_at)
                    versions.append(latest)

        sources: list[SourceInfo] = []
        sources_dict: list[dict] = []
        for version in versions:
            page = version.page
            source = SourceInfo(
                url=page.url if page else "",
                title=version.title or (page.title if page else "") or "",
                category=page.page_type or "その他" if page else "その他",
            )
            sources.append(source)
            sources_dict.append(source.model_dump())

        return sources, sources_dict

    async def _generate_diff(
        self,
        company_id: uuid.UUID,
        current_structured: dict,
    ) -> str:
        """前回の分析結果との差分レポートを生成する。

        前回結果がない場合は空文字列を返す。
        """
        previous = await self._result_repo.find_latest_by_company(company_id)
        if previous is None:
            return ""

        return generate_diff_report(current_structured, previous.structured)
