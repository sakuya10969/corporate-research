# データベース設計

使用DB: PostgreSQL 17 + pgvector
ORM: SQLAlchemy (async) + Alembic

---

## テーブル一覧

| テーブル名 | 概要 | 対応機能 |
|-----------|------|---------|
| `companies` | 企業マスタ | F-005 |
| `analysis_results` | 分析結果 | F-005, F-009, F-012, F-014 |
| `analysis_runs` | 分析実行履歴 | F-005, F-008 |
| `page_snapshots` | ページ取得スナップショット（差分検知用） | F-006 |
| `deep_research_sessions` | 深掘り分析セッション | F-007 |
| `deep_research_messages` | 深掘り質問・回答履歴 | F-007 |
| `comparison_sessions` | 複数企業比較セッション | F-013 |
| `company_embeddings` | 企業ベクトル（補助検索用） | 将来 |

---

## companies

企業の正本マスタ。`company_id` で全テーブルから参照される。

```sql
CREATE TABLE companies (
    company_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 識別情報
    url               TEXT NOT NULL,                        -- 入力URL（正規化前）
    normalized_url    TEXT NOT NULL UNIQUE,                 -- 正規化済みURL（スキーム+ドメイン）
    domain            TEXT NOT NULL,                        -- ドメイン（例: toyota.co.jp）

    -- 企業基本情報（LLM抽出）
    name              TEXT,                                 -- 社名
    name_en           TEXT,                                 -- 英語社名
    industry          TEXT,                                 -- 業種
    country           TEXT DEFAULT 'JP',                    -- 国コード

    -- 収集メタデータ
    first_crawled_at  TIMESTAMPTZ,                          -- 初回クロール日時
    last_crawled_at   TIMESTAMPTZ,                          -- 最終クロール日時
    crawl_count       INTEGER NOT NULL DEFAULT 0,           -- 累計クロール回数
    total_pages_crawled INTEGER NOT NULL DEFAULT 0,         -- 累計取得ページ数

    -- ステータス
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,        -- 有効フラグ

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_companies_domain ON companies (domain);
CREATE INDEX idx_companies_normalized_url ON companies (normalized_url);
```

---

## analysis_results

1回の分析で生成された結果を保存する。企業ごとに複数持てる（履歴）。

```sql
CREATE TABLE analysis_results (
    result_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id        UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,
    run_id            UUID,                                 -- 生成元の analysis_runs.run_id（後から FK 設定）

    -- 分析コンテキスト
    template          TEXT NOT NULL DEFAULT 'general',     -- 使用テンプレート（general/job_hunting/investment/competitor/partnership）
    llm_model         TEXT NOT NULL,                       -- 使用モデル名（例: gpt-4.1-mini）
    llm_api_version   TEXT,                                -- API バージョン
    prompt_version    TEXT,                                 -- プロンプトバージョン（将来の管理用）

    -- 分析結果本体（JSONB）
    structured        JSONB NOT NULL,                      -- StructuredData（企業プロフィール・財務・ニュース・リスク等）
    summary           JSONB NOT NULL,                      -- SummaryData（概要・SWOT・競合・展望）
    scores            JSONB,                               -- ScoreData（財務健全性・成長性・競合優位性・リスク度・情報透明性）
    diff_report       TEXT,                                 -- 差分レポート（再分析時のみ）

    -- ソース情報
    sources           JSONB NOT NULL DEFAULT '[]',         -- SourceInfo[] （url, title, category）
    raw_sources       JSONB NOT NULL DEFAULT '[]',         -- RawSource[]（url, title, content, category）
    pages_used        INTEGER NOT NULL DEFAULT 0,          -- 分析に使用したページ数
    source_categories JSONB NOT NULL DEFAULT '{}',         -- カテゴリ別ページ数（例: {"IR": 3, "採用": 2}）

    -- レポート
    markdown_page     TEXT,                                 -- Markdown形式レポート全文

    -- シェア（F-012）
    share_id          TEXT UNIQUE,                         -- 公開共有ID（UUID先頭8文字）
    shared_at         TIMESTAMPTZ,                         -- シェア有効化日時

    -- 品質メタデータ
    extraction_tokens INTEGER,                             -- Stage1 使用トークン数
    summary_tokens    INTEGER,                             -- Stage2 使用トークン数
    total_tokens      INTEGER,                             -- 合計トークン数
    processing_ms     INTEGER,                             -- 処理時間（ミリ秒）

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analysis_results_company_id ON analysis_results (company_id);
CREATE INDEX idx_analysis_results_created_at ON analysis_results (company_id, created_at DESC);
CREATE INDEX idx_analysis_results_share_id ON analysis_results (share_id) WHERE share_id IS NOT NULL;
CREATE INDEX idx_analysis_results_template ON analysis_results (template);
```

---

## analysis_runs

分析の実行単位を管理する。ステータス追跡・エラー記録・再試行管理に使用する。

