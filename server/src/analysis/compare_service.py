"""複数企業比較サービス（F-013）"""

from __future__ import annotations

import asyncio
import json

from agents import Agent, ModelSettings, Runner
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.prompts import COMPARISON_HUMAN, COMPARISON_SYSTEM
from src.analysis.schemas import AnalysisRequest, AnalysisResponse, CompareRequest, CompareResponse
from src.analysis.service import analyze_company
from src.shared.config import get_settings
from src.shared.exceptions import AnalysisError
from src.shared.logger import logger


async def compare_companies(request: CompareRequest, session: AsyncSession) -> CompareResponse:
    """最大3社を並行分析して比較サマリーを生成する"""
    logger.info("比較分析開始: {} 社", len(request.urls))

    # 各社を並行分析
    tasks = [
        analyze_company(
            AnalysisRequest(company_url=url, template=request.template),
            session,
        )
        for url in request.urls
    ]
    results: list[AnalysisResponse] = await asyncio.gather(*tasks)

    # 比較サマリー生成
    companies_data = [
        {
            "url": r.company_url,
            "name": r.structured.company_profile.name,
            "summary": r.summary.model_dump(),
            "structured": r.structured.model_dump(),
        }
        for r in results
    ]

    settings = get_settings()
    agent = Agent(
        name="comparison_agent",
        instructions=COMPARISON_SYSTEM,
        model=settings.azure_deployment,
        model_settings=ModelSettings(temperature=0.3),
    )
    try:
        result = await Runner.run(
            agent,
            COMPARISON_HUMAN.format(companies_json=json.dumps(companies_data, ensure_ascii=False, indent=2)),
        )
        parsed = json.loads(result.final_output.strip().strip("```json").strip("```").strip())
        comparison_summary = parsed.get("comparison_summary", "")
    except Exception as e:
        logger.warning("比較サマリー生成失敗: {}", e)
        comparison_summary = ""

    return CompareResponse(results=results, comparison_summary=comparison_summary)
