# 実装計画: company-analysis-core

## 概要

企業分析エージェントMVPのコア機能実装。バックエンドのFastAPI + openai-agents 2段階パイプラインとフロントエンドのFSD構成を構築する。

## タスク

- [x] 1. shared モジュールの作成
  - `server/src/shared/config.py` — pydantic-settings による Settings クラス
  - `server/src/shared/llm.py` — AsyncAzureOpenAI + set_default_openai_client 初期化
  - `server/src/shared/exceptions.py` — CollectionError, AnalysisError, ExternalServiceError 定義
  - _要件: 2.6, 2.7_

- [x] 2. collector モジュールの作成
  - [x] 2.1 CollectorService 実装
    - `server/src/collector/service.py` — サイトマップ探索・内部リンク探索・ページ取得・カテゴリ分類
    - _要件: 2.1, 2.2, 2.3_
  - [x] 2.2 HTMLパーサー実装
    - `server/src/collector/parsers.py` — BeautifulSoup + lxml による構造保持テキスト抽出
    - _要件: 2.1_

- [x] 3. analysis モジュールの作成
  - [x] 3.1 スキーマ定義
    - `server/src/analysis/schemas.py` — AnalysisRequest, AnalysisResponse, StructuredData, SummaryData 等
    - _要件: 1.1, 2.4, 2.5_
  - [x] 3.2 プロンプト定義
    - `server/src/analysis/prompts.py` — EXTRACTION_SYSTEM/HUMAN, SUMMARY_SYSTEM/HUMAN
    - _要件: 2.4, 2.5_
  - [x] 3.3 AnalysisService 実装
    - `server/src/analysis/service.py` — 2段階LLMパイプライン（extraction_agent → summary_agent）
    - _要件: 2.4, 2.5_
  - [x] 3.4 ルーター実装
    - `server/src/analysis/router.py` — POST /api/analysis, GET /api/health
    - _要件: 2.1, 2.6, 2.7_

- [x] 4. FastAPI アプリケーション統合
  - `server/main.py` — analysis_router 登録、CORS設定、共通例外ハンドラー登録、init_llm() 呼び出し
  - _要件: 2.6, 2.7_

- [x] 5. OpenAPI → Orval 自動生成
  - [x] 5.1 Orval 設定ファイル作成
    - `client/orval.config.ts` — input: openapi.json, output: react-query クライアント
  - [x] 5.2 Axios インスタンス作成
    - `client/src/shared/api/instance.ts` — baseURL: NEXT_PUBLIC_API_URL
  - [x] 5.3 API クライアント生成
    - `npx orval` で型・フック自動生成

- [x] 6. フロントエンド基盤
  - [x] 6.1 Mantine テーマ設定
    - `client/src/app/layout.tsx` — primaryColor: blue, defaultRadius: md
  - [x] 6.2 shared/config 作成
    - `client/src/shared/config/env.ts` — env.apiUrl
  - [x] 6.3 React Query プロバイダー設定
    - `client/src/app/query-provider.tsx` — QueryClientProvider

- [x] 7. フロントエンド機能実装
  - [x] 7.1 企業URL入力フォーム
    - `client/src/features/company-search/model/schema.ts` — Valibot バリデーション（URL必須・http/https・空白不可）
    - `client/src/features/company-search/ui/CompanySearchForm.tsx` — TextInput + Button
    - _要件: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 7.2 企業エンティティ表示コンポーネント
    - `client/src/entities/company/ui/CompanyCard.tsx` — カードコンポーネント
    - _要件: 3.2, 3.3_
  - [x] 7.3 分析結果表示ウィジェット
    - `client/src/widgets/analysis-result/ui/AnalysisResult.tsx` — スケルトンUI・エラー表示・結果カード
    - _要件: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3_
  - [x] 7.4 トップページ組み立て
    - `client/src/app/page.tsx` — CompanySearchForm + AnalysisResult 配置
    - _要件: 1.1_

- [x] 8. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
