# 機能仕様一覧

## F-001: 企業名入力

### 概要

ユーザーが分析対象の企業名を入力するフォームUI。

### 仕様

- テキスト入力フィールド + 送信ボタンで構成
- Valibot スキーマによるクライアントサイドバリデーション
  - 必須入力
  - 1文字以上
  - 空白のみは不可
- 送信時に POST `/api/analysis` を呼び出す（Orval 生成の mutation フックを使用）
- 送信中はローディング状態を表示し、二重送信を防止する

### 技術的詳細

- FSD 配置: `features/company-search/`
- バリデーション: `features/company-search/model/schema.ts`（Valibot）
- UI: `features/company-search/ui/CompanySearchForm.tsx`（Mantine TextInput + Button）
- API 呼び出し: Orval 生成の `useAnalyzeCompany` mutation フック

---

## F-002: 企業分析実行

### 概要

企業名を受け取り、Web情報収集 → AI要約・分析 → 構造化結果返却を行うバックエンド処理。

### 仕様

- エンドポイント: `POST /api/analysis`
- リクエスト: `{ "company_name": "string" }`
- レスポンス: `AnalysisResponse`（company_name, summary, business_description, key_findings, sources）

### 処理フロー

```
1. analysis.router がリクエストを受付・Pydantic バリデーション
2. analysis.service.analyze_company() を呼び出し
3. collector.service.collect_company_info() で Web 情報収集
   - httpx で対象ページを取得
   - BeautifulSoup + lxml で HTML パース・テキスト抽出
   - CompanyInfo エンティティとして構造化
4. 収集情報を LangChain チェーンに渡す
   - プロンプトテンプレート（prompts.py）を使用
   - langchain-azure-ai 経由で Azure AI Foundry のモデルを呼び出し
   - 出力パーサーで構造化
5. AnalysisResult を生成してレスポンス返却
```

### 技術的詳細

- バックエンドモジュール: `analysis`（フロー制御）、`collector`（情報収集）
- LLM 接続: `shared/llm.py` で初期化した LangChain クライアントを使用
- プロンプト: `analysis/prompts.py` にテンプレートを定義
- エラーハンドリング:
  - 情報収集失敗 → 500 エラー（detail にメッセージ）
  - AI 処理失敗 → 500 エラー
  - Azure AI Foundry 接続不可 → 503 エラー

---

## F-003: 分析結果表示

### 概要

バックエンドから返却された AnalysisResponse をフロントエンドで構造化表示する。

### 仕様

- 企業名をヘッダーとして表示
- 企業概要（summary）をカード形式で表示
- 事業内容（business_description）をセクションとして表示
- 主要な発見事項（key_findings）をリスト形式で表示
- 参照ソース（sources）をリンク付きリストで表示
- ローディング中はスケルトンUIを表示
- エラー時はエラーメッセージを表示

### 技術的詳細

- FSD 配置: `widgets/analysis-result/`
- UI: Mantine の Card, Text, List, Anchor, Skeleton 等を使用
- 状態管理: React Query の query 状態（isLoading, isError, data）を利用
- エンティティ表示: `entities/company/ui/CompanyCard.tsx` を widgets 内で利用

---

## F-004: ヘルスチェック

### 概要

サーバーの稼働状態を確認するエンドポイント。

### 仕様

- エンドポイント: `GET /api/health`
- レスポンス: `{ "status": "ok" }`
- 認証不要

### 技術的詳細

- `analysis/router.py` または専用の `health` エンドポイントとして `main.py` に直接定義
- MVP ではシンプルに固定レスポンスを返す
- 将来的には Azure AI Foundry への接続確認等を追加可能

---

## 横断的仕様

### バリデーション戦略

| レイヤ | ツール | 目的 |
|--------|-------|------|
| フロントエンド | Valibot | UX向上（即時フィードバック） |
| バックエンド | Pydantic | 信頼境界（不正リクエスト防止） |

フロントエンドのバリデーションはUXのためであり、セキュリティ上の信頼境界はバックエンドの Pydantic バリデーションが担う。

### API クライアント自動生成

- Orval で OpenAPI スキーマから自動生成
- 生成先: `client/src/shared/api/generated/`
- 生成物: API クライアント関数、TypeScript 型定義、React Query フック
- 手動編集禁止。バックエンドスキーマ変更時に `npx orval` で再生成

### エラーハンドリング

- バックエンド: `shared/exceptions.py` に共通例外を定義。FastAPI の exception handler で HTTP レスポンスに変換
- フロントエンド: React Query の `isError` / `error` を利用してUIにエラー表示

### 環境変数管理

- バックエンド: `pydantic-settings` で `.env` から型安全に読み込み（`shared/config.py`）
- フロントエンド: `shared/config/env.ts` で Next.js の環境変数を管理
- Azure AI Foundry の接続情報（エンドポイント、キー等）はバックエンドの `.env` で管理
