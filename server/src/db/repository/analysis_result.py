"""AnalysisResultRepository — 分析結果の CRUD"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import AnalysisResult


class AnalysisResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, result: AnalysisResult) -> AnalysisResult:
        self._s.add(result)
        await self._s.flush()
        return result

    async def find_latest_by_company(self, company_id: uuid.UUID) -> AnalysisResult | None:
        res = await self._s.execute(
            select(AnalysisResult)
            .options(selectinload(AnalysisResult.company))
            .where(AnalysisResult.company_id == company_id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def find_by_id(self, result_id: uuid.UUID) -> AnalysisResult | None:
        res = await self._s.execute(
            select(AnalysisResult)
            .options(selectinload(AnalysisResult.company))
            .where(AnalysisResult.result_id == result_id)
        )
        return res.scalar_one_or_none()

    async def find_by_share_id(self, share_id: str) -> AnalysisResult | None:
        res = await self._s.execute(
            select(AnalysisResult)
            .options(selectinload(AnalysisResult.company))
            .where(AnalysisResult.share_id == share_id)
        )
        return res.scalar_one_or_none()

    async def list_by_company(
        self, company_id: uuid.UUID, limit: int = 20
    ) -> list[AnalysisResult]:
        res = await self._s.execute(
            select(AnalysisResult)
            .where(AnalysisResult.company_id == company_id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())
