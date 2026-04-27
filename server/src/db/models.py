"""SQLAlchemy ORM モデル定義"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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
    analysis_results: Mapped[list[AnalysisResult]] = relationship(
        "AnalysisResult", back_populates="company", cascade="all, delete-orphan"
    )
    analysis_runs: Mapped[list[AnalysisRun]] = relationship(
        "AnalysisRun", back_populates="company", cascade="all, delete-orphan"
    )


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
    company: Mapped[Company] = relationship("Company", back_populates="analysis_results")


class AnalysisRun(Base):
    """分析実行履歴"""

    __tablename__ = "analysis_runs"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
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

    # 実行種別
    run_type: Mapped[str] = mapped_column(Text, nullable=False)  # initial / refresh / deep_research
    template: Mapped[str] = mapped_column(Text, nullable=False, default="general")

    # ステータス管理
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.run_id"),
        nullable=True,
    )

    # 実行メタデータ
    triggered_by: Mapped[str] = mapped_column(Text, nullable=False, default="user")
    force_refresh: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    request_ip: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # タイミング
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 収集サマリー
    pages_fetched: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pages_changed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pages_skipped: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
    company: Mapped[Company] = relationship("Company", back_populates="analysis_runs")
