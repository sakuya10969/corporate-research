---
name: fastapi-pydantic
description: FastAPI + Pydantic によるAPIスキーマ設計とエンドポイント実装パターン。server/src/ 配下のコードを書く際に使用する。
license: MIT
metadata:
  author: project
  version: "1.0"
---

# FastAPI + Pydantic — このプロジェクトでの使い方

## モジュール構成

```
server/src/
├── analysis/       # 分析（router.py / service.py / schemas.py / prompts.py）
├── collector/      # 情報収集（service.py / parsers.py）
├── db/             # DBモデル・リポジトリ（models.py / repository.py）
├── deep_research/  # 深掘り分析 F-007
├── download/       # PDF/Word生成 F-009
├── search/         # 企業名検索 F-011
└── shared/         # 共通（config / db / llm / exceptions / logger）
```

モジュール間の依存: `shared` は他モジュールを参照しない。各モジュールは `shared` のみ参照可。

## Pydantic スキーマ

```python
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal
import uuid
from datetime import datetime

class AnalysisRequest(BaseModel):
    company_url: str = Field(..., min_length=1, pattern=r"^https?://.*")
    force_refresh: bool = Field(False)
    template: Literal["general", "job_hunting", "investment", "competitor", "partnership"] = "general"

# ネストモデルは default_factory を使う
class StructuredData(BaseModel):
    company_profile: CompanyProfile = Field(default_factory=CompanyProfile)
    business_domains: list[str] = Field(default_factory=list)

# UUID / datetime
class AnalysisResponse(BaseModel):
    result_id: uuid.UUID | None = None
    analyzed_at: datetime | None = None
```

## FastAPI Router

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.shared.db import get_session
from typing import Annotated

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]

@router.post("/analysis", response_model=AnalysisResponse)
async def post_analysis(request: AnalysisRequest, session: SessionDep) -> AnalysisResponse:
    return await analyze_company(request, session)

# 404
result = await repo.find_by_id(result_id)
if not result:
    raise HTTPException(status_code=404, detail="分析結果が見つかりません")
```

## main.py でのルーター登録

```python
app.include_router(analysis_router, prefix="/api")
```

## 設定管理

```python
from src.shared.config import get_settings
settings = get_settings()  # lru_cache済み
model = settings.azure_deployment
```

## 例外

`src/shared/exceptions.py` に定義済み:
- `CollectionError` → HTTP 500
- `AnalysisError` → HTTP 500
- `ExternalServiceError` → HTTP 503

```python
from src.shared.exceptions import CollectionError
raise CollectionError(f"取得失敗: {url}")
```

## 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| Pydantic モデル | PascalCase | `AnalysisRequest` |
| 関数 | snake_case | `analyze_company` |
| 定数 | UPPER_SNAKE_CASE | `MAX_PAGES` |

## OpenAPI → Orval 連携

スキーマ変更後は必ず `cd client && npx orval` を実行してフロントエンドの型を再生成する。
