"""ExtractionService — 収集ページからの構造化データ抽出

既存の analysis/service.py の _extract_structured() をラップし、
page_versions から LLM 向けコンテキストを構築して構造化データを返す。
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.analysis.service import _extract_structured
from src.analysis.schemas import StructuredData
from src.db.models import Page, PageVersion
from src.db.repository import CompanyRepository
from src.shared.exceptions import AnalysisError
from src.shared.logger import logger
from src.shared.text import build_llm_context


class ExtractionService:
    """収集ページからの構造化データ抽出を担うサービス層。

    既存の _extract_structured() をラップし、page_versions テーブルに
    保存済みのページコンテンツから LLM 向けコンテキストを構築して
    構造化データ（StructuredData）を返す。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._company_repo = CompanyRepository(session)

    async def extract(
        self,
        company_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> StructuredData:
        """page_versions から構造化データを抽出する。

        1. Company レコードから primary_url を取得
        2. 当該企業の最新 page_versions を取得
        3. page_versions の extracted_text から LLM 向けコンテキストを構築
        4. 既存の _extract_structured() で構造化データを抽出
        5. 企業名が抽出できた場合は display_name を更新

        Args:
            company_id: 対象企業の ID
            run_id: 紐づく AnalysisRun の ID

        Returns:
            StructuredData: LLM が抽出した構造化データ

        Raises:
            AnalysisError: 抽出に失敗した場合
        """
        # 1. 企業レコード取得
        company = await self._company_repo.find_by_id(company_id)
        if company is None:
            raise AnalysisError(f"企業が見つかりません: {company_id}")

        logger.info(
            "構造化抽出開始: company_id={}, url={}",
            company_id,
            company.primary_url,
        )

        # 2. 当該企業の最新 page_versions を取得
        page_versions = await self._fetch_latest_page_versions(company_id, run_id)

        if not page_versions:
            raise AnalysisError(
                f"抽出対象のページが見つかりません: company_id={company_id}"
            )

        # 3. LLM 向けコンテキストを構築
        raw_content = self._build_context(page_versions)

        logger.info(
            "LLMコンテキスト構築完了: {} ページ, {} 文字",
            len(page_versions),
            len(raw_content),
        )

        # 4. 既存の _extract_structured() で構造化データを抽出
        structured = await _extract_structured(company.primary_url, raw_content)

        # 5. 企業名が抽出できた場合は display_name を更新
        if structured.company_profile.name:
            company.display_name = structured.company_profile.name
            await self._session.flush()

        logger.info(
            "構造化抽出完了: company_id={}, company_name={}",
            company_id,
            structured.company_profile.name or "(未取得)",
        )

        return structured

    async def _fetch_latest_page_versions(
        self,
        company_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> list[PageVersion]:
        """企業に紐づく page_versions を取得する。

        run_id に紐づくバージョンを優先的に取得する。
        run_id に紐づくバージョンがない場合は、各ページの最新バージョンを取得する。
        """
        # まず run_id に紐づく page_versions を取得（直前のクロールで保存されたもの）
        result = await self._session.execute(
            select(PageVersion)
            .join(Page, PageVersion.page_id == Page.page_id)
            .where(
                Page.company_id == company_id,
                PageVersion.fetch_run_id == run_id,
            )
            .order_by(PageVersion.fetched_at.desc())
        )
        versions = list(result.scalars().all())

        if versions:
            return versions

        # run_id に紐づくバージョンがない場合、各ページの最新バージョンを取得
        # （Deep Analysis など、既存の蓄積データを使うケース）
        result = await self._session.execute(
            select(Page)
            .options(selectinload(Page.versions))
            .where(Page.company_id == company_id, Page.is_active.is_(True))
        )
        pages = list(result.scalars().all())

        latest_versions: list[PageVersion] = []
        for page in pages:
            if page.versions:
                # fetched_at が最新のバージョンを選択
                latest = max(page.versions, key=lambda v: v.fetched_at)
                latest_versions.append(latest)

        return latest_versions

    @staticmethod
    def _build_context(page_versions: list[PageVersion]) -> str:
        """page_versions の extracted_text から LLM 向けコンテキスト文字列を構築する。

        既存の build_llm_context() と同じ形式のセクションリストを作成し、
        カテゴリ別にグルーピングされたコンテキストを返す。
        """
        sections: list[dict[str, str]] = []
        for version in page_versions:
            # page リレーションからカテゴリ・URL 情報を取得
            page = version.page
            sections.append(
                {
                    "category": page.page_type or "その他" if page else "その他",
                    "title": version.title or (page.title if page else "") or "",
                    "url": page.url if page else "",
                    "content": version.extracted_text,
                }
            )

        return build_llm_context(sections)
