"""JobManager — バックグラウンドジョブのオーケストレーション

crawl → extract → analyze のフルパイプラインを BackgroundTasks で実行し、
Company.status と AnalysisRun の状態を管理する。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.analysis_service import AnalysisService
from src.crawler.service import CrawlService
from src.db.models import AnalysisRun
from src.db.repository import AnalysisRunRepository, CompanyRepository
from src.extraction.service import ExtractionService
from src.shared.db import get_async_session
from src.shared.exceptions import AnalysisError, CollectionError, ExternalServiceError
from src.shared.logger import logger


class JobManager:
    """バックグラウンドジョブのオーケストレーション。

    FastAPI BackgroundTasks を使用してフルパイプライン
    (crawl → extract → analyze) を非同期実行し、
    Company.status / AnalysisRun の状態遷移を管理する。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._run_repo = AnalysisRunRepository(session)
        self._company_repo = CompanyRepository(session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def enqueue_full_pipeline(
        self,
        company_id: uuid.UUID,
        background_tasks: BackgroundTasks,
        template: str = "general",
        force_refresh: bool = False,
    ) -> AnalysisRun:
        """クロール→抽出→分析のフルパイプラインをキューに追加する。

        1. AnalysisRun レコードを作成 (status="pending")
        2. BackgroundTasks に _run_pipeline を登録

        Args:
            company_id: 対象企業の ID
            background_tasks: FastAPI BackgroundTasks
            template: 分析テンプレート
            force_refresh: 強制リフレッシュフラグ

        Returns:
            作成された AnalysisRun
        """
        run = AnalysisRun(
            company_id=company_id,
            run_type="initial" if not force_refresh else "refresh",
            template=template,
            status="pending",
            force_refresh=force_refresh,
            input_params={
                "template": template,
                "force_refresh": force_refresh,
            },
        )
        run = await self._run_repo.create(run)
        await self._session.commit()

        background_tasks.add_task(self._run_pipeline, company_id, run.run_id, template)

        logger.info(
            "パイプラインをキューに追加: company_id={}, run_id={}",
            company_id,
            run.run_id,
        )
        return run

    async def get_run_status(self, run_id: uuid.UUID) -> AnalysisRun | None:
        """ジョブの状態を取得する。

        Args:
            run_id: AnalysisRun の ID

        Returns:
            AnalysisRun またはなければ None
        """
        return await self._run_repo.find_by_id(run_id)

    # ------------------------------------------------------------------
    # Pipeline execution (BackgroundTask)
    # ------------------------------------------------------------------

    async def _run_pipeline(
        self,
        company_id: uuid.UUID,
        run_id: uuid.UUID,
        template: str,
    ) -> None:
        """パイプライン実行 (BackgroundTask から呼ばれる)。

        BackgroundTask はリクエストのライフサイクル外で動作するため、
        新しい AsyncSession を作成して使用する。

        状態遷移: pending → crawling → extracting → analyzing → completed
        """
        async with get_async_session() as session:
            run_repo = AnalysisRunRepository(session)
            company_repo = CompanyRepository(session)

            try:
                # パイプライン開始
                started_at = datetime.now(timezone.utc)
                run = await run_repo.find_by_id(run_id)
                if run:
                    run.status = "running"
                    run.started_at = started_at
                    await session.flush()

                logger.info(
                    "パイプライン開始: company_id={}, run_id={}",
                    company_id,
                    run_id,
                )

                # Phase 1: Crawl
                await self._update_status(
                    session,
                    company_repo,
                    run_repo,
                    company_id,
                    run_id,
                    "crawling",
                )
                crawl_service = CrawlService(session)
                crawl_result = await crawl_service.crawl(company_id, run_id)
                await session.commit()

                # Phase 2: Extract
                await self._update_status(
                    session,
                    company_repo,
                    run_repo,
                    company_id,
                    run_id,
                    "extracting",
                )
                extraction_service = ExtractionService(session)
                structured = await extraction_service.extract(company_id, run_id)
                await session.commit()

                # Phase 3: Analyze
                await self._update_status(
                    session,
                    company_repo,
                    run_repo,
                    company_id,
                    run_id,
                    "analyzing",
                )
                analysis_service = AnalysisService(session)
                await analysis_service.analyze(
                    company_id,
                    run_id,
                    template,
                    structured=structured,
                )
                await session.commit()

                # 完了
                completed_at = datetime.now(timezone.utc)
                duration_ms = int((completed_at - started_at).total_seconds() * 1000)

                company = await company_repo.find_by_id(company_id)
                if company:
                    company.status = "completed"

                run = await run_repo.find_by_id(run_id)
                if run:
                    run.status = "completed"
                    run.completed_at = completed_at
                    run.duration_ms = duration_ms
                    run.collection_summary = {
                        "phases": ["crawling", "extracting", "analyzing"],
                        "pages_collected": crawl_result.pages_collected,
                        "template": template,
                    }

                await session.commit()

                logger.info(
                    "パイプライン完了: company_id={}, run_id={}, {}ms",
                    company_id,
                    run_id,
                    duration_ms,
                )

            except CollectionError as e:
                await self._handle_failure(
                    session,
                    company_repo,
                    run_repo,
                    company_id,
                    run_id,
                    e,
                    "COLLECTION_ERROR",
                )
            except AnalysisError as e:
                await self._handle_failure(
                    session,
                    company_repo,
                    run_repo,
                    company_id,
                    run_id,
                    e,
                    "ANALYSIS_ERROR",
                )
            except ExternalServiceError as e:
                await self._handle_failure(
                    session,
                    company_repo,
                    run_repo,
                    company_id,
                    run_id,
                    e,
                    "EXTERNAL_SERVICE_ERROR",
                )
            except Exception as e:
                await self._handle_failure(
                    session,
                    company_repo,
                    run_repo,
                    company_id,
                    run_id,
                    e,
                    "UNEXPECTED_ERROR",
                )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _update_status(
        session: AsyncSession,
        company_repo: CompanyRepository,
        run_repo: AnalysisRunRepository,
        company_id: uuid.UUID,
        run_id: uuid.UUID,
        status: str,
    ) -> None:
        """Company.status と AnalysisRun.status を同時に更新する。"""
        company = await company_repo.find_by_id(company_id)
        if company:
            company.status = status

        run = await run_repo.find_by_id(run_id)
        if run:
            run.status = status

        await session.flush()

    @staticmethod
    async def _handle_failure(
        session: AsyncSession,
        company_repo: CompanyRepository,
        run_repo: AnalysisRunRepository,
        company_id: uuid.UUID,
        run_id: uuid.UUID,
        error: Exception,
        error_code: str,
    ) -> None:
        """共通エラーハンドリング: status 更新 + エラー情報記録。"""
        try:
            company = await company_repo.find_by_id(company_id)
            if company:
                company.status = "failed"

            run = await run_repo.find_by_id(run_id)
            if run:
                run.status = "failed"
                run.error_code = error_code
                run.error_message = str(error)[:1000]
                run.completed_at = datetime.now(timezone.utc)
                if run.started_at:
                    run.duration_ms = int(
                        (run.completed_at - run.started_at).total_seconds() * 1000
                    )

            await session.commit()
        except Exception as commit_err:
            logger.error(
                "エラーハンドリング中のコミット失敗: {}",
                commit_err,
            )

        logger.error(
            "パイプライン失敗: company_id={}, run_id={}, error_code={}, error={}",
            company_id,
            run_id,
            error_code,
            error,
        )
