# 設計書: data-persistence

## 概要

PostgreSQL + SQLAlchemy async + Alembic によるデータ永続化基盤。企業マスタ・分析結果・分析実行履歴の3テーブルを管理し、キャッシュチェックと永続化ロジックをAnalysisServiceに統合する。

## アーキテクチャ

```
POST /api/analysis
  └── AnalysisService.analyze_company()
        ├── CompanyRepository.find_by_url() → キャッシュチェック
        ├── (キャッシュあり & force_refresh=false) → AnalysisResultRepository.find_latest_by_company()
        ├── (新規 or force_refresh=true) → CollectorService + LLM分析
        ├── CompanyRepository.upsert()
        ├── AnalysisResultRepository.save()
        └── AnalysisRunRepository.create() / update_status()

GET /api/analysis/{result_id}
  └── AnalysisResultRepository.find_by_id()
```

## コンポーネントとインターフェース

### `server/src/shared/db.py`
```python
# async engine 作成
engine = create_async_engine(settings.database_url, echo=False)

# FastAPI Depends 対応セッション
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
```

### `server/src/db/models.py`

#### Company（ORM モデル）
```python
class Company(Base):
    __tablename__ = "companies"
    company_id: UUID (PK)
    url: str
    normalized_url: str (UNIQUE)
    domain: str
    name: str | None
    first_crawled_at: datetime | None
    last_crawled_at: datetime | None
    crawl_count: int
    created_at: datetime
    updated_at: datetime
```

#### AnalysisResult（ORM モデル）
```python
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    result_id: UUID (PK)
    company_id: UUID (FK → companies)
    run_id: UUID | None
    template: str
    llm_model: str
    structured: dict (JSONB)
    summary: dict (JSONB)
    scores: dict | None (JSONB)
    diff_report: str | None
    sources: list (JSONB)
    raw_sources: list (JSONB)
    markdown_page: str | None
    share_id: str | None (UNIQUE)
    shared_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

#### AnalysisRun（ORM モデル）
```python
class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    run_id: UUID (PK)
    company_id: UUID (FK → companies)
    result_id: UUID | None
    run_type: str  # initial / refresh / deep_research
    template: str
    status: str  # pending / running / completed / failed
    error_message: str | None
    force_refresh: bool
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    created_at: datetime
    updated_at: datetime
```

### `server/src/db/repository.py`

#### CompanyRepository
```python
async def upsert(session, url, normalized_url, domain, name) -> Company
async def find_by_url(session, normalized_url) -> Company | None
```

#### AnalysisResultRepository
```python
async def save(session, company_id, run_id, data) -> AnalysisResult
async def find_latest_by_company(session, company_id) -> AnalysisResult | None
async def find_by_id(session, result_id) -> AnalysisResult | None
async def find_by_share_id(session, share_id) -> AnalysisResult | None
async def list_by_company(session, company_id) -> list[AnalysisResult]
```

#### AnalysisRunRepository
```python
async def create(session, company_id, run_type, template, force_refresh) -> AnalysisRun
async def update_status(session, run_id, status, result_id, error_message) -> AnalysisRun
async def list_by_company(session, company_id) -> list[AnalysisRun]
```

## データモデル

### AnalysisRequest（拡張）
```python
class AnalysisRequest(BaseModel):
    company_url: str
    force_refresh: bool = False
    template: str = "general"
```

### AnalysisResponse（拡張）
```python
class AnalysisResponse(BaseModel):
    # 既存フィールド...
    result_id: UUID | None
    company_id: UUID | None
    is_cached: bool
    analyzed_at: datetime | None
```

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。*

Property 1: 分析結果の保存と取得の一貫性（ラウンドトリップ）
*For any* 有効な企業URLに対して、分析を実行して保存した後、同じ `result_id` で取得した結果は元の分析結果と等しい
**Validates: Requirements 1.1, 1.2, 3.1**

Property 2: キャッシュ返却の一貫性
*For any* 既に分析済みの企業URLに対して `force_refresh=false` で再リクエストした場合、`is_cached=true` が返される
**Validates: Requirements 2.1**

Property 3: force_refresh によるキャッシュ無効化
*For any* 既に分析済みの企業URLに対して `force_refresh=true` で再リクエストした場合、`is_cached=false` が返される
**Validates: Requirements 2.4**

## エラーハンドリング

| エラー種別 | HTTPステータス | 説明 |
|-----------|--------------|------|
| result_id が存在しない | 404 | AnalysisResult not found |
| DB接続エラー | 500 | データベース接続失敗 |

## テスト戦略

### ユニットテスト
- CompanyRepository.upsert() の冪等性（同一URLで2回呼んでも重複しない）
- AnalysisResultRepository.find_by_id() の存在・非存在ケース

### プロパティベーステスト
- Property 1: 任意の分析データを保存→取得してラウンドトリップを検証（最低100回）
- Property 2, 3: 任意のURLに対してキャッシュフラグの正確性を検証
- タグ形式: `Feature: data-persistence, Property {N}: {property_text}`
