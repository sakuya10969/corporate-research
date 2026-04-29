"""複数企業比較セッションモデル"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base

if TYPE_CHECKING:
    from src.db.models.user import User


class ComparisonSession(Base):
    """比較セッション本体。対象企業は中間テーブルに分離する。"""

    __tablename__ = "comparison_sessions"

    comparison_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    template: Mapped[str] = mapped_column(Text, nullable=False, default="general")
    comparison_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    llm_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    share_id: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    shared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    created_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="comparison_sessions"
    )
    items: Mapped[list["ComparisonSessionItem"]] = relationship(
        "ComparisonSessionItem", back_populates="session", cascade="all, delete-orphan"
    )


class ComparisonSessionItem(Base):
    """比較対象企業。順序と採用した分析結果を保持する。"""

    __tablename__ = "comparison_session_items"

    comparison_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    comparison_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comparison_sessions.comparison_id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
    )
    result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_results.result_id", ondelete="SET NULL"),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    session: Mapped["ComparisonSession"] = relationship(
        "ComparisonSession", back_populates="items"
    )
