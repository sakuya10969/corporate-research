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

    from sqlalchemy import UniqueConstraint
    __table_args__ = (UniqueConstraint("company_id", "normalized_url", name="uq_page_snapshots_company_url"),)


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


class ComparisonSession(Base):
    """複数企業比較セッション F-013"""

    __tablename__ = "comparison_sessions"

    from sqlalchemy.dialects.postgresql import ARRAY
    from sqlalchemy import Column

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


class User(Base):
    """認証ユーザー（Clerk連携）"""

    __tablename__ = "users"

    clerk_user_id: Mapped[str] = mapped_column(Text, primary_key=True)
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
