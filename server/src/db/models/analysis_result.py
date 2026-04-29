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
    from src.db.models.analysis_run import AnalysisRun
    from src.db.models.company import Company
    from src.db.models.page_snapshot import PageVersion


class AnalysisResult(Base):
    """1回の分析から生成される成果物。履歴として積み上げる。"""

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
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.run_id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    template: Mapped[str] = mapped_column(Text, nullable=False, default="general")
    llm_model: Mapped[str] = mapped_column(Text, nullable=False)
    llm_api_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(Text, nullable=True)

    structured: Mapped[dict] = mapped_column(JSONB, nullable=False)
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    diff_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 現行 API 互換用に残す。正規な根拠参照は analysis_result_sources を使う。
    sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    raw_sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    markdown_page: Mapped[str | None] = mapped_column(Text, nullable=True)

    pages_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    share_id: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    shared_at: Mapped[datetime | None] = mapped_column(
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

    company: Mapped["Company"] = relationship("Company", back_populates="analysis_results")
    run: Mapped["AnalysisRun | None"] = relationship("AnalysisRun", back_populates="result")
    source_links: Mapped[list["AnalysisResultSource"]] = relationship(
        "AnalysisResultSource", back_populates="result", cascade="all, delete-orphan"
    )


class AnalysisResultSource(Base):
    """分析結果と保存済みページ版の関連。"""

    __tablename__ = "analysis_result_sources"

    analysis_result_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_results.result_id", ondelete="CASCADE"),
        nullable=False,
    )
    page_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("page_versions.page_version_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    result: Mapped["AnalysisResult"] = relationship(
        "AnalysisResult", back_populates="source_links"
    )
    page_version: Mapped["PageVersion"] = relationship(
        "PageVersion", back_populates="analysis_result_links"
    )
