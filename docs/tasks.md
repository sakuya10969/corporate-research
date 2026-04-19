# 未着手タスク一覧

参照ドキュメント:
- [specs.md](./specs.md) — 機能仕様
- [api-design.md](./api-design.md) — APIデザイン・スキーマ定義
- [domain-design.md](./domain-design.md) — ドメイン設計
- [architecture-philosophy.md](./architecture-philosophy.md) — アーキテクチャ思想
- [DESIGN.md](../DESIGN.md) — デザインシステム
- [.kiro/steering/structure.md](../.kiro/steering/structure.md) — ディレクトリ構成

実装順序: バックエンド → Orval 自動生成 → フロントエンド

---

## Phase 1: バックエンド基盤

### T-001: shared モジュールの作成

- 対象: `server/src/shared/`
- 内容:
  - `__init__.py` 作成
  - `config.py` — pydantic-settings による設定管理（Azure AI Foundry 接続情報、アプリ設定）
  - `llm.py` — LangChain + langchain-azure-ai による LLM クライアント初期化
  - `exceptions.py` — 共通例外クラス定義（CollectionError, AnalysisError 等）
- 参照: specs.md 横断的仕様「環境変数管理」「エラーハンドリング」、domain-design.md shared モジュール

### T-002: collector モジュールの作成

- 対象: `server/src/collector/`
- 内容:
  - `__init__.py` 作成
  - `service.py` — `collect_company_info(company_name: str) -> CompanyInfo` の実装
    - httpx で企業関連ページを非同期取得
    - BeautifulSoup + lxml で HTML パース・テキスト抽出
    - CompanyInfo エンティティとして構造化して返却
  - `parsers.py` — HTML パーサーユーティリティ（タイトル抽出、本文抽出等）
- 参照: domain-design.md CollectorService、specs.md F-002 処理フロー Step 3

### T-003: analysis モジュール — スキーマ定義

- 対象: `server/src/analysis/`
- 内容:
  - `__init__.py` 作成
  - `schemas.py` — Pydantic モデル定義
    - `AnalysisRequest`（company_name: str、必須、1文字以上、空白のみ不可）
    - `AnalysisResponse`（company_name, summary, business_description, key_findings, sources）
    - `SourceInfo`（url, title）
    - `HealthResponse`（status: str）
- 参照: api-design.md スキーマ定義、domain-design.md エンティティ

### T-004: analysis モジュール — プロンプト定義

- 対象: `server/src/analysis/prompts.py`
- 内容:
  - 企業情報の要約・分析用 LangChain プロンプトテンプレートを定義
  - 入力: 収集した企業情報テキスト
  - 出力: summary, business_description, key_findings の構造化データ
  - 出力パーサー（PydanticOutputParser 等）の設定
- 参照: specs.md F-002、domain-design.md AnalysisService

### T-005: analysis モジュール — サービス実装

- 対象: `server/src/analysis/service.py`
- 内容:
  - `analyze_company(request: AnalysisRequest) -> AnalysisResponse` の実装
  - 処理フロー:
    1. collector.service.collect_company_info() で情報収集
    2. shared.llm のクライアントを使用して LangChain チェーン実行
    3. prompts.py のテンプレートで要約・分析
    4. AnalysisResponse として構造化して返却
  - エラーハンドリング: 情報収集失敗、AI処理失敗時の例外処理
- 参照: specs.md F-002 処理フロー、domain-design.md AnalysisService

### T-006: analysis モジュール — ルーター実装

- 対象: `server/src/analysis/router.py`
- 内容:
  - `POST /api/analysis` — 企業分析実行エンドポイント
    - リクエスト: AnalysisRequest
    - レスポンス: AnalysisResponse
    - エラー: 400（バリデーション）、500（内部エラー）、503（外部サービス不可）
  - `GET /api/health` — ヘルスチェックエンドポイント
    - レスポンス: HealthResponse
- 参照: api-design.md エンドポイント一覧、specs.md F-002 / F-004

### T-007: FastAPI アプリケーション統合

- 対象: `server/main.py`
- 内容:
  - FastAPI アプリケーションインスタンスの作成
  - analysis_router の登録（prefix="/api"）
  - CORS 設定（フロントエンド localhost:3000 からのアクセス許可）
  - 共通例外ハンドラーの登録
- 参照: structure.md main.py 構成イメージ

---

## Phase 2: OpenAPI → Orval 自動生成

### T-008: Orval 設定ファイルの作成

- 対象: `client/orval.config.ts`
- 内容:
  - input: `http://localhost:8000/openapi.json`
  - output:
    - target: `./src/shared/api/generated/client.ts`
    - schemas: `./src/shared/api/generated/model`
    - client: `react-query`
    - httpClient: `axios`
  - mutator: `./src/shared/api/instance.ts` の customInstance を指定
- 参照: structure.md Orval 設定、api-design.md OpenAPI → Orval 自動生成フロー

### T-009: Axios インスタンスの作成

- 対象: `client/src/shared/api/instance.ts`
- 内容:
  - Axios インスタンスの作成（baseURL: バックエンドURL）
  - Orval の mutator として使用する customInstance 関数のエクスポート
- 参照: structure.md shared/api/instance.ts

### T-010: Orval による API クライアント・型の自動生成

