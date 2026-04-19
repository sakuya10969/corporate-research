import json

from langchain_core.output_parsers import StrOutputParser

from src.analysis.prompts import ANALYSIS_PROMPT
from src.analysis.schemas import AnalysisRequest, AnalysisResponse, SourceInfo
from src.collector.service import collect_company_info
from src.shared.exceptions import AnalysisError, CollectionError, ExternalServiceError
from src.shared.llm import get_llm
from src.shared.logger import logger


async def analyze_company(request: AnalysisRequest) -> AnalysisResponse:
    logger.info("分析開始: {}", request.company_name)

    try:
        company_info = await collect_company_info(request.company_name)
    except CollectionError:
        raise

    logger.info("情報収集完了: {} 件のソース", len(company_info.sources))

    try:
        llm = get_llm()
        chain = ANALYSIS_PROMPT | llm | StrOutputParser()
        logger.debug("LLM チェーン実行開始")
        result_text = await chain.ainvoke({
            "company_name": request.company_name,
            "raw_content": company_info.raw_content,
        })
        logger.debug("LLM チェーン実行完了 ({}文字)", len(result_text))
    except Exception as e:
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise ExternalServiceError(f"Azure AI Foundry に接続できません: {e}") from e
        raise AnalysisError(f"AI分析処理に失敗しました: {e}") from e

    try:
        parsed = json.loads(result_text)
    except json.JSONDecodeError:
        logger.error("JSON パース失敗: {}", result_text[:200])
        raise AnalysisError("AI応答のJSON解析に失敗しました")

    sources = [
        SourceInfo(url=s.url, title=s.title)
        for s in company_info.sources
    ]

    logger.info("分析完了: {}", request.company_name)
    return AnalysisResponse(
        company_name=request.company_name,
        summary=parsed.get("summary", ""),
        business_description=parsed.get("business_description", ""),
        key_findings=parsed.get("key_findings", []),
        sources=sources,
    )
