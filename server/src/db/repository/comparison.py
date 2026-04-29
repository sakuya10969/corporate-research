"""ComparisonRepository — 比較セッションの CRUD"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import ComparisonSession


class ComparisonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def find_by_id(self, comparison_id: uuid.UUID) -> ComparisonSession | None:
        res = await self._s.execute(
            select(ComparisonSession)
            .options(selectinload(ComparisonSession.items))
            .where(ComparisonSession.comparison_id == comparison_id)
        )
        return res.scalar_one_or_none()

    async def save(self, comparison: ComparisonSession) -> ComparisonSession:
        self._s.add(comparison)
        await self._s.flush()
        return comparison
