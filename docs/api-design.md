# APIデザイン

## 基本方針

- RESTful API として設計する
- FastAPI の自動 OpenAPI スキーマ生成を活用し、フロントエンドとの型安全な連携を実現する
- エンドポイントのプレフィックスは `/api` とする
- リクエスト / レスポンスは Pydantic モデルで定義し、バリデーションとドキュメント生成を自動化する

## エンドポイント一覧（MVP）

### 企業分析

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---------|------|------|-----------|-----------|
| POST | `/api/analysis` | 企業分析を実行する | AnalysisRequest | AnalysisResponse |
| GET | `/api/health` | ヘルスチェック | — | HealthResponse |

## スキーマ定義

### AnalysisRequest

```json
{
  "company_url": "string"  // 必須。分析対象の企業URL（例: https://www.toyota.co.jp/）
}
```

バリデーション：
- `company_url`: 必須、`http://` または `https://` で始まるURL

### AnalysisResponse

```json
{
  "company_url": "string",
  "structured": {
    "company_profile": {
      "name": "", "founded": "", "ceo": "", "location": "", "employees": "", "capital": ""
    },
    "business_domains": ["string"],
    "products": ["string"],
    "financials": {
      "revenue": "", "operating_income": "", "net_income": "", "growth_rate": ""
    },
    "news": [{"title": "string", "date": "string", "summary": "string"}],
    "risks": [{"category": "string", "description": "string"}]
  },
  "summary": {
    "overview": "string",
    "business_model": "string",
    "swot": {
      "strengths": ["string"], "weaknesses": ["string"],
      "opportunities": ["string"], "threats": ["string"]
    },
    "risks": ["string"],
    "competitors": ["string"],
    "outlook": "string"
  },
  "sources": [{"url": "string", "title": "string", "category": "string"}],
  "raw_sources": [{"url": "string", "title": "string", "content": "string", "category": "string"}],
  "markdown_page": "string",
  "diff_report": "string"
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| company_url | string | 分析対象の企業URL |
| structured | StructuredData | 構造化抽出結果（企業プロフィール、事業領域、財務等） |
| summary | SummaryData | 要約・SWOT分析・競合推定・展望 |
| sources | SourceInfo[] | 参照した情報ソース（カテゴリ付き） |
| raw_sources | RawSource[] | 生テキストソース（カテゴリ付き） |
| markdown_page | string | 人間向けMarkdownレポート |
| diff_report | string | 差分検知レポート（過去データがある場合） |

### SourceInfo

```json
{
  "url": "string",
  "title": "string",
  "category": "string"
}
```

### HealthResponse

```json
{
  "status": "ok"
}
```

## エラーレスポンス

共通のエラーレスポンス形式を定義する。

```json
{
  "detail": "string"  // エラーメッセージ
}
```

| ステータスコード | 用途 |
|----------------|------|
| 400 | バリデーションエラー（URLが無効など） |
| 404 | 企業情報が見つからない場合 |
| 500 | 内部エラー（情報収集失敗、AI処理失敗など） |
| 503 | 外部サービス（Azure AI Foundry）が利用不可 |

## OpenAPI → Orval 自動生成フロー

```
1. FastAPI が Pydantic モデルから OpenAPI スキーマを自動生成
   GET http://localhost:8000/openapi.json

2. Orval が OpenAPI スキーマを読み取り、以下を生成：
   - API クライアント関数（Axios ベース）
   - リクエスト / レスポンスの TypeScript 型定義
   - TanStack React Query 用カスタムフック

3. 生成先: client/src/shared/api/generated/

4. 生成コマンド:
   cd client && npx orval
