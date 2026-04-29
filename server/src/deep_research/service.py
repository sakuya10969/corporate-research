"""深掘り分析サービス（F-007）— openai-agents ベース"""

from __future__ import annotations

import uuid
from agents import Agent, ModelSettings, Runner
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.prompts import DEEP_RESEARCH_SYSTEM
from src.analysis.schemas import StructuredData, SummaryData
from src.db.models import DeepResearchMessage, DeepResearchSession
from src.db.repository import AnalysisResultRepository, DeepResearchRepository
from src.shared.config import get_settings
from src.shared.exceptions import AnalysisError
from src.shared.logger import logger


async def ask_deep_research(
    company_id: uuid.UUID,
    result_id: uuid.UUID | None,
    question: str,
    session_id: uuid.UUID | None,
    db: AsyncSession,
) -> dict:
    """深掘り質問に回答し、セッション・メッセージを DB に保存する"""
    settings = get_settings()
    result_repo = AnalysisResultRepository(db)
    deep_research_repo = DeepResearchRepository(db)

    # 分析結果を取得
    if result_id:
        result = await result_repo.find_by_id(result_id)
    else:
        result = await result_repo.find_latest_by_company(company_id)

    if not result:
        raise AnalysisError("分析結果が見つかりません。先に企業分析を実行してください。")

    structured = StructuredData.model_validate(result.structured)
    summary = SummaryData.model_validate(result.summary)

    context = (
        f"企業分析データ:\n"
        f"構造化データ: {structured.model_dump_json(indent=2)}\n\n"
        f"要約データ: {summary.model_dump_json(indent=2)}"
    )

    # セッション取得 or 作成
    if session_id:
        dr_session = await deep_research_repo.find_session(session_id)
    else:
        dr_session = None

    if not dr_session:
        dr_session = DeepResearchSession(
            company_id=company_id,
            base_result_id=result_id or result.result_id,
            status="active",
        )
        await deep_research_repo.save_session(dr_session)

    # メッセージ数取得
    from sqlalchemy import func, select
    count_res = await db.execute(
        select(func.count()).where(DeepResearchMessage.session_id == dr_session.session_id)
    )
    msg_count = count_res.scalar() or 0

    # ユーザーメッセージ保存
    user_msg = DeepResearchMessage(
        session_id=dr_session.session_id,
        role="user",
        content=question,
        sequence=msg_count,
    )
    db.add(user_msg)
    await db.flush()

    # LLM 呼び出し
    agent = Agent(
        name="deep_research_agent",
        instructions=DEEP_RESEARCH_SYSTEM + f"\n\n{context}",
        model=settings.azure_deployment,
        model_settings=ModelSettings(temperature=0.3),
    )
    try:
        result_obj = await Runner.run(agent, question)
        answer = result_obj.final_output
    except Exception as e:
        raise AnalysisError(f"深掘り分析に失敗しました: {e}") from e

    # アシスタントメッセージ保存
    assistant_msg = DeepResearchMessage(
        session_id=dr_session.session_id,
        role="assistant",
        content=answer,
        model_name=settings.azure_deployment,
        retrieval_context={"used_cached_analysis_result": True},
        sequence=msg_count + 1,
    )
    db.add(assistant_msg)
    dr_session.message_count = msg_count + 2
    await db.commit()

    logger.info("深掘り分析完了: session={}", dr_session.session_id)
    return {
        "session_id": str(dr_session.session_id),
        "answer": answer,
    }
