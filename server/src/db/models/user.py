"""認証ユーザーモデル"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base

if TYPE_CHECKING:
    from src.db.models.analysis_run import AnalysisRun
    from src.db.models.comparison_session import ComparisonSession
    from src.db.models.deep_research import DeepResearchSession


class User(Base):
    """認証ユーザー。Clerk のIDは一意キーとして保持する。"""

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clerk_user_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="requested_by_user"
    )
    deep_research_sessions: Mapped[list["DeepResearchSession"]] = relationship(
        "DeepResearchSession", back_populates="created_by_user"
    )
    comparison_sessions: Mapped[list["ComparisonSession"]] = relationship(
        "ComparisonSession", back_populates="created_by_user"
    )
