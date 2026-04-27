from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.compare_service import compare_companies
from src.analysis.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    CompareRequest,
    CompareResponse,
    HealthResponse,
    HistoryResponse,
    RunSummary,
    SearchResponse,
)
from src.analysis.service import analyze_company
from src.db.repository import AnalysisResultRepository, AnalysisRunRepository, CompanyRepository
from src.deep_research.service import ask_deep_research
from src.download.generator import generate_docx, generate_pdf
from src.search.service import search_company_url
from src.shared.db import get_session
from src.shared.exceptions import AnalysisError

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# 分析（F-001/F-002/F-005）
# ---------------------------------------------------------------------------

@router.post("/analysis", response_model=AnalysisResponse, tags=["analysis"])
async def post_analysis(request: AnalysisRequest, session: SessionDep) -> AnalysisResponse:
    return await analyze_company(request, session)


# ---------------------------------------------------------------------------
# 分析結果取得（F-008）
# ---------------------------------------------------------------------------

@router.get("/analysis/{result_id}", response_model=AnalysisResponse, tags=["analysis"])
async def get_analysis_result(result_id: uuid.UUID, session: SessionDep) -> AnalysisResponse:
    repo = AnalysisResultRepository(session)
    result = await repo.find_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="分析結果が見つかりません")
    from src.analysis.service import _model_to_response
    return _model_to_response(result, is_cached=True)


# ---------------------------------------------------------------------------
# ダウンロード（F-009）
# ---------------------------------------------------------------------------

@router.get("/analysis/{result_id}/download", tags=["analysis"])
async def download_analysis(
    result_id: uuid.UUID,
    format: Annotated[Literal["pdf", "docx"], Query()] = "pdf",
    session: SessionDep = None,
) -> Response:
    repo = AnalysisResultRepository(session)
    result = await repo.find_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="分析結果が見つかりません")

    company_name = (result.structured or {}).get("company_profile", {}).get("name", "企業")
    from datetime import date
    date_str = result.created_at.strftime("%Y-%m-%d") if result.created_at else date.today().isoformat()
    filename_base = f"{company_name}_{date_str}"

    if format == "pdf":
        content = generate_pdf(result)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'},
        )
    else:
        content = generate_docx(result)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.docx"'},
        )


# ---------------------------------------------------------------------------
# 分析履歴（F-008）
# ---------------------------------------------------------------------------

@router.get("/companies/{company_id}/runs", response_model=HistoryResponse, tags=["companies"])
async def get_company_runs(company_id: uuid.UUID, session: SessionDep) -> HistoryResponse:
    run_repo = AnalysisRunRepository(session)
    runs = await run_repo.list_by_company(company_id)
    return HistoryResponse(
        company_id=company_id,
        runs=[
            RunSummary(
                run_id=r.run_id,
                run_type=r.run_type,
                status=r.status,
                template=r.template,
                started_at=r.started_at,
                completed_at=r.completed_at,
                duration_ms=r.duration_ms,
                error_message=r.error_message,
                result_id=r.result_id,
            )
            for r in runs
        ],
    )


# ---------------------------------------------------------------------------
# シェア（F-012）
# ---------------------------------------------------------------------------

@router.post("/analysis/{result_id}/share", tags=["share"])
async def create_share(result_id: uuid.UUID, session: SessionDep) -> dict:
    repo = AnalysisResultRepository(session)
    result = await repo.find_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="分析結果が見つかりません")
    if not result.share_id:
        from datetime import datetime, timezone
        result.share_id = str(result_id)[:8]
        result.shared_at = datetime.now(timezone.utc)
        await session.commit()
    return {"share_id": result.share_id}


@router.get("/share/{share_id}", response_model=AnalysisResponse, tags=["share"])
async def get_shared_result(share_id: str, session: SessionDep) -> AnalysisResponse:
    repo = AnalysisResultRepository(session)
    result = await repo.find_by_share_id(share_id)
    if not result:
        raise HTTPException(status_code=404, detail="共有リンクが見つかりません")
    from src.analysis.service import _model_to_response
    return _model_to_response(result, is_cached=True)


# ---------------------------------------------------------------------------
# 深掘り分析（F-007）
# ---------------------------------------------------------------------------

@router.post("/companies/{company_id}/deep-research", tags=["companies"])
async def post_deep_research(
    company_id: uuid.UUID,
    body: dict,
    session: SessionDep,
) -> dict:
    question = body.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="question は必須です")
    result_id_str = body.get("result_id")
    result_id = uuid.UUID(result_id_str) if result_id_str else None
    session_id_str = body.get("session_id")
    session_id = uuid.UUID(session_id_str) if session_id_str else None
    return await ask_deep_research(company_id, result_id, question, session_id, session)


# ---------------------------------------------------------------------------
# 企業名検索（F-011）
# ---------------------------------------------------------------------------

@router.get("/search", response_model=SearchResponse, tags=["search"])
async def search_company(q: Annotated[str, Query(min_length=1)]) -> SearchResponse:
    results = await search_company_url(q)
    from src.analysis.schemas import SearchResult
    return SearchResponse(results=[SearchResult(**r) for r in results])


# ---------------------------------------------------------------------------
# 複数企業比較（F-013）
# ---------------------------------------------------------------------------

@router.post("/compare", response_model=CompareResponse, tags=["compare"])
async def post_compare(request: CompareRequest, session: SessionDep) -> CompareResponse:
    return await compare_companies(request, session)


# ---------------------------------------------------------------------------
# ヘルスチェック
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse, tags=["health"])
async def get_health() -> HealthResponse:
    return HealthResponse()
