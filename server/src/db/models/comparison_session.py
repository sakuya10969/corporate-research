"""複数企業比較セッションモデル F-013"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class ComparisonSession(Base):
    """複数企業比較セッション F-013"""

    __tablename__ = "comparison_sessions"

    comparison_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_ids = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False)
    result_ids = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False)

    comparison_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    template: Mapped[str] = mapped_column(Text, nullable=False, default="general")
    share_id: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    shared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    llm_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
