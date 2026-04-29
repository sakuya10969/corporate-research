"""企業管理エンドポイント

POST /api/companies                                 — 企業登録
GET  /api/companies                                 — 企業一覧
GET  /api/companies/{company_id}                    — 企業詳細
POST /api/companies/{company_id}/crawl              — クロールジョブ開始
POST /api/companies/{company_id}/analysis-runs      — 分析ジョブ開始
GET  /api/companies/{company_id}/analysis-results/latest — 最新分析結果
GET  /api/companies/{company_id}/analysis-results   — 分析履歴
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.analysis_service import AnalysisService
from src.analysis.schemas import AnalysisResponse, RunSummary
from src.analysis.service import _model_to_response
from src.companies.schemas import (
    AnalysisHistoryResponse,
    CompanyDetailResponse,
    CompanyListResponse,
    CompanyResponse,
    RegisterCompanyRequest,
    RunStatusResponse,
    StartAnalysisRequest,
)
from src.companies.service import CompanyService
from src.db.repository import AnalysisResultRepository, AnalysisRunRepository
from src.jobs.manager import JobManager
from src.shared.db import get_session

router = APIRouter(prefix="/api/companies", tags=["companies"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------


def _company_to_response(company) -> CompanyResponse:
    """Company ORM モデル → CompanyResponse 変換"""
    return CompanyResponse(
        company_id=company.company_id,
        primary_url=company.primary_url,
        normalized_url=company.normalized_url,
        display_name=company.display_name,
        status=company.status,
        last_page_crawl_at=company.last_page_crawl_at,
        last_analyzed_at=company.last_analyzed_at,
        analysis_count=company.analysis_count or 0,
        created_at=company.created_at,
    )


def _run_to_status_response(run) -> RunStatusResponse:
    """AnalysisRun ORM モデル → RunStatusResponse 変換"""
    return RunStatusResponse(
        run_id=run.run_id,
        company_id=run.company_id,
        status=run.status,
        run_type=run.run_type,
        template=run.template,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
        result_id=run.result.result_id if run.result else None,
    )


def _run_to_summary(run) -> RunSummary:
    """AnalysisRun ORM モデル → RunSummary 変換"""
    return RunSummary(
        run_id=run.run_id,
        run_type=run.run_type,
        status=run.status,
        template=run.template,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
        result_id=run.result.result_id if run.result else None,
    )


# ---------------------------------------------------------------------------
# POST /api/companies — 企業登録 (Req 10.1)
# ---------------------------------------------------------------------------


@router.post("", response_model=CompanyResponse, status_code=201)
async def register_company(
    request: RegisterCompanyRequest,
    background_tasks: BackgroundTasks,
    session: SessionDep,
) -> CompanyResponse:
    """企業URLを登録し、フルパイプライン（クロール→抽出→分析）を自動開始する。

    重複URLの場合は既存レコードを返却する（201ではなく200相当だが冪等性を優先）。
    """
    service = CompanyService(session)
    company = await service.register_company(url=request.url)

    # 新規登録（status=pending）の場合のみパイプラインを自動開始
    if company.status == "pending":
        job_manager = JobManager(session)
        await job_manager.enqueue_full_pipeline(
            company_id=company.company_id,
            background_tasks=background_tasks,
        )

    await session.commit()
    return _company_to_response(company)


# ---------------------------------------------------------------------------
# GET /api/companies — 企業一覧 (Req 10.2)
# ---------------------------------------------------------------------------


@router.get("", response_model=CompanyListResponse)
async def list_companies(session: SessionDep) -> CompanyListResponse:
    """登録済み企業の一覧を返却する。"""
    service = CompanyService(session)
    companies = await service.list_companies()
    return CompanyListResponse(
        companies=[_company_to_response(c) for c in companies],
    )


# ---------------------------------------------------------------------------
# GET /api/companies/{company_id} — 企業詳細 (Req 10.3)
# ---------------------------------------------------------------------------


@router.get("/{company_id}", response_model=CompanyDetailResponse)
async def get_company(
    company_id: uuid.UUID,
    session: SessionDep,
) -> CompanyDetailResponse:
    """企業詳細を返却する。最新分析結果と直近の実行履歴を含む。"""
    service = CompanyService(session)
    company = await service.get_company(company_id)

    # 最新分析結果
    result_repo = AnalysisResultRepository(session)
    latest_result_model = await result_repo.find_latest_by_company(company_id)
    latest_result = (
        _model_to_response(latest_result_model, is_cached=True)
        if latest_result_model
        else None
    )

    # 直近の実行履歴（最大10件）
    run_repo = AnalysisRunRepository(session)
    runs = await run_repo.list_by_company(company_id, limit=10)
    recent_runs = [_run_to_summary(r) for r in runs]

    return CompanyDetailResponse(
        company_id=company.company_id,
        primary_url=company.primary_url,
        normalized_url=company.normalized_url,
        display_name=company.display_name,
        status=company.status,
        last_page_crawl_at=company.last_page_crawl_at,
        last_analyzed_at=company.last_analyzed_at,
        analysis_count=company.analysis_count or 0,
        created_at=company.created_at,
        latest_result=latest_result,
        recent_runs=recent_runs,
    )


# ---------------------------------------------------------------------------
# POST /api/companies/{company_id}/crawl — クロールジョブ開始 (Req 10.4)
# ---------------------------------------------------------------------------


@router.post("/{company_id}/crawl", response_model=RunStatusResponse)
async def start_crawl(
    company_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: SessionDep,
) -> RunStatusResponse:
    """指定企業のクロールジョブ（フルパイプライン）を開始する。"""
    service = CompanyService(session)
    company = await service.get_company(company_id)

    job_manager = JobManager(session)
    run = await job_manager.enqueue_full_pipeline(
        company_id=company.company_id,
        background_tasks=background_tasks,
        force_refresh=True,
    )

    return RunStatusResponse(
        run_id=run.run_id,
        company_id=run.company_id,
        status=run.status,
        run_type=run.run_type,
        template=run.template,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
    )


# ---------------------------------------------------------------------------
# POST /api/companies/{company_id}/analysis-runs — 分析ジョブ開始 (Req 10.5)
# ---------------------------------------------------------------------------


@router.post("/{company_id}/analysis-runs", response_model=RunStatusResponse)
async def start_analysis(
    company_id: uuid.UUID,
    request: StartAnalysisRequest,
    background_tasks: BackgroundTasks,
    session: SessionDep,
) -> RunStatusResponse:
    """分析ジョブを開始する。

    - force_refresh=true: フルパイプライン（再クロール→抽出→分析）
    - force_refresh=false かつ蓄積データあり: Deep Analysis（テンプレート別再分析）
    - force_refresh=false かつ蓄積データなし: フルパイプライン
    """
    service = CompanyService(session)
    company = await service.get_company(company_id)

    if request.force_refresh:
        # フルパイプライン（再クロールから）
        job_manager = JobManager(session)
        run = await job_manager.enqueue_full_pipeline(
            company_id=company.company_id,
            background_tasks=background_tasks,
            template=request.template,
            force_refresh=True,
        )
        return RunStatusResponse(
            run_id=run.run_id,
            company_id=run.company_id,
            status=run.status,
            run_type=run.run_type,
            template=run.template,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_ms=run.duration_ms,
            error_message=run.error_message,
        )

    # 蓄積データがあるか確認（last_page_crawl_at が設定されていれば蓄積あり）
    if company.last_page_crawl_at is not None:
        # Deep Analysis: 蓄積データを使用したテンプレート別再分析
        analysis_service = AnalysisService(session)
        result = await analysis_service.run_deep_analysis(
            company_id=company.company_id,
            template=request.template,
        )
        await session.commit()

        # Deep Analysis で作成された run を取得
        run_repo = AnalysisRunRepository(session)
        run = await run_repo.find_by_id(result.run_id)
        if run is None:
            raise HTTPException(status_code=500, detail="分析ジョブの取得に失敗しました")

        return RunStatusResponse(
            run_id=run.run_id,
            company_id=run.company_id,
            status=run.status,
            run_type=run.run_type,
            template=run.template,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_ms=run.duration_ms,
            error_message=run.error_message,
            result_id=result.result_id,
        )

    # 蓄積データなし → フルパイプライン
    job_manager = JobManager(session)
    run = await job_manager.enqueue_full_pipeline(
        company_id=company.company_id,
        background_tasks=background_tasks,
        template=request.template,
    )
    return RunStatusResponse(
        run_id=run.run_id,
        company_id=run.company_id,
        status=run.status,
        run_type=run.run_type,
        template=run.template,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        error_message=run.error_message,
    )


# ---------------------------------------------------------------------------
# GET /api/companies/{company_id}/analysis-results/latest — 最新分析結果 (Req 10.6)
# ---------------------------------------------------------------------------


@router.get(
    "/{company_id}/analysis-results/latest",
    response_model=AnalysisResponse,
)
async def get_latest_result(
    company_id: uuid.UUID,
    session: SessionDep,
) -> AnalysisResponse:
    """指定企業の最新分析結果を返却する。"""
    # 企業の存在確認
    service = CompanyService(session)
    await service.get_company(company_id)

    result_repo = AnalysisResultRepository(session)
    result = await result_repo.find_latest_by_company(company_id)
    if result is None:
        raise HTTPException(status_code=404, detail="分析結果が見つかりません")

    return _model_to_response(result, is_cached=True)


# ---------------------------------------------------------------------------
# GET /api/companies/{company_id}/analysis-results — 分析履歴 (Req 10.7)
# ---------------------------------------------------------------------------


@router.get(
    "/{company_id}/analysis-results",
    response_model=AnalysisHistoryResponse,
)
async def list_results(
    company_id: uuid.UUID,
    session: SessionDep,
) -> AnalysisHistoryResponse:
    """指定企業の分析結果履歴を返却する。"""
    # 企業の存在確認
    service = CompanyService(session)
    await service.get_company(company_id)

    result_repo = AnalysisResultRepository(session)
    results = await result_repo.list_by_company(company_id)

    return AnalysisHistoryResponse(
        company_id=company_id,
        results=[_model_to_response(r, is_cached=True) for r in results],
    )
