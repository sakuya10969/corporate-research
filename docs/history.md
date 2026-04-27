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

---

## LLM 基盤刷新（openai-agents 移行）

### LangChain → openai-agents 移行 ✅
- 完了日: 2026-04-27
- 対象: `server/src/shared/llm.py`, `server/src/shared/config.py`, `server/src/analysis/prompts.py`, `server/src/analysis/service.py`, `server/main.py`
- 実装内容:
  - `llm.py` — `AsyncAzureOpenAI` + `set_default_openai_client` / `set_default_openai_api("chat_completions")` / `set_tracing_disabled(True)` でグローバル初期化
  - `config.py` — `azure_openai_endpoint`, `azure_openai_api_key`, `azure_deployment`, `api_version` を必須フィールドに変更。`extra="ignore"` で旧変数を無視
  - `prompts.py` — `ChatPromptTemplate` を廃止しプレーン文字列定数（`EXTRACTION_SYSTEM/HUMAN`, `SUMMARY_SYSTEM/HUMAN`）に変更
  - `service.py` — LangChain チェーンを `Agent` + `Runner.run()` ベースに刷新。`model=settings.azure_deployment`, `ModelSettings(temperature=0)`
  - `main.py` — 起動時に `init_llm()` 呼び出しを追加
  - `uv remove` で langchain / langchain-azure-ai / langgraph / azure-identity 等 41 パッケージ削除

---

## インフラ設定修正

### docker-compose.yml healthcheck 修正 ✅
- 完了日: 2026-04-27
- 内容: healthcheck の `-d app_db` を `-d corporate-research` に修正（POSTGRES_DB と不一致だった）

### alembic.ini sqlalchemy.url 修正 ✅
- 完了日: 2026-04-27
- 内容: `localhost:5432://admin:password@localhost/corporate-research` → `postgresql+asyncpg://admin:password@localhost:5432/corporate-research` に修正

---

## Phase 5: V1 — データ永続化基盤

### T-018: DB スキーマ定義 & マイグレーション ✅
- 完了日: 2026-04-27
- 実装内容:
  - `companies`, `analysis_results`, `analysis_runs` テーブル定義（ORM + Alembic autogenerate）
  - `uv run alembic upgrade head` で適用済み

### T-019: DB クライアント & リポジトリ層 ✅
- 完了日: 2026-04-27
- 対象: `server/src/shared/db.py`, `server/src/db/repository.py`
- 実装内容:
  - SQLAlchemy async engine / session（`get_session` FastAPI Depends 対応）
  - `CompanyRepository` — upsert, find_by_url
  - `AnalysisResultRepository` — save, find_latest_by_company, find_by_id, find_by_share_id, list_by_company
  - `AnalysisRunRepository` — create, update_status, list_by_company

### T-020: 分析サービスへの永続化統合 ✅
- 完了日: 2026-04-27
- 対象: `server/src/analysis/service.py`
- 実装内容:
  - キャッシュチェック（同一URL再入力時に DB から返却）
  - 分析完了後に `companies` / `analysis_results` / `analysis_runs` へ保存
  - `AnalysisResponse` に `result_id`, `company_id`, `is_cached`, `analyzed_at` 追加

### T-021: 永続化対応 API エンドポイント更新 ✅
- 完了日: 2026-04-27
- 対象: `server/src/analysis/router.py`, `server/src/analysis/schemas.py`
- 実装内容:
  - `POST /api/analysis` に `force_refresh`, `template` パラメータ追加
  - `GET /api/analysis/{result_id}` — 過去の分析結果取得
  - `GET /api/companies/{company_id}/runs` — 分析履歴一覧

### T-022: フロントエンド — キャッシュ通知 UI ✅
- 完了日: 2026-04-27
- 対象: `client/src/features/company-search/ui/CompanySearchForm.tsx`
- 実装内容:
  - 過去分析済みの場合に「前回分析: {日時}」バナー表示
  - 「最新情報で更新する」ボタンで `force_refresh=true` 再送信

---

## Phase 6: V1 — 分析履歴管理

### T-023: 分析履歴 API ✅
- 完了日: 2026-04-27
- 対象: `server/src/analysis/router.py`
- 実装内容:
  - `GET /api/companies/{company_id}/runs` — run_type, status, started_at, completed_at, duration_ms 一覧

### T-024: フロントエンド — 分析履歴タブ ✅
- 完了日: 2026-04-27
- 対象: `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`
- 実装内容:
  - Tabs コンポーネントで「分析結果」「分析履歴」「深掘り分析」タブ追加
  - 実行日時・種別・状態・duration 一覧表示

---

## Phase 7: V1 — ダウンロード機能

