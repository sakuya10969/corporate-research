"""企業管理モジュール — Pydantic スキーマ定義"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.analysis.schemas import AnalysisResponse, RunSummary


# ---------------------------------------------------------------------------
# リクエスト
# ---------------------------------------------------------------------------


class RegisterCompanyRequest(BaseModel):
    url: str = Field(
        ...,
        min_length=1,
        pattern=r"^https?://.*",
        description="登録する企業のURL（例: https://www.toyota.co.jp/）",
    )


class StartAnalysisRequest(BaseModel):
    template: str = Field("general", description="分析テンプレート")
    force_refresh: bool = Field(
        False, description="キャッシュを無視して再クロール・再分析する"
    )


# ---------------------------------------------------------------------------
# レスポンス — 企業
# ---------------------------------------------------------------------------


class CompanyResponse(BaseModel):
    company_id: uuid.UUID
    primary_url: str
    normalized_url: str
    display_name: str | None = None
    status: str
    last_page_crawl_at: datetime | None = None
    last_analyzed_at: datetime | None = None
    analysis_count: int
    created_at: datetime


class CompanyListResponse(BaseModel):
    companies: list[CompanyResponse]


class CompanyDetailResponse(CompanyResponse):
    latest_result: AnalysisResponse | None = None
    recent_runs: list[RunSummary] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# レスポンス — ジョブ状態
# ---------------------------------------------------------------------------


class RunStatusResponse(BaseModel):
    run_id: uuid.UUID
    company_id: uuid.UUID
    status: str = Field(
        ..., description="ジョブ状態: pending, running, completed, failed"
    )
    run_type: str
    template: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    result_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# レスポンス — 分析履歴
# ---------------------------------------------------------------------------


class AnalysisHistoryResponse(BaseModel):
    company_id: uuid.UUID
    results: list[AnalysisResponse]

