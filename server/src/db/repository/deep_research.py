"""DeepResearchRepository — 深掘り分析の CRUD"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import DeepResearchSession


class DeepResearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def find_session(self, session_id: uuid.UUID) -> DeepResearchSession | None:
        res = await self._s.execute(
            select(DeepResearchSession)
            .options(selectinload(DeepResearchSession.messages))
            .where(DeepResearchSession.session_id == session_id)
        )
        return res.scalar_one_or_none()

    async def save_session(self, session: DeepResearchSession) -> DeepResearchSession:
        self._s.add(session)
        await self._s.flush()
        return session
