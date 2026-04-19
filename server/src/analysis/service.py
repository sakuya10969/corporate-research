"""分析サービス — 2段階パイプライン（構造化抽出 → 要約生成）+ Markdown・差分"""

from __future__ import annotations

import json

from langchain_core.output_parsers import StrOutputParser

from src.analysis.prompts import EXTRACTION_PROMPT, SUMMARY_PROMPT
from src.analysis.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    CompanyProfile,
    Financials,
    NewsItem,
    RawSource,
    RiskItem,
    SourceInfo,
    StructuredData,
    SummaryData,
    SwotAnalysis,
)
from src.collector.service import collect_company_info
from src.shared.exceptions import AnalysisError, CollectionError, ExternalServiceError
from src.shared.llm import get_llm
from src.shared.logger import logger
from src.shared.text import generate_diff_report, generate_markdown_report


async def analyze_company(request: AnalysisRequest) -> AnalysisResponse:
    """企業分析のメインフロー。

    1. collector で情報収集（サイトマップ探索・ページ分類付き、Google検索なし）
    2. Stage 1: LLM で構造化抽出
    3. Stage 2: LLM で要約・SWOT・展望生成
    4. Markdown レポート生成
    5. 差分検知（過去データがあれば）
    6. レスポンス構築
    """
    logger.info("分析開始: {}", request.company_url)

    # --- 情報収集 ---
    try:
        company_info = await collect_company_info(request.company_url)
    except CollectionError:
        raise

    logger.info(
        "情報収集完了: {} 件のソース (raw_content: {}文字)",
        len(company_info.sources),
        len(company_info.raw_content),
    )

    llm = get_llm()

    # --- Stage 1: 構造化抽出 ---
    structured = await _extract_structured(
        llm,
        request.company_url,
        company_info.raw_content,
    )
    logger.info("構造化抽出完了: {}", request.company_url)

    # --- Stage 2: 要約生成 ---
    summary = await _generate_summary(
        llm,
        request.company_url,
        structured,
    )
    logger.info("要約生成完了: {}", request.company_url)

    # --- レスポンス構築 ---
    sources = [
        SourceInfo(url=s.url, title=s.title, category=s.category)
        for s in company_info.sources
    ]

    raw_sources = [
        RawSource(url=s.url, title=s.title, content=s.content, category=s.category)
        for s in company_info.sources
    ]

    # --- Markdown レポート生成 ---
    structured_dict = structured.model_dump()
    summary_dict = summary.model_dump()
    sources_dict = [s.model_dump() for s in sources]
    markdown_page = generate_markdown_report(
        company_url=request.company_url,
        structured=structured_dict,
        summary=summary_dict,
        sources=sources_dict,
    )

    # --- 差分検知（MVP: 過去データなし → 空文字列） ---
    diff_report = generate_diff_report(structured_dict, None)

    logger.info("分析完了: {}", request.company_url)
    return AnalysisResponse(
        company_url=request.company_url,
        structured=structured,
        summary=summary,
        sources=sources,
        raw_sources=raw_sources,
        markdown_page=markdown_page,
        diff_report=diff_report,
    )


async def _extract_structured(
    llm, company_url: str, raw_content: str
) -> StructuredData:
    """Stage 1: 収集データから構造化情報を抽出する。"""
    try:
        chain = EXTRACTION_PROMPT | llm | StrOutputParser()
        result_text = await chain.ainvoke(
            {
                "company_url": company_url,
                "classified_content": raw_content,
            }
        )
        logger.debug("構造化抽出 LLM応答 ({}文字)", len(result_text))
    except Exception as e:
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise ExternalServiceError(f"Azure AI Foundry に接続できません: {e}") from e
        raise AnalysisError(f"構造化抽出に失敗しました: {e}") from e

    return _parse_structured(result_text)


def _parse_structured(text: str) -> StructuredData:
    """LLM出力JSONをStructuredDataにパースする。"""
    try:
        parsed = json.loads(_clean_json(text))
    except json.JSONDecodeError:
        logger.error("構造化抽出 JSONパース失敗: {}", text[:300])
        raise AnalysisError("構造化抽出のJSON解析に失敗しました")

    profile_data = parsed.get("company_profile", {})
    financials_data = parsed.get("financials", {})
    news_data = parsed.get("news", [])
    risks_data = parsed.get("risks", [])

    return StructuredData(
        company_profile=CompanyProfile(
            **{
                k: profile_data.get(k, "")
                for k in ("name", "founded", "ceo", "location", "employees", "capital")
            }
        ),
        business_domains=parsed.get("business_domains", []),
        products=parsed.get("products", []),
        financials=Financials(
            **{
                k: financials_data.get(k, "")
                for k in ("revenue", "operating_income", "net_income", "growth_rate")
            }
        ),
        news=[
            NewsItem(
                title=n.get("title", ""),
                date=n.get("date", ""),
                summary=n.get("summary", ""),
            )
            for n in news_data
            if isinstance(n, dict) and n.get("title")
        ],
        risks=[
            RiskItem(
                category=r.get("category", ""),
                description=r.get("description", ""),
            )
            for r in risks_data
            if isinstance(r, dict) and r.get("description")
        ],
    )


async def _generate_summary(
    llm, company_url: str, structured: StructuredData
) -> SummaryData:
    """Stage 2: 構造化データから要約・SWOT・展望を生成する。"""
    structured_json = structured.model_dump_json(indent=2)

    try:
        chain = SUMMARY_PROMPT | llm | StrOutputParser()
        result_text = await chain.ainvoke(
            {
                "company_url": company_url,
                "structured_json": structured_json,
            }
        )
        logger.debug("要約生成 LLM応答 ({}文字)", len(result_text))
    except Exception as e:
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise ExternalServiceError(f"Azure AI Foundry に接続できません: {e}") from e
        raise AnalysisError(f"要約生成に失敗しました: {e}") from e

    return _parse_summary(result_text)


def _parse_summary(text: str) -> SummaryData:
    """LLM出力JSONをSummaryDataにパースする。"""
    try:
        parsed = json.loads(_clean_json(text))
    except json.JSONDecodeError:
        logger.error("要約生成 JSONパース失敗: {}", text[:300])
        raise AnalysisError("要約生成のJSON解析に失敗しました")

    swot_data = parsed.get("swot", {})

    return SummaryData(
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


def _clean_json(text: str) -> str:
    """LLM出力からJSON部分を抽出する（```json ... ``` 対応）。"""
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
