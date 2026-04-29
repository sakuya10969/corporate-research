"""分析実行履歴モデル"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base

if TYPE_CHECKING:
    from src.db.models.analysis_result import AnalysisResult
    from src.db.models.company import Company
    from src.db.models.page_snapshot import PageVersion
    from src.db.models.user import User


class AnalysisRun(Base):
    """分析の実行単位。入力条件と実行状態を保持する。"""

    __tablename__ = "analysis_runs"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.company_id", ondelete="CASCADE"),
        nullable=False,
    )
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    run_type: Mapped[str] = mapped_column(Text, nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False, default="general")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")

    force_refresh: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    input_params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    collection_summary: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.run_id", ondelete="SET NULL"),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    company: Mapped["Company"] = relationship("Company", back_populates="analysis_runs")
    requested_by_user: Mapped["User | None"] = relationship(
        "User", back_populates="analysis_runs"
    )
    result: Mapped["AnalysisResult | None"] = relationship(
        "AnalysisResult", back_populates="run", uselist=False
    )
    page_versions: Mapped[list["PageVersion"]] = relationship(
        "PageVersion", back_populates="fetch_run"
    )
