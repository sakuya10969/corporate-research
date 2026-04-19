from fastapi import APIRouter

from src.analysis.schemas import AnalysisRequest, AnalysisResponse, HealthResponse
from src.analysis.service import analyze_company

router = APIRouter()


@router.post("/analysis", response_model=AnalysisResponse)
async def post_analysis(request: AnalysisRequest) -> AnalysisResponse:
    return await analyze_company(request)


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return HealthResponse()