```sql
CREATE TABLE analysis_runs (
    run_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id        UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,
    result_id         UUID REFERENCES analysis_results (result_id) ON DELETE SET NULL,

    -- 実行種別
    run_type          TEXT NOT NULL,                       -- initial / refresh / deep_research
    template          TEXT NOT NULL DEFAULT 'general',

    -- ステータス管理
    status            TEXT NOT NULL DEFAULT 'pending',     -- pending / running / completed / failed / cancelled
    error_code        TEXT,                                 -- エラー種別コード（COLLECTION_ERROR / ANALYSIS_ERROR / TIMEOUT 等）
    error_message     TEXT,                                 -- エラー詳細メッセージ
    retry_count       INTEGER NOT NULL DEFAULT 0,          -- リトライ回数
    parent_run_id     UUID REFERENCES analysis_runs (run_id), -- リトライ元 run_id

    -- 実行メタデータ
    triggered_by      TEXT NOT NULL DEFAULT 'user',        -- user / system / scheduled
    force_refresh     BOOLEAN NOT NULL DEFAULT FALSE,       -- キャッシュ無視フラグ
    request_ip        TEXT,                                 -- リクエスト元IP（将来の認証対応用）
    user_agent        TEXT,                                 -- User-Agent

    -- タイミング
    started_at        TIMESTAMPTZ,
    completed_at      TIMESTAMPTZ,
    duration_ms       INTEGER,                             -- 完了時に計算して保存

    -- 収集サマリー
    pages_fetched     INTEGER,                             -- 取得ページ数
    pages_changed     INTEGER,                             -- 変更検知ページ数（refresh時）
    pages_skipped     INTEGER,                             -- スキップページ数（差分なし）

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analysis_runs_company_id ON analysis_runs (company_id, created_at DESC);
CREATE INDEX idx_analysis_runs_status ON analysis_runs (status) WHERE status IN ('pending', 'running');
CREATE INDEX idx_analysis_runs_run_type ON analysis_runs (run_type);
```

---

## page_snapshots

企業サイトの各ページの取得履歴を保持する。差分検知（F-006）に使用する。

```sql
CREATE TABLE page_snapshots (
    snapshot_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id        UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,

    -- ページ識別
    url               TEXT NOT NULL,
    normalized_url    TEXT NOT NULL,                       -- クエリパラメータ除去済みURL
    category          TEXT,                                -- ページカテゴリ（会社概要/IR・財務情報/プレスリリース/採用/その他）

    -- 変更検知
    content_hash      TEXT NOT NULL,                       -- SHA-256 of extracted text
    etag              TEXT,                                 -- HTTP ETag ヘッダー値
    last_modified     TEXT,                                 -- HTTP Last-Modified ヘッダー値
    content_length    INTEGER,                             -- レスポンスボディサイズ（bytes）

    -- ページメタデータ
    title             TEXT,
    description       TEXT,                                -- meta description
    og_title          TEXT,                                -- OGP title
    og_description    TEXT,                                -- OGP description
    canonical_url     TEXT,                                -- canonical URL
    lang              TEXT,                                -- html lang 属性
    status_code       INTEGER,                             -- HTTP ステータスコード
    content_type      TEXT,                                -- Content-Type

    -- 取得情報
    fetched_at        TIMESTAMPTZ NOT NULL,                -- 最終取得日時
    fetch_duration_ms INTEGER,                             -- 取得にかかった時間
    is_changed        BOOLEAN NOT NULL DEFAULT TRUE,       -- 前回から変更があったか
    previous_hash     TEXT,                                -- 前回の content_hash

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (company_id, normalized_url)
);

CREATE INDEX idx_page_snapshots_company_id ON page_snapshots (company_id);
CREATE INDEX idx_page_snapshots_category ON page_snapshots (company_id, category);
CREATE INDEX idx_page_snapshots_fetched_at ON page_snapshots (company_id, fetched_at DESC);
CREATE INDEX idx_page_snapshots_changed ON page_snapshots (company_id, is_changed) WHERE is_changed = TRUE;
```

---

## deep_research_sessions

深掘り分析（F-007）のセッション単位を管理する。

```sql
CREATE TABLE deep_research_sessions (
    session_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id        UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,
    result_id         UUID REFERENCES analysis_results (result_id) ON DELETE SET NULL,

    -- セッション状態
    status            TEXT NOT NULL DEFAULT 'active',      -- active / closed
    message_count     INTEGER NOT NULL DEFAULT 0,

    -- 使用リソース
    total_tokens      INTEGER NOT NULL DEFAULT 0,
    additional_pages_fetched INTEGER NOT NULL DEFAULT 0,   -- 追加収集したページ数

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deep_research_sessions_company_id ON deep_research_sessions (company_id);
```

---

## deep_research_messages

深掘り分析の質問・回答ペアを保存する。

