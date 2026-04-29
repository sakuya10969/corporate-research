"""企業マスタモデル"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base

if TYPE_CHECKING:
    from src.db.models.analysis_result import AnalysisResult
    from src.db.models.analysis_run import AnalysisRun
    from src.db.models.page_snapshot import Page


class Company(Base):
    """企業の正本。分析結果ではなく企業識別を管理する。"""

    __tablename__ = "companies"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 識別情報
    primary_url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    primary_domain: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    # 安定しやすい企業属性のみ保持
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    legal_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    country_code: Mapped[str] = mapped_column(String(10), nullable=False, default="JP")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # 分析・収集の集計
    first_analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    analysis_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_page_crawl_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="company", cascade="all, delete-orphan"
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="company", cascade="all, delete-orphan"
    )
    pages: Mapped[list["Page"]] = relationship(
        "Page", back_populates="company", cascade="all, delete-orphan"
    )
