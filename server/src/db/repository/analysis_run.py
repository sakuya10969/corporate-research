"""AnalysisRunRepository — 分析実行履歴の CRUD"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import AnalysisRun


class AnalysisRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, run: AnalysisRun) -> AnalysisRun:
        self._s.add(run)
        await self._s.flush()
        return run

    async def find_by_id(self, run_id: uuid.UUID) -> AnalysisRun | None:
        result = await self._s.execute(
            select(AnalysisRun).where(AnalysisRun.run_id == run_id)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        run: AnalysisRun,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
        collection_summary: dict | None = None,
    ) -> AnalysisRun:
        run.status = status
        if error_code:
            run.error_code = error_code
        if error_message:
            run.error_message = error_message
        if collection_summary is not None:
            run.collection_summary = collection_summary
        if status in ("completed", "failed", "cancelled"):
            run.completed_at = datetime.now(timezone.utc)
            if run.started_at:
                run.duration_ms = int(
                    (run.completed_at - run.started_at).total_seconds() * 1000
                )
        await self._s.flush()
        return run

    async def list_by_company(
        self, company_id: uuid.UUID, limit: int = 50
    ) -> list[AnalysisRun]:
        res = await self._s.execute(
            select(AnalysisRun)
            .options(selectinload(AnalysisRun.result))
            .where(AnalysisRun.company_id == company_id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())