```sql
CREATE TABLE deep_research_messages (
    message_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id        UUID NOT NULL REFERENCES deep_research_sessions (session_id) ON DELETE CASCADE,

    -- メッセージ内容
    role              TEXT NOT NULL,                       -- user / assistant
    content           TEXT NOT NULL,

    -- 回答メタデータ（role=assistant のみ）
    used_cached_data  BOOLEAN,                             -- 保存済みデータのみで回答したか
    additional_urls   JSONB DEFAULT '[]',                  -- 追加収集したURL一覧
    tokens_used       INTEGER,
    response_ms       INTEGER,

    sequence          INTEGER NOT NULL,                    -- セッション内の順序

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deep_research_messages_session_id ON deep_research_messages (session_id, sequence);
```

---

## comparison_sessions

複数企業比較（F-013）の結果を保存する。

```sql
CREATE TABLE comparison_sessions (
    comparison_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 比較対象（最大3社）
    company_ids       UUID[] NOT NULL,                     -- 比較対象の company_id 配列
    result_ids        UUID[] NOT NULL,                     -- 使用した analysis_result_id 配列

    -- 比較結果
    comparison_summary JSONB,                              -- AIによる比較コメント・サマリー
    template          TEXT NOT NULL DEFAULT 'general',

    -- シェア
    share_id          TEXT UNIQUE,
    shared_at         TIMESTAMPTZ,

    -- メタデータ
    llm_model         TEXT,
    tokens_used       INTEGER,
    processing_ms     INTEGER,

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comparison_sessions_company_ids ON comparison_sessions USING GIN (company_ids);
CREATE INDEX idx_comparison_sessions_share_id ON comparison_sessions (share_id) WHERE share_id IS NOT NULL;
```

---

## company_embeddings

pgvector による企業ベクトル（補助的な類似検索用途）。業務データの正本は上記リレーショナルテーブルで持つ。

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE company_embeddings (
    embedding_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id        UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,
    result_id         UUID REFERENCES analysis_results (result_id) ON DELETE SET NULL,

    -- ベクトル
    embedding         VECTOR(1536) NOT NULL,               -- text-embedding-3-small 次元数
    embedding_model   TEXT NOT NULL,                       -- 使用した embedding モデル名
    source_text       TEXT,                                 -- ベクトル化したテキスト（overview等）
    source_field      TEXT,                                 -- どのフィールドをベクトル化したか（overview/business_model等）

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_company_embeddings_company_id ON company_embeddings (company_id);
CREATE INDEX idx_company_embeddings_vector ON company_embeddings USING hnsw (embedding vector_cosine_ops);
```

---

## JSONB スキーマ定義

### structured（StructuredData）

```json
{
  "company_profile": {
    "name": "string",
    "founded": "string",
    "ceo": "string",
    "location": "string",
    "employees": "string",
    "capital": "string"
  },
  "business_domains": ["string"],
  "products": ["string"],
  "financials": {
    "revenue": "string",
    "operating_income": "string",
    "net_income": "string",
    "growth_rate": "string"
  },
  "news": [
    { "title": "string", "date": "string", "summary": "string" }
  ],
  "risks": [
    { "category": "string", "description": "string" }
  ]
}
```

### summary（SummaryData）

```json
{
  "overview": "string",
  "business_model": "string",
  "swot": {
    "strengths": ["string"],
    "weaknesses": ["string"],
    "opportunities": ["string"],
    "threats": ["string"]
  },
  "risks": ["string"],
  "competitors": ["string"],
  "outlook": "string"
}
```

### scores（ScoreData）

```json
{
  "financial_health":   { "score": 0, "reason": "string" },
  "growth_potential":   { "score": 0, "reason": "string" },
  "competitive_edge":   { "score": 0, "reason": "string" },
  "risk_level":         { "score": 0, "reason": "string" },
  "info_transparency":  { "score": 0, "reason": "string" }
}
```

---

## ER 図（概略）

```
companies
  ├── analysis_results  (company_id)
  │     └── company_embeddings (result_id)
  ├── analysis_runs     (company_id → result_id)
  ├── page_snapshots    (company_id)
  ├── deep_research_sessions (company_id → result_id)
  │     └── deep_research_messages (session_id)
  └── comparison_sessions (company_ids[])
```

---

## 設計方針まとめ

- PK は全テーブル UUID v4（`gen_random_uuid()`）
- タイムスタンプは全テーブルに `created_at` / `updated_at`（TIMESTAMPTZ）
- 業務データの正本はリレーショナルカラム。柔軟な構造のみ JSONB
- pgvector は `company_embeddings` に分離し、業務ロジックから切り離す
- `analysis_runs` でステータス・エラー・リトライを一元管理
- `page_snapshots` の `content_hash` で差分検知を実現（ETag/Last-Modified も併用）
- ダウンロード（F-009）は `markdown_page` を PDF/Word に変換して返すため専用テーブル不要
