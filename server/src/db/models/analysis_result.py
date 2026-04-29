"""分析結果モデル"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base

if TYPE_CHECKING:
    from src.db.models.company import Company


class AnalysisResult(Base):
    """分析結果"""

    __tablename__ = "analysis_results"

    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # 分析コンテキスト
    template: Mapped[str] = mapped_column(Text, nullable=False, default="general")
    llm_model: Mapped[str] = mapped_column(Text, nullable=False)
    llm_api_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 分析結果本体（JSONB）
    structured: Mapped[dict] = mapped_column(JSONB, nullable=False)
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    diff_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ソース情報
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    raw_sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    pages_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_categories: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # レポート
    markdown_page: Mapped[str | None] = mapped_column(Text, nullable=True)

    # シェア（F-012）
    share_id: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    shared_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 品質メタデータ
    extraction_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
    company: Mapped["Company"] = relationship("Company", back_populates="analysis_results")
