"""分析モジュール — Pydantic スキーマ定義"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# リクエスト
# ---------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    company_name: str = Field(..., min_length=1, pattern=r".*\S.*")


# ---------------------------------------------------------------------------
# 構造化抽出結果（LLM出力 → パース先）
# ---------------------------------------------------------------------------

class CompanyProfile(BaseModel):
    """企業プロフィール"""
    name: str = ""
    founded: str = ""
    ceo: str = ""
    location: str = ""
    employees: str = ""
    capital: str = ""


class Financials(BaseModel):
    """財務情報"""
    revenue: str = ""
    operating_income: str = ""
    net_income: str = ""
    growth_rate: str = ""


class NewsItem(BaseModel):
    """ニュース項目"""
    title: str
    date: str = ""
    summary: str = ""


class RiskItem(BaseModel):
    """リスク要因"""
    category: str = ""
    description: str


class SourceInfo(BaseModel):
    """参照ソース"""
    url: str
    title: str
    category: str = "その他"


class RawSource(BaseModel):
    """生テキストソース"""
    url: str
    title: str
    content: str


class StructuredData(BaseModel):
    """構造化抽出結果"""
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
    """SWOT分析"""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)


class SummaryData(BaseModel):
    """要約・分析結果"""
    overview: str = ""
    business_model: str = ""
    swot: SwotAnalysis = Field(default_factory=SwotAnalysis)
    risks: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    outlook: str = ""


# ---------------------------------------------------------------------------
# APIレスポンス
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    """分析結果レスポンス（API返却用）"""
    company_name: str
    structured: StructuredData
    summary: SummaryData
    sources: list[SourceInfo]
    raw_sources: list[RawSource] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# ヘルスチェック
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
