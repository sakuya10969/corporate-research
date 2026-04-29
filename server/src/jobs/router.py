"""ジョブ状態エンドポイント

GET /api/analysis-runs/{run_id} — ジョブ状態取得
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.companies.schemas import RunStatusResponse
from src.jobs.manager import JobManager
from src.shared.db import get_session

router = APIRouter(prefix="/api/analysis-runs", tags=["jobs"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------


def _run_to_status_response(run) -> RunStatusResponse:
    """AnalysisRun ORM モデル → RunStatusResponse 変換"""
    return RunStatusResponse(
        run_id=run.run_id,
        company_id=run.company_id,
        status=run.status,
        run_type=run.run_type,
        template=run.template,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
        result_id=run.result.result_id if run.result else None,
    )


# ---------------------------------------------------------------------------
# GET /api/analysis-runs/{run_id} — ジョブ状態取得 (Req 10.8)
# ---------------------------------------------------------------------------


@router.get("/{run_id}", response_model=RunStatusResponse)
async def get_run_status(
    run_id: uuid.UUID,
    session: SessionDep,
) -> RunStatusResponse:
    """指定された分析ジョブの状態を返却する。"""
    job_manager = JobManager(session)
    run = await job_manager.get_run_status(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail="分析ジョブが見つかりません")

    return _run_to_status_response(run)
