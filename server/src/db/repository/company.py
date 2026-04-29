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