- 前提: T-007（バックエンドサーバー起動可能）、T-008、T-009 が完了していること
- 内容:
  - バックエンドサーバーを起動（`http://localhost:8000`）
  - `client/` ディレクトリで `npx orval` を実行
  - `client/src/shared/api/generated/` に以下が生成されることを確認:
    - API クライアント関数
    - TypeScript 型定義（AnalysisRequest, AnalysisResponse, SourceInfo, HealthResponse）
    - TanStack React Query フック
  - `client/src/shared/api/index.ts` で生成物を re-export
- 参照: api-design.md OpenAPI → Orval 自動生成フロー

---

## Phase 3: フロントエンド基盤

デザインは DESIGN.md を遵守すること（白背景 + 青 #2563EB コンポーネント、角丸 8px 統一、影なし）。

### T-011: Mantine テーマ設定

- 対象: `client/src/app/layout.tsx`
- 内容:
  - MantineProvider にカスタムテーマを設定
    - primaryColor: `blue`（shade 6 を #2563EB 相当に）
    - defaultRadius: `md`（8px）
    - カラースキーム: `light` 固定
  - グローバル CSS の調整（背景白、フォント設定）
- デザイン準拠: DESIGN.md カラーパレット、Mantine テーマとの対応

### T-012: shared/config の作成

- 対象: `client/src/shared/config/env.ts`
- 内容:
  - バックエンド API の URL 等、環境変数の管理
- 参照: specs.md 横断的仕様「環境変数管理」

### T-013: React Query プロバイダーの設定

- 対象: `client/src/app/layout.tsx` または専用プロバイダーファイル
- 内容:
  - QueryClientProvider の設定
  - デフォルトオプション（staleTime、retry 等）の設定
- 参照: tech-stack.md TanStack React Query

---

## Phase 4: フロントエンド機能実装

デザインは DESIGN.md を遵守すること。

### T-014: 企業名入力フォーム（F-001）

- 対象: `client/src/features/company-search/`
- 内容:
  - `model/schema.ts` — Valibot バリデーションスキーマ（必須、1文字以上、空白のみ不可）
  - `ui/CompanySearchForm.tsx` — 企業名入力フォーム
    - Mantine TextInput + Button
    - Orval 生成の mutation フックで POST /api/analysis を呼び出し
    - 送信中はボタンをローディング状態にし、二重送信防止
    - バリデーションエラーはフィールド下に赤テキストで表示
  - `index.ts` — barrel export
- デザイン準拠: DESIGN.md 入力フィールド仕様、ボタン仕様、企業名入力画面レイアウト
- 参照: specs.md F-001

### T-015: 企業エンティティ表示コンポーネント（entities）

- 対象: `client/src/entities/company/`
- 内容:
  - `ui/CompanyCard.tsx` — 企業情報の表示カード
    - 白背景、Slate 200 ボーダー、角丸 8px、影なし
    - セクション見出し: SemiBold 18px
  - `model/types.ts` — 企業関連の手動型定義（Orval 生成型を補完する場合のみ）
  - `index.ts` — barrel export
- デザイン準拠: DESIGN.md カード仕様
- 参照: specs.md F-003

### T-016: 分析結果表示ウィジェット（F-003）

- 対象: `client/src/widgets/analysis-result/`
- 内容:
  - `ui/AnalysisResult.tsx` — 分析結果の構造化表示
    - 企業名をページタイトルとして表示（Bold 24px）
    - 企業概要（summary）をカード形式で表示
    - 事業内容（business_description）をセクションとして表示
    - 主要な発見事項（key_findings）をリスト形式で表示
    - 参照ソース（sources）をリンク付きリストで表示（リンク色は青 #2563EB）
    - ローディング中はスケルトンUI（Mantine Skeleton）
    - エラー時はエラーメッセージ表示（Error Light 背景 + 赤テキスト + 警告アイコン）
  - `index.ts` — barrel export
- デザイン準拠: DESIGN.md 分析結果画面レイアウト、カード仕様、スケルトンUI仕様、エラー表示仕様
- 参照: specs.md F-003

### T-017: トップページの組み立て

- 対象: `client/src/app/page.tsx`
- 内容:
  - ページ中央寄せレイアウト（最大幅 960px）
  - プロダクトのキャッチコピー表示
  - CompanySearchForm（features/company-search）の配置
  - AnalysisResult（widgets/analysis-result）の配置
  - 状態遷移: 初期状態 → 入力中 → 送信中（スケルトン） → 結果表示 / エラー
- デザイン準拠: DESIGN.md レイアウト方針、インタラクション状態遷移
- 参照: specs.md F-001 / F-003

---

## タスク依存関係

```
T-001 (shared)
  ↓
T-002 (collector) ← T-001
  ↓
T-003 (schemas)
  ↓
T-004 (prompts) ← T-001
  ↓
T-005 (service) ← T-001, T-002, T-003, T-004
  ↓
T-006 (router) ← T-003, T-005
  ↓
T-007 (main.py) ← T-006
  ↓
T-008 (orval config)
T-009 (axios instance)
  ↓
T-010 (orval generate) ← T-007, T-008, T-009
  ↓
T-011 (mantine theme)
T-012 (shared/config)
T-013 (query provider)
  ↓
T-014 (company search form) ← T-010, T-011, T-013
T-015 (company entity) ← T-011
  ↓
T-016 (analysis result widget) ← T-010, T-011, T-015
  ↓
T-017 (top page) ← T-014, T-016
```
