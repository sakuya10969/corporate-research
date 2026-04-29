"""PageRepository — 収集ページとバージョンの永続化"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Page, PageVersion


class PageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    @staticmethod
    def normalize_page_url(url: str) -> str:
        parsed = urlsplit(url.strip())
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        return urlunsplit((parsed.scheme.lower() or "https", netloc, path, "", ""))

    @staticmethod
    def build_content_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def get_or_create_page(
        self,
        company_id,
        url: str,
        page_type: str | None = None,
        title: str | None = None,
    ) -> Page:
        normalized_url = self.normalize_page_url(url)
        result = await self._s.execute(
            select(Page).where(
                Page.company_id == company_id,
                Page.normalized_url == normalized_url,
            )
        )
        page = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if page is None:
            page = Page(
                company_id=company_id,
                url=url,
                normalized_url=normalized_url,
                page_type=page_type,
                title=title,
                first_seen_at=now,
                last_seen_at=now,
            )
            self._s.add(page)
        else:
            page.url = url
            page.last_seen_at = now
            if page_type:
                page.page_type = page_type
            if title:
                page.title = title
        await self._s.flush()
        return page

    async def add_version(
        self,
        page: Page,
        extracted_text: str,
        fetched_at: datetime | None = None,
        fetch_run_id=None,
        title: str | None = None,
        metadata: dict | None = None,
    ) -> PageVersion:
        fetched_at = fetched_at or datetime.now(timezone.utc)
        content_hash = self.build_content_hash(extracted_text)
        previous_hash = page.latest_content_hash
        version = PageVersion(
            page_id=page.page_id,
            fetch_run_id=fetch_run_id,
            content_hash=content_hash,
            title=title or page.title,
            meta_description=(metadata or {}).get("description"),
            lang=(metadata or {}).get("lang"),
            extracted_text=extracted_text,
            page_metadata=metadata or {},
            fetched_at=fetched_at,
            content_length=len(extracted_text),
        )
        self._s.add(version)
        page.latest_content_hash = content_hash
        page.last_seen_at = fetched_at
        if previous_hash != content_hash:
            page.last_changed_at = fetched_at
        elif page.last_changed_at is None:
            page.last_changed_at = fetched_at
        await self._s.flush()
        return version
