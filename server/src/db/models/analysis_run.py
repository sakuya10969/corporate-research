"""分析実行履歴モデル"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base

if TYPE_CHECKING:
    from src.db.models.company import Company


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
    company: Mapped["Company"] = relationship("Company", back_populates="analysis_runs")
