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
  "company_name": "string"  // 必須。分析対象の企業名
}
```

バリデーション：
- `company_name`: 必須、1文字以上、空白のみは不可

### AnalysisResponse

```json
{
  "company_name": "string",
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
  "raw_sources": [{"url": "string", "title": "string", "content": "string"}]
}
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| company_name | string | 分析対象の企業名 |
| structured | StructuredData | 構造化抽出結果（企業プロフィール、事業領域、財務等） |
| summary | SummaryData | 要約・SWOT分析・競合推定・展望 |
| sources | SourceInfo[] | 参照した情報ソース（カテゴリ付き） |
| raw_sources | RawSource[] | 生テキストソース |

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
| 400 | バリデーションエラー（企業名が空など） |
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

## 機能一覧（MVP）

| # | 機能 | エンドポイント | 説明 |
|---|------|--------------|------|
| F-001 | 企業名入力 | — | フロントエンドのフォームUI。Valibot でバリデーション |
| F-002 | 企業分析実行 | POST /api/analysis | 企業名を受け取り、情報収集→AI分析→結果返却 |
| F-003 | 分析結果表示 | — | フロントエンドで AnalysisResponse を構造化表示 |
| F-004 | ヘルスチェック | GET /api/health | サーバー稼働確認 |

## 将来追加予定のエンドポイント（参考）

| メソッド | パス | 説明 | フェーズ |
|---------|------|------|---------|
| GET | `/api/analysis/history` | 分析履歴一覧 | Phase 2 |
| GET | `/api/analysis/{id}` | 分析結果詳細 | Phase 2 |
| GET | `/api/templates` | 分析テンプレート一覧 | Phase 3 |
| POST | `/api/analysis/compare` | 比較分析 | Phase 4 |