### T-025: サーバーサイド PDF / Word 生成エンドポイント ✅
- 完了日: 2026-04-27
- 対象: `server/src/download/generator.py`, `server/src/analysis/router.py`
- 実装内容:
  - `uv add weasyprint python-docx markdown` で依存追加
  - `GET /api/analysis/{result_id}/download?format=pdf` — WeasyPrint で HTML→PDF 変換
  - `GET /api/analysis/{result_id}/download?format=docx` — python-docx で Word 生成
  - Noto Sans JP フォント適用、Content-Disposition: attachment

### T-026: フロントエンド — PDF / Word ダウンロード UI ✅
- 完了日: 2026-04-27
- 対象: `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`
- 実装内容:
  - Mantine Menu ドロップダウンで PDF / Word 2択
  - fetch → Blob → `<a>` タグでブラウザダウンロード

---

## Phase 8: V1 — 差分更新分析

### T-027: ページハッシュ管理 ✅
- 完了日: 2026-04-27
- 対象: `server/src/db/models.py`（PageSnapshot モデル追加）
- 実装内容:
  - `page_snapshots` テーブル（content_hash, etag, last_modified, OGP メタ等）
  - Alembic autogenerate で `cf968a334637` マイグレーション生成・適用

### T-028: 差分分析サービス ✅
- 完了日: 2026-04-27
- 対象: `server/src/analysis/service.py`
- 実装内容:
  - `run_type=refresh` 時に前回 structured と比較して `diff_report` 生成
  - `generate_diff_report` を利用

### T-029: フロントエンド — 差分表示 ✅
- 完了日: 2026-04-27
- 対象: `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`
- 実装内容:
  - `diff_report` が存在する場合に「前回分析からの変更点」Alert バナー付きで表示

---

## Phase 9: V1 — 深掘り分析

### T-030: 深掘り分析 API ✅
- 完了日: 2026-04-27
- 対象: `server/src/deep_research/service.py`, `server/src/analysis/router.py`
- 実装内容:
  - `POST /api/companies/{company_id}/deep-research` — openai-agents Agent ループで回答
  - `deep_research_sessions` / `deep_research_messages` テーブルに保存
  - 保存済み structured + summary をコンテキストとして使用

### T-031: フロントエンド — 深掘り質問 UI ✅
- 完了日: 2026-04-27
- 対象: `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`
- 実装内容:
  - 「深掘り分析」タブに会話形式 UI
  - Textarea + 送信ボタン、質問・回答を交互に表示
  - セッション ID を保持して継続会話対応

---

## Phase 10: V2 — 分析テンプレート & スコアリング

### T-032: 分析テンプレート ✅
- 完了日: 2026-04-27
- 対象: `server/src/analysis/prompts.py`, `server/src/analysis/schemas.py`
- 実装内容:
  - `AnalysisRequest` に `template` フィールド追加（general/job_hunting/investment/competitor/partnership）
  - `get_summary_system(template)` でテンプレート別プロンプト分岐
  - フロントエンド: Select コンポーネントでテンプレート選択

### T-033: 分析スコアリング ✅
- 完了日: 2026-04-27
- 対象: `server/src/analysis/service.py`, `server/src/analysis/schemas.py`
- 実装内容:
  - Stage 2 LLM 呼び出しでスコアも同時生成（`ScoreData` — 5観点 × score + reason）
  - `AnalysisResponse` に `scores` フィールド追加
  - フロントエンド: スコアバー + 根拠テキスト表示（ScoreCard コンポーネント）

---

## Phase 11: V2 — 企業名検索・シェア・比較

### T-034: 企業名検索 URL 補完 ✅
- 完了日: 2026-04-27
- 対象: `server/src/search/service.py`, `client/src/features/company-search/ui/CompanySearchForm.tsx`
- 実装内容:
  - `GET /api/search?q={企業名}` — DuckDuckGo Instant Answer API で URL 候補最大5件
  - フロントエンド: Mantine Autocomplete + useDebouncedValue でオートコンプリート

### T-035: 分析結果シェア ✅
- 完了日: 2026-04-27
- 対象: `server/src/analysis/router.py`, `client/src/app/share/[shareId]/page.tsx`
- 実装内容:
  - `POST /api/analysis/{result_id}/share` — share_id 生成（UUID 先頭8文字）
  - `GET /api/share/{share_id}` — 公開分析結果取得（認証不要）
  - フロントエンド: シェアボタン → URL クリップボードコピー + コピー完了フィードバック
  - `/share/[shareId]` ページ（読み取り専用）+ OGP メタタグ

### T-036: 複数企業比較 ✅
- 完了日: 2026-04-27
- 対象: `server/src/analysis/compare_service.py`, `client/src/app/compare/page.tsx`
- 実装内容:
  - `POST /api/compare` — 最大3社を asyncio.gather で並行分析
  - AI による比較サマリー生成（COMPARISON_SYSTEM プロンプト）
  - `comparison_sessions` テーブルに保存
  - フロントエンド: `/compare` ページ（URL入力 × 最大3、横並び比較テーブル・SWOT・財務）
  - トップページに「複数企業を比較する →」リンク追加
