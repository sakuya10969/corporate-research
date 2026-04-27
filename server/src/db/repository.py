"""リポジトリ層 — Company / AnalysisResult / AnalysisRun の CRUD"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import AnalysisResult, AnalysisRun, Company


# ---------------------------------------------------------------------------
# CompanyRepository
# ---------------------------------------------------------------------------


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    @staticmethod
    def _normalize(url: str) -> tuple[str, str]:
        """(normalized_url, domain) を返す"""
        p = urlparse(url.strip())
        scheme = p.scheme or "https"
        domain = p.netloc
        return f"{scheme}://{domain}", domain

    async def find_by_url(self, url: str) -> Company | None:
        normalized, _ = self._normalize(url)
        result = await self._s.execute(
            select(Company).where(Company.normalized_url == normalized)
        )
        return result.scalar_one_or_none()

    async def upsert(self, url: str, name: str | None = None) -> Company:
        normalized, domain = self._normalize(url)
        company = await self.find_by_url(url)
        now = datetime.now(timezone.utc)
        if company is None:
            company = Company(
                url=url,
                normalized_url=normalized,
                domain=domain,
                name=name,
                first_crawled_at=now,
                last_crawled_at=now,
                crawl_count=1,
            )
            self._s.add(company)
        else:
            company.last_crawled_at = now
            company.crawl_count += 1
            if name:
                company.name = name
        await self._s.flush()
        return company


# ---------------------------------------------------------------------------
# AnalysisResultRepository
# ---------------------------------------------------------------------------


class AnalysisResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save(self, result: AnalysisResult) -> AnalysisResult:
        self._s.add(result)
        await self._s.flush()
        return result

    async def find_latest_by_company(self, company_id: uuid.UUID) -> AnalysisResult | None:
        res = await self._s.execute(
            select(AnalysisResult)
            .where(AnalysisResult.company_id == company_id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def find_by_id(self, result_id: uuid.UUID) -> AnalysisResult | None:
        res = await self._s.execute(
            select(AnalysisResult).where(AnalysisResult.result_id == result_id)
        )
        return res.scalar_one_or_none()

    async def find_by_share_id(self, share_id: str) -> AnalysisResult | None:
        res = await self._s.execute(
            select(AnalysisResult).where(AnalysisResult.share_id == share_id)
        )
        return res.scalar_one_or_none()

    async def list_by_company(self, company_id: uuid.UUID, limit: int = 20) -> list[AnalysisResult]:
        res = await self._s.execute(
            select(AnalysisResult)
            .where(AnalysisResult.company_id == company_id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())


# ---------------------------------------------------------------------------
# AnalysisRunRepository
# ---------------------------------------------------------------------------


class AnalysisRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(self, run: AnalysisRun) -> AnalysisRun:
        self._s.add(run)
        await self._s.flush()
        return run

    async def update_status(
        self,
        run: AnalysisRun,
        status: str,
        result_id: uuid.UUID | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> AnalysisRun:
        run.status = status
        if result_id:
            run.result_id = result_id
        if error_code:
            run.error_code = error_code
        if error_message:
            run.error_message = error_message
        if status in ("completed", "failed"):
            run.completed_at = datetime.now(timezone.utc)
            if run.started_at:
                run.duration_ms = int(
                    (run.completed_at - run.started_at).total_seconds() * 1000
                )
        await self._s.flush()
        return run

    async def list_by_company(self, company_id: uuid.UUID, limit: int = 50) -> list[AnalysisRun]:
        res = await self._s.execute(
            select(AnalysisRun)
            .where(AnalysisRun.company_id == company_id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())
