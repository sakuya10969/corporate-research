# 完了タスク履歴

## Phase 1: バックエンド基盤

### T-001: shared モジュールの作成 ✅
- 完了日: 2026-04-19
- 対象: `server/src/shared/`
- 実装内容:
  - `config.py` — pydantic-settings による Settings クラス（azure_ai_project_endpoint, llm_model_name, cors_origins）
  - `llm.py` — LangChain init_chat_model で Azure AI モデル初期化
  - `exceptions.py` — CollectionError, AnalysisError, ExternalServiceError 定義

### T-002: collector モジュールの作成 ✅
- 完了日: 2026-04-19
- 対象: `server/src/collector/`
- 実装内容:
  - `service.py` — Google 検索→ページ取得→テキスト抽出の非同期情報収集フロー
  - `parsers.py` — BeautifulSoup + lxml による HTML タイトル・本文抽出

### T-003: analysis モジュール — スキーマ定義 ✅
- 完了日: 2026-04-19
- 対象: `server/src/analysis/schemas.py`
- 実装内容:
  - AnalysisRequest（company_name: 必須、1文字以上、空白のみ不可）
  - AnalysisResponse（company_name, summary, business_description, key_findings, sources）
  - SourceInfo（url, title）
  - HealthResponse（status: "ok"）

### T-004: analysis モジュール — プロンプト定義 ✅
- 完了日: 2026-04-19
- 対象: `server/src/analysis/prompts.py`
- 実装内容:
  - ChatPromptTemplate で企業分析用プロンプト定義（JSON 出力指定）

### T-005: analysis モジュール — サービス実装 ✅
- 完了日: 2026-04-19
- 対象: `server/src/analysis/service.py`
- 実装内容:
  - analyze_company: 情報収集→LangChain チェーン実行→JSON パース→AnalysisResponse 構築
  - エラーハンドリング: CollectionError, ExternalServiceError, AnalysisError

### T-006: analysis モジュール — ルーター実装 ✅
- 完了日: 2026-04-19
- 対象: `server/src/analysis/router.py`
- 実装内容:
  - POST /api/analysis — 企業分析エンドポイント
  - GET /api/health — ヘルスチェックエンドポイント

### T-007: FastAPI アプリケーション統合 ✅
- 完了日: 2026-04-19
- 対象: `server/main.py`
- 実装内容:
  - FastAPI アプリ作成、analysis_router 登録（prefix="/api"）
  - CORS 設定（localhost:3000 許可）
  - 共通例外ハンドラー登録（CollectionError→500, AnalysisError→500, ExternalServiceError→503）

---

## Phase 2: OpenAPI → Orval 自動生成

### T-008: Orval 設定ファイルの作成 ✅
- 完了日: 2026-04-19
- 対象: `client/orval.config.ts`
- 実装内容:
  - input: `../server/openapi.json`（ローカルファイル参照）
  - output: react-query クライアント、tags-split モード
  - mutator: customInstance 指定

### T-009: Axios インスタンスの作成 ✅
- 完了日: 2026-04-19
- 対象: `client/src/shared/api/instance.ts`
- 実装内容:
  - Axios インスタンス（baseURL: NEXT_PUBLIC_API_URL or localhost:8000）
  - customInstance 関数（Orval mutator 用）

### T-010: Orval による API クライアント・型の自動生成 ✅
- 完了日: 2026-04-19
- 対象: `client/src/shared/api/generated/`
- 実装内容:
  - `server/scripts/export_openapi.py` で OpenAPI JSON をファイル出力
  - `npx orval` で API クライアント・型・React Query フック自動生成
  - 生成物: usePostAnalysisApiAnalysisPost (mutation), useGetHealthApiHealthGet (query)
  - 型: AnalysisRequest, AnalysisResponse, SourceInfo, HealthResponse
  - `shared/api/index.ts` で re-export

---

## Phase 3: フロントエンド基盤

### T-011: Mantine テーマ設定 ✅
- 完了日: 2026-04-19
- 対象: `client/src/app/layout.tsx`
- 実装内容:
  - primaryColor: blue（shade 6 = #2563EB）
  - defaultRadius: md（8px）
  - forceColorScheme: light
  - メタデータ: 日本語タイトル・説明

### T-012: shared/config の作成 ✅
- 完了日: 2026-04-19
- 対象: `client/src/shared/config/env.ts`
- 実装内容:
  - env.apiUrl（NEXT_PUBLIC_API_URL or localhost:8000）

### T-013: React Query プロバイダーの設定 ✅
- 完了日: 2026-04-19
- 対象: `client/src/app/query-provider.tsx`
- 実装内容:
  - QueryClientProvider（staleTime: 60s, retry: 1）
  - "use client" ディレクティブ

---

## Phase 4: フロントエンド機能実装

### T-014: 企業名入力フォーム ✅
- 完了日: 2026-04-19
- 対象: `client/src/features/company-search/`
- 実装内容:
  - `model/schema.ts` — Valibot バリデーション（必須、空白のみ不可）
  - `ui/CompanySearchForm.tsx` — TextInput + Button、ローディング状態、バリデーションエラー表示
  - `index.ts` — barrel export

### T-015: 企業エンティティ表示コンポーネント ✅
- 完了日: 2026-04-19
- 対象: `client/src/entities/company/`
- 実装内容:
  - `ui/CompanyCard.tsx` — 白背景、Slate 200 ボーダー、角丸 8px、影なし、SemiBold 18px タイトル
  - `index.ts` — barrel export

### T-016: 分析結果表示ウィジェット ✅
- 完了日: 2026-04-19
- 対象: `client/src/widgets/analysis-result/`
- 実装内容:
  - `ui/AnalysisResult.tsx` — スケルトン UI、エラー表示（Error Light 背景 + 警告アイコン）、結果表示
  - 企業名 Bold 24px、summary/business_description/key_findings/sources を CompanyCard で表示
  - sources はリンク付きリスト（#2563EB）
  - `index.ts` — barrel export

### T-017: トップページの組み立て ✅
- 完了日: 2026-04-19
- 対象: `client/src/app/page.tsx`
- 実装内容:
  - Container（max 960px）中央寄せ
  - キャッチコピー表示
  - CompanySearchForm + AnalysisResult 配置
  - usePostAnalysisApiAnalysisPost mutation で状態管理（初期→送信中→結果/エラー）

---

## ビルド検証
- 完了日: 2026-04-19
- Next.js ビルド成功（TypeScript エラーなし、静的ページ生成正常）
