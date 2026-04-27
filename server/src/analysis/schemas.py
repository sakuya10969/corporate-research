"""分析モジュール — Pydantic スキーマ定義"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# リクエスト
# ---------------------------------------------------------------------------


class AnalysisRequest(BaseModel):
    company_url: str = Field(
        ...,
        min_length=1,
        pattern=r"^https?://.*",
        description="分析対象の企業URL（例: https://www.toyota.co.jp/）",
    )
    force_refresh: bool = Field(False, description="キャッシュを無視して再分析する")
    template: Literal["general", "job_hunting", "investment", "competitor", "partnership"] = Field(
        "general", description="分析テンプレート"
    )


# ---------------------------------------------------------------------------
# 構造化抽出結果
# ---------------------------------------------------------------------------


class CompanyProfile(BaseModel):
    name: str = ""
    founded: str = ""
    ceo: str = ""
    location: str = ""
    employees: str = ""
    capital: str = ""


class Financials(BaseModel):
    revenue: str = ""
    operating_income: str = ""
    net_income: str = ""
    growth_rate: str = ""


class NewsItem(BaseModel):
    title: str
    date: str = ""
    summary: str = ""


class RiskItem(BaseModel):
    category: str = ""
    description: str


class SourceInfo(BaseModel):
    url: str
    title: str
    category: str = "その他"


class RawSource(BaseModel):
    url: str
    title: str
    content: str
    category: str = "その他"


class StructuredData(BaseModel):
    company_profile: CompanyProfile = Field(default_factory=CompanyProfile)
    business_domains: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    financials: Financials = Field(default_factory=Financials)
    news: list[NewsItem] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 要約結果
# ---------------------------------------------------------------------------


class SwotAnalysis(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)


class SummaryData(BaseModel):
    overview: str = ""
    business_model: str = ""
    swot: SwotAnalysis = Field(default_factory=SwotAnalysis)
    risks: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    outlook: str = ""


# ---------------------------------------------------------------------------
# スコアリング（F-014）
# ---------------------------------------------------------------------------


class ScoreItem(BaseModel):
    score: int = Field(0, ge=0, le=100)
    reason: str = ""


class ScoreData(BaseModel):
    financial_health: ScoreItem = Field(default_factory=ScoreItem)
    growth_potential: ScoreItem = Field(default_factory=ScoreItem)
    competitive_edge: ScoreItem = Field(default_factory=ScoreItem)
    risk_level: ScoreItem = Field(default_factory=ScoreItem)
    info_transparency: ScoreItem = Field(default_factory=ScoreItem)


# ---------------------------------------------------------------------------
# APIレスポンス
# ---------------------------------------------------------------------------


class AnalysisResponse(BaseModel):
    company_url: str
    result_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    is_cached: bool = False
    analyzed_at: datetime | None = None
    structured: StructuredData
    summary: SummaryData
    scores: ScoreData | None = None
    sources: list[SourceInfo]
    raw_sources: list[RawSource] = Field(default_factory=list)
    markdown_page: str = ""
    diff_report: str = ""
    template: str = "general"


# ---------------------------------------------------------------------------
# 履歴レスポンス（F-008）
# ---------------------------------------------------------------------------


class RunSummary(BaseModel):
    run_id: uuid.UUID
    run_type: str
    status: str
    template: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    error_message: str | None
    result_id: uuid.UUID | None


class HistoryResponse(BaseModel):
    company_id: uuid.UUID
    runs: list[RunSummary]


# ---------------------------------------------------------------------------
# 比較リクエスト/レスポンス（F-013）
# ---------------------------------------------------------------------------


class CompareRequest(BaseModel):
    urls: list[str] = Field(..., min_length=2, max_length=3)
    template: Literal["general", "job_hunting", "investment", "competitor", "partnership"] = "general"


class CompareResponse(BaseModel):
    results: list[AnalysisResponse]
    comparison_summary: str = ""


# ---------------------------------------------------------------------------
# 検索レスポンス（F-011）
# ---------------------------------------------------------------------------


class SearchResult(BaseModel):
    name: str
    url: str


class SearchResponse(BaseModel):
    results: list[SearchResult]


# ---------------------------------------------------------------------------
# ヘルスチェック
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"
