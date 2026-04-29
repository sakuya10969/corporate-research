"""CrawlService — 企業サイトのクロール・ページ収集

既存の collector/service.py の collect_company_info() をラップし、
収集結果を pages / page_versions テーブルに永続化する。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.collector.service import collect_company_info
from src.db.repository import CompanyRepository, PageRepository
from src.shared.exceptions import CollectionError
from src.shared.logger import logger


@dataclass
class CrawlResult:
    """クロール結果のサマリー。"""

    company_id: uuid.UUID
    run_id: uuid.UUID
    pages_collected: int = 0
    sources: list[dict[str, str]] = field(default_factory=list)


class CrawlService:
    """企業サイトのクロール・ページ収集を担うサービス層。

    既存の collector/service.py の collect_company_info() をラップし、
    収集したページを pages テーブルに、ページ内容を page_versions テーブルに保存する。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._page_repo = PageRepository(session)
        self._company_repo = CompanyRepository(session)

    async def crawl(
        self,
        company_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> CrawlResult:
        """企業サイトをクロールし、pages/page_versions に保存する。

        1. Company レコードから primary_url を取得
        2. collect_company_info() で企業サイトをクロール
        3. 収集した各ページを pages / page_versions に永続化
        4. Company.last_page_crawl_at を更新

        Args:
            company_id: 対象企業の ID
            run_id: 紐づく AnalysisRun の ID

        Returns:
            CrawlResult: 収集結果のサマリー

        Raises:
            CollectionError: クロールに失敗した場合
        """
        # 1. 企業レコード取得
        company = await self._company_repo.find_by_id(company_id)
        if company is None:
            raise CollectionError(f"企業が見つかりません: {company_id}")

        logger.info(
            "クロール開始: company_id={}, url={}",
            company_id,
            company.primary_url,
        )

        # 2. 既存の collect_company_info() でクロール実行
        company_info = await collect_company_info(company.primary_url)

        # 3. 収集結果を pages / page_versions に永続化
        now = datetime.now(timezone.utc)
        sources_summary: list[dict[str, str]] = []

        for source in company_info.sources:
            page = await self._page_repo.get_or_create_page(
                company_id=company_id,
                url=source.url,
                page_type=source.category,
                title=source.title,
            )

            await self._page_repo.add_version(
                page=page,
                extracted_text=source.content,
                fetched_at=now,
                fetch_run_id=run_id,
                title=source.title,
                metadata=source.meta,
            )

            sources_summary.append(
                {
                    "url": source.url,
                    "title": source.title,
                    "category": source.category,
                }
            )

        # 4. Company.last_page_crawl_at を更新
        company.last_page_crawl_at = now
        await self._session.flush()

        pages_collected = len(sources_summary)
        logger.info(
            "クロール完了: company_id={}, {} ページ収集",
            company_id,
            pages_collected,
        )

        return CrawlResult(
            company_id=company_id,
            run_id=run_id,
            pages_collected=pages_collected,
            sources=sources_summary,
        )
