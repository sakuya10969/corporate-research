# データベース設計

使用DB: PostgreSQL 17  
ORM: SQLAlchemy (async) + Alembic

この設計は、企業分析SaaSを初期から拡張前提で運用するための現行案である。  
業務データの正本は PostgreSQL に置き、ベクトル検索はまだ正本設計に含めない。

---

## 設計方針

1. `companies` は企業の正本IDを管理する
2. `pages` / `page_versions` はスクレイピング資産を再利用するための保存層にする
3. `analysis_runs` は実行履歴、`analysis_results` は成果物として分離する
4. 分析結果がどのページ版を根拠にしたかは `analysis_result_sources` で追跡する
5. `clerk_user_id` は全テーブルに複製せず、`users` に閉じ込める
6. ユーザー起点の区別は `requested_by_user_id` / `created_by_user_id` を上位テーブルに持たせる
7. `pgvector` は現時点では未採用。必要になったら `page_versions` 単位で追加する

---

## テーブル一覧

| テーブル名 | 概要 |
|-----------|------|
| `users` | Clerk 連携ユーザー |
| `companies` | 企業の正本 |
| `analysis_runs` | 分析実行履歴 |
| `analysis_results` | 分析成果物 |
| `analysis_result_sources` | 分析結果と根拠ページ版の関連 |
| `pages` | URL単位の論理ページ |
| `page_versions` | 取得時点ごとの本文・メタ情報 |
| `deep_research_sessions` | 深掘り分析セッション |
| `deep_research_messages` | 深掘り分析メッセージ |
| `comparison_sessions` | 複数企業比較セッション |
| `comparison_session_items` | 比較対象企業の中間テーブル |

---

## users

認証ユーザーを内部IDで管理する。`clerk_user_id` を外部認証識別子として保持する。

