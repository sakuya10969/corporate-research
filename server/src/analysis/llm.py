"""分析モジュール — LLM呼び出しユーティリティ

構造化抽出・要約生成のための LLM Agent 呼び出しと JSON パース処理を提供する。
ExtractionService, AnalysisService, および レガシーの analyze_company() から利用される。
"""

from __future__ import annotations

import json

from agents import Agent, ModelSettings, Runner

from src.analysis.prompts import (
    EXTRACTION_HUMAN,
    EXTRACTION_SYSTEM,
    SUMMARY_HUMAN,
    get_summary_system,
)
from src.analysis.schemas import (
    CompanyProfile,
    Financials,
    NewsItem,
    RiskItem,
    ScoreData,
    ScoreItem,
    StructuredData,
    SummaryData,
    SwotAnalysis,
)
from src.shared.config import get_settings
from src.shared.exceptions import AnalysisError, ExternalServiceError
from src.shared.logger import logger


async def extract_structured(company_url: str, raw_content: str) -> StructuredData:
    """LLM を使用して企業情報を構造化データに抽出する。"""
    settings = get_settings()
    agent = Agent(
        name="extraction_agent",
        instructions=EXTRACTION_SYSTEM,
        model=settings.azure_deployment,
        model_settings=ModelSettings(temperature=0),
    )
    user_message = EXTRACTION_HUMAN.format(
        company_url=company_url, classified_content=raw_content
    )
    try:
        result = await Runner.run(agent, user_message)
        result_text = result.final_output
    except Exception as e:
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise ExternalServiceError(f"Azure OpenAI に接続できません: {e}") from e
        raise AnalysisError(f"構造化抽出に失敗しました: {e}") from e
    return _parse_structured(result_text)


async def generate_summary_and_scores(
    company_url: str, structured: StructuredData, template: str = "general"
) -> tuple[SummaryData, ScoreData | None]:
    """LLM を使用して要約・スコアを生成する。"""
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
            for n in parsed.get("news", [])
            if isinstance(n, dict) and n.get("title")
        ],
        risks=[
            RiskItem(
                category=r.get("category", ""),
                description=r.get("description", ""),
            )
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
