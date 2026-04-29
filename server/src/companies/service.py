"""CompanyService — 企業の登録・検索・基本情報管理"""

from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Company
from src.db.repository import CompanyRepository
from src.shared.logger import logger


class CompanyService:
    """企業の登録・検索・基本情報管理を担うサービス層。

    既存の CompanyRepository を活用し、企業登録ワークフローに
    必要なビジネスロジック（URL正規化・重複チェック・初期状態設定）を提供する。
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CompanyRepository(session)

    async def register_company(
        self,
        url: str,
        user_id: uuid.UUID | None = None,
    ) -> Company:
        """企業URLを登録する。

        - URL正規化（スキーム+ドメイン抽出）を実行し、normalized_url と primary_domain を設定する
        - 登録済みURLと同一の正規化URLが送信された場合、既存の企業レコードを返却する
        - 新規登録時は status="pending" に設定し、重い同期処理は実行しない

        Returns:
            Company: 新規作成または既存の企業レコード
        """
        normalized_url, domain = CompanyRepository._normalize(url)

        # 重複チェック: 同一 normalized_url が存在すれば既存レコードを返却
        existing = await self._repo.find_by_url(url)
        if existing is not None:
            logger.info("企業登録: 既存レコードを返却 ({})", normalized_url)
            return existing

        # 新規登録: status="pending"、分析関連フィールドは未設定
        company = Company(
            primary_url=url,
            normalized_url=normalized_url,
            primary_domain=domain,
            status="pending",
        )
        self._session.add(company)
        await self._session.flush()

        logger.info(
            "企業登録: 新規作成 ({}, id={})", normalized_url, company.company_id
        )
        return company

    async def get_company(self, company_id: uuid.UUID) -> Company:
        """企業詳細を取得する。

        Raises:
            HTTPException: 企業が見つからない場合 (404)
        """
        company = await self._repo.find_by_id(company_id)
        if company is None:
            raise HTTPException(status_code=404, detail="企業が見つかりません")
        return company

    async def list_companies(
        self,
        user_id: uuid.UUID | None = None,
    ) -> list[Company]:
        """企業一覧を取得する。"""
        return await self._repo.list_all()

    async def update_display_name(
        self,
        company_id: uuid.UUID,
        name: str,
    ) -> Company:
        """表示名を更新する（LLM抽出結果から呼ばれる想定）。

        Raises:
            HTTPException: 企業が見つからない場合 (404)
        """
        company = await self._repo.find_by_id(company_id)
        if company is None:
            raise HTTPException(status_code=404, detail="企業が見つかりません")

        company.display_name = name
        await self._session.flush()

        logger.info("表示名更新: {} → {}", company.company_id, name)
        return company
