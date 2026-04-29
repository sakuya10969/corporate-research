"""ページ取得スナップショットモデル（差分検知用）F-006"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base


class PageSnapshot(Base):
    """ページ取得スナップショット（差分検知用）F-006"""

    __tablename__ = "page_snapshots"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)

    url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)

    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    etag: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_modified: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_length: Mapped[int | None] = mapped_column(Integer, nullable=True)

    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    og_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    og_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    lang: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(Text, nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetch_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_changed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    previous_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("company_id", "normalized_url", name="uq_page_snapshots_company_url"),)
