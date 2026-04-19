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

企業名（またはURL）を受け取り、Web情報収集 → 前処理・分類 → 構造化抽出 → 要約・SWOT生成 → 構造化結果返却を行うバックエンド処理。

### 仕様

- エンドポイント: `POST /api/analysis`
- リクエスト: `{ "company_name": "string" }`
- レスポンス: `AnalysisResponse`（company_name, structured, summary, sources, raw_sources）

### 処理フロー

```
1. analysis.router がリクエストを受付・Pydantic バリデーション
2. analysis.service.analyze_company() を呼び出し
3. collector.service.collect_company_info() で Web 情報収集
   a. URL正規化（企業名 → 公式サイトURL推定、URL入力はそのまま使用）
   b. サイトマップ探索（/sitemap.xml）→ 優先度付きURL選定
   c. サイトマップなしの場合: トップページから内部リンク探索（深さ1-2）
   d. 各ページを並行取得 → 構造保持テキスト抽出（表・リスト構造維持）
   e. ページカテゴリ分類（会社概要/事業内容/IR/ニュース等）
   f. Google検索で補完収集
   g. 前処理（ボイラープレート除去、正規化、カテゴリ別グルーピング）
   h. CompanyInfo エンティティとして構造化
4. Stage 1: 構造化抽出（EXTRACTION_PROMPT）
   - 分類済みコンテキストを LLM に投入
   - 企業プロフィール、事業領域、製品、財務、ニュース、リスクを抽出
   - StructuredData として構造化
5. Stage 2: 要約・分析生成（SUMMARY_PROMPT）
   - StructuredData を LLM に投入
   - 企業概要サマリー、事業モデル、SWOT、競合推定、展望を生成
   - SummaryData として構造化
6. AnalysisResponse を生成してレスポンス返却
```

### 技術的詳細

- バックエンドモジュール: `analysis`（フロー制御・2段階パイプライン）、`collector`（情報収集・前処理）
- 共通ユーティリティ: `shared/http_client.py`（リトライ付きHTTPクライアント）、`shared/text.py`（テキスト前処理・LLMコンテキスト整形）
- LLM 接続: `shared/llm.py` で初期化した LangChain クライアントを使用
- プロンプト: `analysis/prompts.py` に EXTRACTION_PROMPT と SUMMARY_PROMPT の2テンプレートを定義
- エラーハンドリング:
  - 情報収集失敗 → 500 エラー（detail にメッセージ）
  - AI 処理失敗（構造化抽出/要約生成） → 500 エラー
  - Azure AI Foundry 接続不可 → 503 エラー

---

## F-003: 分析結果表示

### 概要

バックエンドから返却された AnalysisResponse をフロントエンドで構造化表示する。

### 仕様

- 企業名をヘッダーとして表示
- 企業概要サマリー（summary.overview）をカード形式で表示
- 企業プロフィール（structured.company_profile）を項目別に表示
- 事業モデル（summary.business_model）をセクションとして表示
- 事業領域（structured.business_domains）をバッジ形式で表示
- プロダクト・サービス（structured.products）をリスト形式で表示
- 財務情報（structured.financials）を項目別に表示
- SWOT分析（summary.swot）を強み/弱み/機会/脅威に分けて表示
- リスク要因（summary.risks）をリスト形式で表示
- 競合企業（summary.competitors）をバッジ形式で表示
- 今後の展望（summary.outlook）をテキスト表示
- ニュース（structured.news）を日付付きリスト形式で表示
- 参照ソース（sources）をカテゴリバッジ付きリンクリストで表示
- ローディング中はスケルトンUIを表示
- エラー時はエラーメッセージを表示
- 各セクションはデータが存在する場合のみ表示（空データは非表示）

### 技術的詳細

- FSD 配置: `widgets/analysis-result/`
- UI: Mantine の Card, Text, List, Anchor, Skeleton, Badge, Group, Stack, Alert 等を使用
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
