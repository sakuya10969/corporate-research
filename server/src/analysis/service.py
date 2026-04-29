"""分析サービス — 永続化・キャッシュ・差分・テンプレート・スコアリング対応"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from agents import Agent, ModelSettings, Runner
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.prompts import (
    EXTRACTION_HUMAN,
    EXTRACTION_SYSTEM,
    SUMMARY_HUMAN,
    get_summary_system,
)
from src.analysis.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    CompanyProfile,
    Financials,
    NewsItem,
    RawSource,
    RiskItem,
    ScoreData,
    ScoreItem,
    SourceInfo,
    StructuredData,
    SummaryData,
    SwotAnalysis,
)
from src.collector.service import collect_company_info
from src.db.models import AnalysisResult as AnalysisResultModel
from src.db.models import AnalysisResultSource, AnalysisRun
from src.db.repository import (
    AnalysisResultRepository,
    AnalysisRunRepository,
    CompanyRepository,
    PageRepository,
)
from src.shared.config import get_settings
from src.shared.exceptions import AnalysisError, CollectionError, ExternalServiceError
from src.shared.logger import logger
from src.shared.text import generate_diff_report, generate_markdown_report


async def analyze_company(request: AnalysisRequest, session: AsyncSession) -> AnalysisResponse:
    """企業分析メインフロー（永続化・キャッシュ対応）"""
    logger.info("分析開始: {} (force_refresh={}, template={})", request.company_url, request.force_refresh, request.template)
    settings = get_settings()

    company_repo = CompanyRepository(session)
    result_repo = AnalysisResultRepository(session)
    run_repo = AnalysisRunRepository(session)
    page_repo = PageRepository(session)

    # --- キャッシュチェック ---
    existing_company = await company_repo.find_by_url(request.company_url)
    if existing_company and not request.force_refresh:
        cached = await result_repo.find_latest_by_company(existing_company.company_id)
        if cached:
            logger.info("キャッシュヒット: {}", request.company_url)
            return _model_to_response(cached, is_cached=True)

    company = existing_company or await company_repo.upsert(request.company_url)

    # --- run 作成 ---
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

    # --- 情報収集 ---
    try:
        company_info = await collect_company_info(request.company_url)
    except CollectionError as exc:
        await run_repo.update_status(
            run,
            "failed",
            error_code="COLLECTION_ERROR",
            error_message=str(exc),
        )
        await session.commit()
        raise

    logger.info("情報収集完了: {} 件のソース", len(company_info.sources))
    start_ms = time.monotonic()

    # --- LLM 処理 ---
    try:
        structured = await _extract_structured(request.company_url, company_info.raw_content)
        summary, scores = await _generate_summary_and_scores(
            request.company_url, structured, request.template
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

    elapsed_ms = int((time.monotonic() - start_ms) * 1000)

    sources = [SourceInfo(url=s.url, title=s.title, category=s.category) for s in company_info.sources]
    raw_sources = [RawSource(url=s.url, title=s.title, content=s.content, category=s.category) for s in company_info.sources]

    structured_dict = structured.model_dump()
    summary_dict = summary.model_dump()
    sources_dict = [s.model_dump() for s in sources]
    markdown_page = generate_markdown_report(
        company_url=request.company_url,
        structured=structured_dict,
        summary=summary_dict,
        sources=sources_dict,
    )

    # 差分レポート（refresh時）
    diff_report = ""
    if run_type == "refresh" and existing_company:
        prev = await result_repo.find_latest_by_company(company.company_id)
        if prev:
            diff_report = generate_diff_report(structured_dict, prev.structured)

    if structured.company_profile.name:
        company.display_name = structured.company_profile.name

    # カテゴリ別ページ数とページ資産の保存
    source_categories: dict[str, int] = {}
    page_versions = []
    for s in company_info.sources:
        source_categories[s.category] = source_categories.get(s.category, 0) + 1
        page = await page_repo.get_or_create_page(
            company.company_id,
            s.url,
            page_type=s.category,
            title=s.title,
        )
        version = await page_repo.add_version(
            page,
            extracted_text=s.content,
            fetched_at=datetime.now(timezone.utc),
            fetch_run_id=run.run_id,
            title=s.title,
            metadata=s.meta,
        )
        page_versions.append((s, version))
    company.last_page_crawl_at = datetime.now(timezone.utc)

    result_model = AnalysisResultModel(
        company_id=company.company_id,
        run_id=run.run_id,
        template=request.template,
        llm_model=settings.azure_deployment,
        llm_api_version=settings.api_version,
        structured=structured_dict,
        summary=summary_dict,
        scores=scores.model_dump() if scores else None,
        diff_report=diff_report or None,
        sources=sources_dict,
        raw_sources=[s.model_dump() for s in raw_sources],
        pages_used=len(sources),
        markdown_page=markdown_page,
        quality_metrics={
            "processing_ms": elapsed_ms,
            "source_categories": source_categories,
        },
    )
    result_model = await result_repo.save(result_model)

    for index, (source, version) in enumerate(page_versions):
        session.add(
            AnalysisResultSource(
                result_id=result_model.result_id,
                page_version_id=version.page_version_id,
                source_order=index,
                page_category=source.category,
                citation_title=source.title,
                snippet=source.content[:500],
                citation_metadata=source.meta,
            )
        )

    await run_repo.update_status(
        run,
        "completed",
        collection_summary={
            "pages_fetched": len(sources),
            "source_categories": source_categories,
        },
    )

    await session.commit()

    logger.info("分析完了: {} ({}ms)", request.company_url, elapsed_ms)
    return AnalysisResponse(
        company_url=request.company_url,
        result_id=result_model.result_id,
        company_id=company.company_id,
        is_cached=False,
        analyzed_at=result_model.created_at,
        structured=structured,
        summary=summary,
        scores=scores,
        sources=sources,
        raw_sources=raw_sources,
        markdown_page=markdown_page,
        diff_report=diff_report,
        template=request.template,
    )


def _model_to_response(model: AnalysisResultModel, is_cached: bool = False) -> AnalysisResponse:
    """DB モデル → AnalysisResponse 変換"""
    structured = StructuredData.model_validate(model.structured)
    summary = SummaryData.model_validate(model.summary)
    scores = ScoreData.model_validate(model.scores) if model.scores else None
    sources = [SourceInfo.model_validate(s) for s in (model.sources or [])]
    raw_sources = [RawSource.model_validate(s) for s in (model.raw_sources or [])]
    return AnalysisResponse(
        company_url=model.company.primary_url if model.company else "",
        result_id=model.result_id,
        company_id=model.company_id,
        is_cached=is_cached,
        analyzed_at=model.created_at,
        structured=structured,
        summary=summary,
        scores=scores,
        sources=sources,
        raw_sources=raw_sources,
        markdown_page=model.markdown_page or "",
        diff_report=model.diff_report or "",
        template=model.template,
    )


async def _extract_structured(company_url: str, raw_content: str) -> StructuredData:
    settings = get_settings()
    agent = Agent(
        name="extraction_agent",
        instructions=EXTRACTION_SYSTEM,
        model=settings.azure_deployment,
        model_settings=ModelSettings(temperature=0),
    )
    user_message = EXTRACTION_HUMAN.format(company_url=company_url, classified_content=raw_content)
    try:
        result = await Runner.run(agent, user_message)
        result_text = result.final_output
    except Exception as e:
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise ExternalServiceError(f"Azure OpenAI に接続できません: {e}") from e
        raise AnalysisError(f"構造化抽出に失敗しました: {e}") from e
    return _parse_structured(result_text)


async def _generate_summary_and_scores(
    company_url: str, structured: StructuredData, template: str = "general"
) -> tuple[SummaryData, ScoreData | None]:
    settings = get_settings()
    agent = Agent(
        name="summary_agent",
        instructions=get_summary_system(template),
        model=settings.azure_deployment,
        model_settings=ModelSettings(temperature=0),
    )
    user_message = SUMMARY_HUMAN.format(
        company_url=company_url,
        structured_json=structured.model_dump_json(indent=2),
    )
    try:
        result = await Runner.run(agent, user_message)
        result_text = result.final_output
    except Exception as e:
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise ExternalServiceError(f"Azure OpenAI に接続できません: {e}") from e
        raise AnalysisError(f"要約生成に失敗しました: {e}") from e
    return _parse_summary_and_scores(result_text)


def _parse_structured(text: str) -> StructuredData:
    try:
        parsed = json.loads(_clean_json(text))
    except json.JSONDecodeError:
        logger.error("構造化抽出 JSONパース失敗: {}", text[:300])
        raise AnalysisError("構造化抽出のJSON解析に失敗しました")

    profile_data = parsed.get("company_profile", {})
    financials_data = parsed.get("financials", {})
    return StructuredData(
        company_profile=CompanyProfile(
            **{k: profile_data.get(k, "") for k in ("name", "founded", "ceo", "location", "employees", "capital")}
        ),
        business_domains=parsed.get("business_domains", []),
        products=parsed.get("products", []),
        financials=Financials(
            **{k: financials_data.get(k, "") for k in ("revenue", "operating_income", "net_income", "growth_rate")}
        ),
        news=[
            NewsItem(title=n.get("title", ""), date=n.get("date", ""), summary=n.get("summary", ""))
            for n in parsed.get("news", [])
            if isinstance(n, dict) and n.get("title")
        ],
        risks=[
            RiskItem(category=r.get("category", ""), description=r.get("description", ""))
            for r in parsed.get("risks", [])
            if isinstance(r, dict) and r.get("description")
        ],
    )


def _parse_summary_and_scores(text: str) -> tuple[SummaryData, ScoreData | None]:
    try:
        parsed = json.loads(_clean_json(text))
    except json.JSONDecodeError:
        logger.error("要約生成 JSONパース失敗: {}", text[:300])
        raise AnalysisError("要約生成のJSON解析に失敗しました")

    swot_data = parsed.get("swot", {})
    summary = SummaryData(
        overview=parsed.get("overview", ""),
        business_model=parsed.get("business_model", ""),
        swot=SwotAnalysis(
            strengths=swot_data.get("strengths", []),
            weaknesses=swot_data.get("weaknesses", []),
            opportunities=swot_data.get("opportunities", []),
            threats=swot_data.get("threats", []),
        ),
        risks=parsed.get("risks", []),
        competitors=parsed.get("competitors", []),
        outlook=parsed.get("outlook", ""),
    )

    scores = None
    if "scores" in parsed:
        s = parsed["scores"]
        scores = ScoreData(
            financial_health=ScoreItem(**s.get("financial_health", {})),
            growth_potential=ScoreItem(**s.get("growth_potential", {})),
            competitive_edge=ScoreItem(**s.get("competitive_edge", {})),
            risk_level=ScoreItem(**s.get("risk_level", {})),
            info_transparency=ScoreItem(**s.get("info_transparency", {})),
        )

    return summary, scores


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        start = 1
        end = len(lines)
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end = i
                break
        text = "\n".join(lines[start:end])
    return text.strip()
