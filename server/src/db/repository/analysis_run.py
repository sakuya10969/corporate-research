"""AnalysisRunRepository — 分析実行履歴の CRUD"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AnalysisRun


class AnalysisRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, run: AnalysisRun) -> AnalysisRun:
        self._s.add(run)
        await self._s.flush()
        return run

    async def update_status(
        self,
        run: AnalysisRun,
        status: str,
        result_id: uuid.UUID | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> AnalysisRun:
        run.status = status
        if result_id:
            run.result_id = result_id
        if error_code:
            run.error_code = error_code
        if error_message:
            run.error_message = error_message
        if status in ("completed", "failed"):
            run.completed_at = datetime.now(timezone.utc)
            if run.started_at:
                run.duration_ms = int(
                    (run.completed_at - run.started_at).total_seconds() * 1000
                )
        await self._s.flush()
        return run

    async def list_by_company(self, company_id: uuid.UUID, limit: int = 50) -> list[AnalysisRun]:
        res = await self._s.execute(
            select(AnalysisRun)
            .where(AnalysisRun.company_id == company_id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())