```

生成コードは手動編集しない。バックエンドのスキーマ変更時に再生成する。

## バリデーション戦略

| レイヤ | ツール | 目的 |
|--------|-------|------|
| フロントエンド | Valibot | UX向上（即時フィードバック） |
| バックエンド | Pydantic | 信頼境界（不正リクエスト防止） |

フロントエンドのバリデーションはUXのためであり、セキュリティ上の信頼境界はバックエンドの Pydantic バリデーションが担う。

## エラーハンドリング

- バックエンド: `shared/exceptions.py` に共通例外を定義。FastAPI の exception handler で HTTP レスポンスに変換
- フロントエンド: React Query の `isError` / `error` を利用してUIにエラー表示

## 環境変数管理

- バックエンド: `pydantic-settings` で `.env` から型安全に読み込み（`shared/config.py`）
- フロントエンド: `shared/config/env.ts` で Next.js の環境変数を管理
- Azure AI Foundry の接続情報（エンドポイント、キー等）はバックエンドの `.env` で管理

## 機能一覧（MVP）

| # | 機能 | エンドポイント | 説明 |
|---|------|--------------|------|
| F-001 | 企業URL入力 | — | フロントエンドのフォームUI。Valibot でURL バリデーション |
| F-002 | 企業分析実行 | POST /api/analysis | 企業URLを受け取り、サイト情報収集→AI分析→結果返却 |
| F-003 | 分析結果表示 | — | フロントエンドで AnalysisResponse を構造化表示 |
| F-004 | ヘルスチェック | GET /api/health | サーバー稼働確認 |

## 将来追加予定のエンドポイント（参考）

| メソッド | パス | 説明 | フェーズ |
|---------|------|------|---------|
| GET | `/api/analysis/history` | 分析履歴一覧 | Phase 2 |
| GET | `/api/analysis/{id}` | 分析結果詳細 | Phase 2 |
| GET | `/api/templates` | 分析テンプレート一覧 | Phase 3 |
| POST | `/api/analysis/compare` | 比較分析 | Phase 4 |


---

## エンドポイント一覧（V2追加分）

### 企業名検索（F-011）

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---------|------|------|-----------|-----------|
| GET | `/api/search/company` | 企業名からURL候補を検索する | `?q={企業名}` | CompanySearchResponse |

### 分析結果シェア（F-012）

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---------|------|------|-----------|-----------|
| GET | `/api/share/{share_id}` | 共有IDで分析結果を取得する | — | AnalysisResponse |

### 複数企業比較（F-013）

| メソッド | パス | 説明 | リクエスト | レスポンス |
|---------|------|------|-----------|-----------|
| POST | `/api/analysis/compare` | 複数企業を並行分析・比較する | CompareRequest | CompareResponse |

---

## スキーマ定義（V2追加分）

### AnalysisRequest（V2拡張）

```json
{
  "company_url": "string",
  "template": "general | job_hunting | investment | competitor | partnership"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| company_url | string | ✅ | 分析対象の企業URL |
| template | string | — | 分析テンプレートID。省略時は `general` |

### ScoreData（F-014: スコアリング）

```json
{
  "financial_health": {"score": 0, "reason": "string"},
  "growth_potential": {"score": 0, "reason": "string"},
  "competitive_advantage": {"score": 0, "reason": "string"},
  "risk_level": {"score": 0, "reason": "string"},
  "information_transparency": {"score": 0, "reason": "string"}
}
```

各スコアは 0〜100 の整数。`reason` はスコアの根拠となる1〜2文の説明。

### AnalysisResponse（V2拡張）

既存フィールドに以下を追加：

```json
{
  "...既存フィールド...",
  "scores": {
    "financial_health": {"score": 75, "reason": "string"},
    "growth_potential": {"score": 80, "reason": "string"},
    "competitive_advantage": {"score": 70, "reason": "string"},
    "risk_level": {"score": 40, "reason": "string"},
    "information_transparency": {"score": 85, "reason": "string"}
  },
  "template": "general"
}
```

### CompanySearchResponse（F-011）

```json
{
  "query": "string",
  "results": [
    {
      "name": "string",
      "url": "string",
      "description": "string"
    }
  ]
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| query | string | 検索クエリ（企業名） |
| results | CompanyCandidate[] | 候補企業リスト（最大5件） |

### CompanyCandidate

```json
{
  "name": "string",
  "url": "string",
  "description": "string"
}
```

### CompareRequest（F-013）

```json
{
  "company_urls": ["string", "string"],
  "template": "general | job_hunting | investment | competitor | partnership"
}
```

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| company_urls | string[] | ✅ | 比較対象の企業URL（2〜3件） |
| template | string | — | 分析テンプレートID。省略時は `general` |

バリデーション：
- `company_urls`: 2件以上3件以下

### CompareResponse（F-013）

```json
{
  "companies": [
    {
      "company_url": "string",
      "structured": {},
      "summary": {},
      "scores": {}
    }
  ],
  "comparison_summary": "string",
  "template": "string"
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| companies | AnalysisResponse[] | 各企業の分析結果 |
| comparison_summary | string | AIによる比較コメント（自然文） |
| template | string | 使用したテンプレートID |

---

## エンドポイント一覧（V2完全版）

| # | 機能 | メソッド | パス | フェーズ |
|---|------|---------|------|---------|
| F-001〜004 | MVP機能 | — | — | MVP ✅ |
| F-005 | 企業データ永続化 | — | — | V1 |
| F-006 | 差分更新分析 | POST | `/api/analysis/refresh` | V1 |
| F-007 | 深掘り分析 | POST | `/api/analysis/{id}/deep` | V1 |
| F-008 | 分析履歴管理 | GET | `/api/analysis/history` | V1 |
| F-009 | ダウンロード | GET | `/api/analysis/{id}/download` | V1 |
| F-010 | 分析テンプレート | — | リクエストパラメータ拡張 | V2 |
| F-011 | 企業名検索 | GET | `/api/search/company` | V2 |
| F-012 | 分析結果シェア | GET | `/api/share/{share_id}` | V2 |
| F-013 | 複数企業比較 | POST | `/api/analysis/compare` | V2 |
| F-014 | 分析スコアリング | — | レスポンス拡張 | V2 |

---

## OGP対応（F-012: シェア機能）

共有ページ（`/share/{share_id}`）では以下のOGPメタタグを設定する：

```html
<meta property="og:title" content="{企業名} の企業分析レポート" />
<meta property="og:description" content="{overview の先頭150文字}" />
<meta property="og:url" content="https://app.example.com/share/{share_id}" />
<meta property="og:type" content="article" />
```

Next.js App Router の `generateMetadata` を使用して動的に生成する。
