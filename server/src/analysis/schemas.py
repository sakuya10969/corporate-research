from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    company_name: str = Field(..., min_length=1, pattern=r".*\S.*")


class SourceInfo(BaseModel):
    url: str
    title: str


class AnalysisResponse(BaseModel):
    company_name: str
    summary: str
    business_description: str
    key_findings: list[str]
    sources: list[SourceInfo]


class HealthResponse(BaseModel):
    status: str = "ok"
