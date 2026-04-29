"""深掘り分析セッション・メッセージモデル F-007"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class DeepResearchSession(Base):
    """深掘り分析セッション F-007"""

    __tablename__ = "deep_research_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    result_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_results.result_id", ondelete="SET NULL"), nullable=True)

    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    message_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    additional_pages_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    messages: Mapped[list["DeepResearchMessage"]] = relationship("DeepResearchMessage", back_populates="session", cascade="all, delete-orphan")


class DeepResearchMessage(Base):
    """深掘り分析メッセージ F-007"""

    __tablename__ = "deep_research_messages"

    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deep_research_sessions.session_id", ondelete="CASCADE"), nullable=False)

    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    used_cached_data: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    additional_urls: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    session: Mapped[DeepResearchSession] = relationship("DeepResearchSession", back_populates="messages")
