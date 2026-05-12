"""分析サービス — 永続化・キャッシュ・差分・テンプレート・スコアリング対応

新サービス層（CompanyService, CrawlService, ExtractionService, AnalysisService）を
内部で呼び出し、既存の同期的な動作と AnalysisResponse スキーマとの後方互換性を維持する。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.analysis_service import AnalysisService
from src.analysis.converters import model_to_response as _model_to_response
from src.analysis.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    RawSource,
)
from src.companies.service import CompanyService
from src.crawler.service import CrawlService
from src.db.models import AnalysisRun, Page, PageVersion
from src.db.repository import (
    AnalysisResultRepository,
    AnalysisRunRepository,
    CompanyRepository,
)
from src.extraction.service import ExtractionService
from src.shared.exceptions import AnalysisError, CollectionError
from src.shared.logger import logger


async def analyze_company(
    request: AnalysisRequest, session: AsyncSession
) -> AnalysisResponse:
    """企業分析メインフロー（永続化・キャッシュ対応）

    内部で CompanyService, CrawlService, ExtractionService, AnalysisService を
    呼び出し、既存の同期的な動作（レスポンスを待って返す）を維持する。
    既存の AnalysisResponse スキーマとの後方互換性を維持する。
    """
    logger.info(
        "分析開始: {} (force_refresh={}, template={})",
        request.company_url,
        request.force_refresh,
        request.template,
    )

    # --- サービス初期化 ---
    company_service = CompanyService(session)
    crawl_service = CrawlService(session)
    extraction_service = ExtractionService(session)
    analysis_service = AnalysisService(session)
    result_repo = AnalysisResultRepository(session)
    run_repo = AnalysisRunRepository(session)

    # --- キャッシュチェック ---
    company_repo = CompanyRepository(session)
    existing_company = await company_repo.find_by_url(request.company_url)
    if existing_company and not request.force_refresh:
        cached = await result_repo.find_latest_by_company(existing_company.company_id)
        if cached:
            logger.info("キャッシュヒット: {}", request.company_url)
            return _model_to_response(cached, is_cached=True)

    # --- 企業登録（CompanyService） ---
    company = await company_service.register_company(request.company_url)

    # --- AnalysisRun 作成 ---
    run_type = "refresh" if (existing_company and request.force_refresh) else "initial"
    run = AnalysisRun(
        company_id=company.company_id,
        run_type=run_type,
        template=request.template,
        status="running",
        started_at=datetime.now(timezone.utc),
        force_refresh=request.force_refresh,
        input_params={
            "company_url": request.company_url,
            "template": request.template,
            "force_refresh": request.force_refresh,
        },
    )
    run = await run_repo.create(run)

    # --- クロール（CrawlService） ---
    try:
        crawl_result = await crawl_service.crawl(company.company_id, run.run_id)
    except CollectionError as exc:
        await run_repo.update_status(
            run,
            "failed",
            error_code="COLLECTION_ERROR",
            error_message=str(exc),
        )
        await session.commit()
        raise

    logger.info("情報収集完了: {} 件のソース", crawl_result.pages_collected)

    # --- 構造化抽出（ExtractionService） ---
    try:
        structured = await extraction_service.extract(company.company_id, run.run_id)
    except AnalysisError as exc:
        await run_repo.update_status(
            run,
            "failed",
            error_code="ANALYSIS_ERROR",
            error_message=str(exc),
        )
        await session.commit()
        raise

    # --- 分析（AnalysisService） ---
    try:
        result_model = await analysis_service.analyze(
            company_id=company.company_id,
            run_id=run.run_id,
            template=request.template,
            structured=structured,
        )
    except AnalysisError as exc:
        await run_repo.update_status(
            run,
            "failed",
            error_code="ANALYSIS_ERROR",
            error_message=str(exc),
        )
        await session.commit()
        raise

    # --- raw_sources の補完（後方互換性のため） ---
    # AnalysisService は raw_sources=[] で保存するため、
    # レガシーフローでは page_versions からコンテンツを取得して補完する
    raw_sources_data = await _build_raw_sources(session, company.company_id, run.run_id)
    if raw_sources_data:
        result_model.raw_sources = raw_sources_data
        await session.flush()

    # --- AnalysisRun を完了に更新 ---
    source_categories: dict[str, int] = {}
    for src_info in crawl_result.sources:
        cat = src_info.get("category", "その他")
        source_categories[cat] = source_categories.get(cat, 0) + 1

    await run_repo.update_status(
        run,
        "completed",
        collection_summary={
            "pages_fetched": crawl_result.pages_collected,
            "source_categories": source_categories,
        },
    )

    await session.commit()

    logger.info("分析完了: {}", request.company_url)
    return _model_to_response(result_model, is_cached=False)


async def _build_raw_sources(
    session: AsyncSession,
    company_id: uuid.UUID,
    run_id: uuid.UUID,
) -> list[dict]:
    """page_versions から raw_sources データを構築する（後方互換性のため）。

    レガシーフローでは AnalysisResponse.raw_sources にページコンテンツを含める
    必要があるため、CrawlService が保存した page_versions から復元する。
    """
    result = await session.execute(
        select(PageVersion)
        .join(Page, PageVersion.page_id == Page.page_id)
        .where(
            Page.company_id == company_id,
            PageVersion.fetch_run_id == run_id,
        )
        .order_by(PageVersion.fetched_at.desc())
    )
    versions = list(result.scalars().all())

    raw_sources: list[dict] = []
    for version in versions:
        page = version.page
        raw_sources.append(
            RawSource(
                url=page.url if page else "",
                title=version.title or (page.title if page else "") or "",
                content=version.extracted_text or "",
                category=page.page_type or "その他" if page else "その他",
            ).model_dump()
        )

    return raw_sources