```sql
CREATE TABLE users (
    user_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_user_id     TEXT NOT NULL UNIQUE,
    email             TEXT NOT NULL UNIQUE,
    display_name      TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## companies

企業の正本。分析で変わりやすい項目は極力ここに寄せず、企業識別と安定属性に絞る。

```sql
CREATE TABLE companies (
    company_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    primary_url       TEXT NOT NULL,
    normalized_url    TEXT NOT NULL UNIQUE,
    primary_domain    TEXT NOT NULL,

    display_name      TEXT,
    legal_name        TEXT,
    country_code      TEXT NOT NULL DEFAULT 'JP',
    status            TEXT NOT NULL DEFAULT 'active',
    extra_data        JSONB NOT NULL DEFAULT '{}',

    first_analyzed_at TIMESTAMPTZ,
    last_analyzed_at  TIMESTAMPTZ,
    analysis_count    INTEGER NOT NULL DEFAULT 0,
    last_page_crawl_at TIMESTAMPTZ,

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_companies_primary_domain ON companies (primary_domain);
```

---

## analysis_runs

分析の実行単位。入力条件、実行状態、収集サマリーを保持する。

```sql
CREATE TABLE analysis_runs (
    run_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,
    requested_by_user_id UUID REFERENCES users (user_id) ON DELETE SET NULL,

    run_type            TEXT NOT NULL,
    template            TEXT NOT NULL DEFAULT 'general',
    status              TEXT NOT NULL DEFAULT 'pending',

    force_refresh       BOOLEAN NOT NULL DEFAULT FALSE,
    input_params        JSONB NOT NULL DEFAULT '{}',
    collection_summary  JSONB NOT NULL DEFAULT '{}',

    error_code          TEXT,
    error_message       TEXT,
    retry_count         INTEGER NOT NULL DEFAULT 0,
    parent_run_id       UUID REFERENCES analysis_runs (run_id) ON DELETE SET NULL,

    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    duration_ms         INTEGER,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analysis_runs_company_id ON analysis_runs (company_id, created_at DESC);
CREATE INDEX idx_analysis_runs_requested_by_user_id ON analysis_runs (requested_by_user_id);
CREATE INDEX idx_analysis_runs_status ON analysis_runs (status);
```

---

## analysis_results

1回の分析で生成された成果物。`analysis_runs` と 1:1 に近い形で紐づける。

```sql
CREATE TABLE analysis_results (
    result_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id         UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,
    run_id             UUID UNIQUE REFERENCES analysis_runs (run_id) ON DELETE SET NULL,

    template           TEXT NOT NULL DEFAULT 'general',
    llm_model          TEXT NOT NULL,
    llm_api_version    TEXT,
    prompt_version     TEXT,

    structured         JSONB NOT NULL,
    summary            JSONB NOT NULL,
    scores             JSONB,
    diff_report        TEXT,

    sources            JSONB NOT NULL DEFAULT '[]',
    raw_sources        JSONB NOT NULL DEFAULT '[]',
    markdown_page      TEXT,
    pages_used         INTEGER NOT NULL DEFAULT 0,
    quality_metrics    JSONB NOT NULL DEFAULT '{}',

    share_id           TEXT UNIQUE,
    shared_at          TIMESTAMPTZ,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analysis_results_company_id ON analysis_results (company_id, created_at DESC);
CREATE INDEX idx_analysis_results_run_id ON analysis_results (run_id);
CREATE INDEX idx_analysis_results_share_id ON analysis_results (share_id) WHERE share_id IS NOT NULL;
```

`sources` と `raw_sources` は現行API互換のため残している。  
正規な根拠追跡は `analysis_result_sources` を使う。

---

## analysis_result_sources

分析結果がどの保存済みページ版を根拠にしたかを保持する。

```sql
CREATE TABLE analysis_result_sources (
    analysis_result_source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id          UUID NOT NULL REFERENCES analysis_results (result_id) ON DELETE CASCADE,
    page_version_id    UUID NOT NULL REFERENCES page_versions (page_version_id) ON DELETE CASCADE,
    source_order       INTEGER NOT NULL DEFAULT 0,
    page_category      TEXT,
    citation_title     TEXT,
    snippet            TEXT,
    citation_metadata  JSONB NOT NULL DEFAULT '{}',
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_analysis_result_sources_result_id ON analysis_result_sources (result_id, source_order);
CREATE INDEX idx_analysis_result_sources_page_version_id ON analysis_result_sources (page_version_id);
```

---

## pages

会社配下の論理ページ。URL単位の現在状態を持つ。

```sql
CREATE TABLE pages (
    page_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id         UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,

    url                TEXT NOT NULL,
    normalized_url     TEXT NOT NULL,
    page_type          TEXT,
    title              TEXT,
    is_active          BOOLEAN NOT NULL DEFAULT TRUE,

    first_seen_at      TIMESTAMPTZ,
    last_seen_at       TIMESTAMPTZ,
    last_changed_at    TIMESTAMPTZ,
    latest_content_hash TEXT,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (company_id, normalized_url)
);

CREATE INDEX idx_pages_company_id ON pages (company_id);
CREATE INDEX idx_pages_page_type ON pages (company_id, page_type);
```

---

## page_versions

ページ取得時点ごとの本文とメタ情報を保持する。差分更新と再利用の核。

```sql
CREATE TABLE page_versions (
    page_version_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id            UUID NOT NULL REFERENCES pages (page_id) ON DELETE CASCADE,
    fetch_run_id       UUID REFERENCES analysis_runs (run_id) ON DELETE SET NULL,

    content_hash       TEXT NOT NULL,
    title              TEXT,
    meta_description   TEXT,
    content_type       TEXT,
    lang               TEXT,
    etag               TEXT,
    last_modified      TEXT,
    content_length     INTEGER,

    raw_html           TEXT,
    extracted_text     TEXT NOT NULL,
    page_metadata      JSONB NOT NULL DEFAULT '{}',

    fetched_at         TIMESTAMPTZ NOT NULL,
    fetch_duration_ms  INTEGER,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_page_versions_page_id ON page_versions (page_id, fetched_at DESC);
CREATE INDEX idx_page_versions_fetch_run_id ON page_versions (fetch_run_id);
CREATE INDEX idx_page_versions_content_hash ON page_versions (content_hash);
```

---

## deep_research_sessions

深掘り分析の会話単位。基底となる分析結果を保持する。

```sql
CREATE TABLE deep_research_sessions (
    session_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,
    base_result_id      UUID REFERENCES analysis_results (result_id) ON DELETE SET NULL,
    created_by_user_id  UUID REFERENCES users (user_id) ON DELETE SET NULL,

    status              TEXT NOT NULL DEFAULT 'active',
    message_count       INTEGER NOT NULL DEFAULT 0,
    total_input_tokens  INTEGER NOT NULL DEFAULT 0,
    total_output_tokens INTEGER NOT NULL DEFAULT 0,
    retrieval_summary   JSONB NOT NULL DEFAULT '{}',

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deep_research_sessions_company_id ON deep_research_sessions (company_id);
CREATE INDEX idx_deep_research_sessions_created_by_user_id ON deep_research_sessions (created_by_user_id);
```

---

## deep_research_messages

深掘り質問と回答の履歴。回答根拠や検索コンテキストを持てるようにする。

```sql
CREATE TABLE deep_research_messages (
    message_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id         UUID NOT NULL REFERENCES deep_research_sessions (session_id) ON DELETE CASCADE,

    sequence           INTEGER NOT NULL,
    role               TEXT NOT NULL,
    content            TEXT NOT NULL,
    model_name         TEXT,
    citations          JSONB NOT NULL DEFAULT '[]',
    retrieval_context  JSONB NOT NULL DEFAULT '{}',
    additional_urls    JSONB NOT NULL DEFAULT '[]',
    input_tokens       INTEGER,
    output_tokens      INTEGER,
    response_ms        INTEGER,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deep_research_messages_session_id ON deep_research_messages (session_id, sequence);
```

---

## comparison_sessions

複数企業比較のセッション本体。

```sql
CREATE TABLE comparison_sessions (
    comparison_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by_user_id UUID REFERENCES users (user_id) ON DELETE SET NULL,

    template           TEXT NOT NULL DEFAULT 'general',
    comparison_summary JSONB NOT NULL DEFAULT '{}',
    llm_model          TEXT,
    processing_ms      INTEGER,

    share_id           TEXT UNIQUE,
    shared_at          TIMESTAMPTZ,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comparison_sessions_created_by_user_id ON comparison_sessions (created_by_user_id);
CREATE INDEX idx_comparison_sessions_share_id ON comparison_sessions (share_id) WHERE share_id IS NOT NULL;
```

---

## comparison_session_items

比較対象企業を中間テーブルで持つ。配列カラムではなく、参照整合性を優先する。

```sql
CREATE TABLE comparison_session_items (
    comparison_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comparison_id      UUID NOT NULL REFERENCES comparison_sessions (comparison_id) ON DELETE CASCADE,
    company_id         UUID NOT NULL REFERENCES companies (company_id) ON DELETE CASCADE,
    result_id          UUID REFERENCES analysis_results (result_id) ON DELETE SET NULL,
    sort_order         INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_comparison_session_items_comparison_id ON comparison_session_items (comparison_id, sort_order);
CREATE INDEX idx_comparison_session_items_company_id ON comparison_session_items (company_id);
```

---

## ベクトル検索の扱い

現時点では `pgvector` テーブルは導入しない。

理由:

1. 今の主目的は企業ごとの分析履歴とスクレイピング資産の再利用である
2. まずは `pages / page_versions` の保存だけで再分析効率が大きく上がる
3. ベクトル検索を入れるなら、正本とは分離した副次データとして足すべきである

将来追加する場合の起点:

- `page_versions.extracted_text` をチャンク化する
- `page_version_id` 単位で embedding を持つ
- 深掘り分析や横断検索でのみ使う

つまり、正本は通常の PostgreSQL、意味検索が必要になったら `pgvector` を後付けする。
