"""CompanyRepository — 企業マスタの CRUD"""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Company


class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    @staticmethod
    def _normalize(url: str) -> tuple[str, str]:
        """(normalized_url, domain) を返す。企業識別はホスト単位に寄せる。"""
        p = urlparse(url.strip())
        scheme = (p.scheme or "https").lower()
        domain = p.netloc.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return f"{scheme}://{domain}", domain

    async def find_by_url(self, url: str) -> Company | None:
        normalized, _ = self._normalize(url)
        result = await self._s.execute(
            select(Company).where(Company.normalized_url == normalized)
        )
        return result.scalar_one_or_none()

    async def find_by_id(self, company_id) -> Company | None:
        result = await self._s.execute(
            select(Company).where(Company.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Company]:
        """全企業を作成日時の降順で取得する。"""
        result = await self._s.execute(
            select(Company).order_by(Company.created_at.desc())
        )
        return list(result.scalars().all())

    async def upsert(self, url: str, name: str | None = None) -> Company:
        normalized, domain = self._normalize(url)
        company = await self.find_by_url(url)
        now = datetime.now(timezone.utc)
        if company is None:
            company = Company(
                primary_url=url,
                normalized_url=normalized,
                primary_domain=domain,
                display_name=name,
                first_analyzed_at=now,
                last_analyzed_at=now,
                analysis_count=1,
            )
            self._s.add(company)
        else:
            company.primary_url = url
            company.last_analyzed_at = now
            company.analysis_count += 1
            if name:
                company.display_name = name
        await self._s.flush()
        return company
