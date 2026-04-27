---
name: sqlalchemy-async
description: SQLAlchemy async + Alembic のパターン集。server/src/db/ 配下のコードを書く際に使用する。
license: MIT
metadata:
  author: project
  version: "1.0"
---

# SQLAlchemy Async + Alembic — このプロジェクトでの使い方

## セッション取得（FastAPI Depends）

```python
from src.shared.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends

SessionDep = Annotated[AsyncSession, Depends(get_session)]
```

## ORMモデルの書き方

```python
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import Text, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Company(Base):
    __tablename__ = "companies"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now(),
    )
    # リレーション
    analysis_results: Mapped[list[AnalysisResult]] = relationship(
        "AnalysisResult", back_populates="company", cascade="all, delete-orphan"
    )
```

## JSONB カラム

```python
# dict型
structured: Mapped[dict] = mapped_column(JSONB, nullable=False)
scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

# list型
sources: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
```

## リポジトリパターン

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class CompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_id(self, company_id: uuid.UUID) -> Company | None:
        result = await self.session.execute(
            select(Company).where(Company.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def save(self, company: Company) -> Company:
        self.session.add(company)
        await self.session.flush()
        await self.session.refresh(company)
        return company
```

## Alembic マイグレーション

```bash
cd server

# マイグレーションファイル生成（モデル変更後）
uv run alembic revision --autogenerate -m "add_page_snapshots_table"

# 適用
uv run alembic upgrade head

# ロールバック
uv run alembic downgrade -1

# 現在のリビジョン確認
uv run alembic current
```

マイグレーションファイルは `server/alembic/versions/` に生成される。自動生成後は必ず内容を確認してから適用すること。

## テーブル一覧（このプロジェクト）

| テーブル | モデルクラス | 用途 |
|---------|------------|------|
| `companies` | `Company` | 企業マスタ |
| `analysis_results` | `AnalysisResult` | 分析結果（JSONB） |
| `analysis_runs` | `AnalysisRun` | 実行履歴・ステータス管理 |
| `page_snapshots` | `PageSnapshot` | 差分検知用スナップショット（F-006） |
| `deep_research_sessions` | `DeepResearchSession` | 深掘り分析セッション（F-007） |
| `deep_research_messages` | `DeepResearchMessage` | 深掘り質問・回答履歴（F-007） |
| `comparison_sessions` | `ComparisonSession` | 複数企業比較（F-013） |

## 注意事項

- PKは全テーブルUUID v4（`default=uuid.uuid4`）
- タイムスタンプは `DateTime(timezone=True)` を使う（naive datetimeは使わない）
- `session.commit()` はルーター層またはサービス層の最後に1回だけ呼ぶ
- `session.flush()` + `session.refresh()` でIDを即時取得できる
