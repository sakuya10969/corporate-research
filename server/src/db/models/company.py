"""企業マスタモデル"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base

if TYPE_CHECKING:
    from src.db.models.analysis_result import AnalysisResult
    from src.db.models.analysis_run import AnalysisRun


class Company(Base):
    """企業マスタ"""

    __tablename__ = "companies"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 識別情報
    url: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    domain: Mapped[str] = mapped_column(Text, nullable=False)

    # 企業基本情報（LLM抽出）
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String(10), nullable=False, default="JP")

    # 収集メタデータ
    first_crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_crawled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    crawl_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_pages_crawled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ステータス
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # リレーション
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="company", cascade="all, delete-orphan"
    )
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="company", cascade="all, delete-orphan"
    )
