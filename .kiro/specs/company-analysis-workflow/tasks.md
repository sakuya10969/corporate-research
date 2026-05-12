# 実装計画: 企業分析ワークフロー変革

## 概要

現行の同期型 `analyze_company()` を責務別サービスに分割し、企業登録→バックグラウンドジョブ→蓄積データ活用の非同期ワークフローを実装する。既存エンドポイント・DBスキーマは維持しつつ、段階的に新アーキテクチャへ移行する。

## タスク

- [x] 1. CompanyService の実装
  - [x] 1.1 `server/src/companies/` モジュールを作成し、CompanyService クラスを実装する
    - `register_company(url)`: URL正規化、重複チェック、Company レコード作成（status="pending"）
    - `get_company(company_id)`: 企業詳細取得
    - `list_companies()`: 企業一覧取得
    - `update_display_name(company_id, name)`: 表示名更新
    - 既存の `CompanyRepository` を活用する
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - [x] 1.2 `server/src/companies/schemas.py` を作成し、Pydantic スキーマを定義する
    - `RegisterCompanyRequest`, `CompanyResponse`, `CompanyListResponse`, `CompanyDetailResponse`
    - _Requirements: 2.1, 2.2, 10.1, 10.2, 10.3_
  - [ ]* 1.3 CompanyService のプロパティテストを作成する
    - **Property 1: URL正規化の一貫性**
    - **Property 2: 企業登録の冪等性（URL重複防止）**
    - **Property 3: 企業登録の初期状態とジョブ自動投入**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.5**
  - [ ]* 1.4 CompanyService のユニットテストを作成する
    - 無効なURL入力のバリデーション
    - 正規化のエッジケース（末尾スラッシュ、www有無、ポート番号）
    - _Requirements: 1.2, 1.3_

- [x] 2. CrawlService の実装
  - [x] 2.1 `server/src/crawler/service.py` を作成し、CrawlService クラスを実装する
    - `crawl(company_id, run_id)`: 既存の `collect_company_info()` をラップし、pages/page_versions に保存
    - Company の last_page_crawl_at を更新
    - 既存の `collector/service.py` と `PageRepository` を活用する
    - _Requirements: 3.1, 3.2, 3.3_
  - [ ]* 2.2 CrawlService のプロパティテストを作成する
    - **Property 6: クロール結果の永続化**
    - **Validates: Requirements 3.2, 3.3**

- [x] 3. ExtractionService の実装
  - [x] 3.1 `server/src/extraction/service.py` を作成し、ExtractionService クラスを実装する
    - `extract(company_id, run_id)`: 既存の `_extract_structured()` をラップし、構造化データを保存
    - page_versions から LLM 向けコンテキストを構築
    - _Requirements: 4.1, 4.2_
  - [ ]* 3.2 ExtractionService のプロパティテストを作成する
    - **Property 8: 構造化抽出結果の保存**
    - **Validates: Requirements 4.2**

- [x] 4. AnalysisService の実装
  - [x] 4.1 `server/src/analysis/analysis_service.py` を作成し、AnalysisService クラスを実装する
    - `analyze(company_id, run_id, template)`: 既存の `_generate_summary_and_scores()` をラップし、結果を保存
    - `run_deep_analysis(company_id, template)`: 蓄積データを使用したテンプレート別再分析
    - markdown_page 生成、diff_report 生成を含む
    - _Requirements: 4.3, 4.4, 6.1, 6.2, 6.3_
  - [ ]* 4.2 AnalysisService のプロパティテストを作成する
    - **Property 9: 分析結果の保存**
    - **Property 11: Deep Analysis の蓄積データ活用**
    - **Property 14: 再分析時の差分レポート生成**
    - **Validates: Requirements 4.4, 6.1, 6.2, 6.3, 7.3**

- [x] 5. チェックポイント - サービス層の動作確認
  - 全サービスのテストが通ることを確認する。不明点があればユーザーに質問する。

- [x] 6. JobManager の実装
  - [x] 6.1 `server/src/jobs/manager.py` を作成し、JobManager クラスを実装する
    - `enqueue_full_pipeline(company_id, background_tasks, template, force_refresh)`: パイプラインをキューに追加
    - `_run_pipeline(company_id, run_id, template)`: crawl → extract → analyze のフルパイプライン実行
    - `get_run_status(run_id)`: ジョブ状態取得
    - 状態遷移管理: pending → crawling → extracting → analyzing → completed / failed
    - エラーハンドリング: 各フェーズの例外を捕捉し、status="failed" + エラー情報記録
    - 新しい AsyncSession を BackgroundTask 内で作成する
    - _Requirements: 3.1, 3.5, 4.1, 4.3, 4.5, 4.6, 5.1, 5.2, 5.3, 11.1, 11.2, 11.3_
  - [ ]* 6.2 JobManager のプロパティテストを作成する
    - **Property 5: パイプライン状態遷移の正当性**
    - **Property 7: パイプライン失敗時のエラー記録**
    - **Property 10: ジョブ状態追跡のタイムスタンプ整合性**
    - **Validates: Requirements 3.1, 3.4, 4.1, 4.3, 4.5, 4.6, 5.2, 5.3**

- [x] 7. 新規APIエンドポイントの実装
  - [x] 7.1 `server/src/companies/router.py` を作成し、企業管理エンドポイントを実装する
    - POST /api/companies: 企業登録（CompanyService.register_company + JobManager.enqueue_full_pipeline）
    - GET /api/companies: 企業一覧
    - GET /api/companies/{company_id}: 企業詳細（最新結果・直近run含む）
    - POST /api/companies/{company_id}/crawl: クロールジョブ開始
    - POST /api/companies/{company_id}/analysis-runs: 分析ジョブ開始（テンプレート指定、Deep Analysis対応）
    - GET /api/companies/{company_id}/analysis-results/latest: 最新分析結果
    - GET /api/companies/{company_id}/analysis-results: 分析履歴
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_
  - [x] 7.2 `server/src/jobs/router.py` を作成し、ジョブ状態エンドポイントを実装する
    - GET /api/analysis-runs/{run_id}: ジョブ状態取得
    - _Requirements: 10.8_
  - [x] 7.3 `server/main.py` に新規ルーターを登録する
    - companies_router と jobs_router を include_router で追加
    - _Requirements: 10.1-10.8_
  - [ ]* 7.4 新規エンドポイントのプロパティテストを作成する
    - **Property 4: 企業一覧・詳細レスポンスの完全性**
    - **Validates: Requirements 2.1, 2.2**

- [x] 8. 既存 analyze_company() のリファクタリング
  - [x] 8.1 `server/src/analysis/service.py` の `analyze_company()` を新サービス層を使用するようリファクタリングする
    - CompanyService, CrawlService, ExtractionService, AnalysisService を内部で呼び出す
    - 既存の同期的な動作（レスポンスを待って返す）は維持する
    - 既存の AnalysisResponse スキーマとの後方互換性を維持する
    - _Requirements: 8.1, 8.2, 8.3, 9.1, 13.2_
  - [ ]* 8.2 レガシー分析のプロパティテストを作成する
    - **Property 15: レガシー分析の後方互換性**
    - **Validates: Requirements 8.2, 8.3**

- [ ] 9. キャッシュ・再分析ポリシーの実装
  - [x] 9.1 force_refresh フラグに基づくキャッシュ/再分析ロジックを CompanyService と JobManager に実装する
    - force_refresh=false: 最新結果を返却
    - force_refresh=true: 新規パイプラインを開始
    - _Requirements: 7.1, 7.2, 7.3_
  - [ ]* 9.2 キャッシュポリシーのプロパティテストを作成する
    - **Property 12: キャッシュヒット（force_refresh=false）**
    - **Property 13: 強制リフレッシュによる新規パイプライン**
    - **Validates: Requirements 7.1, 7.2**

- [x] 10. チェックポイント - バックエンド統合確認
  - 全テストが通ることを確認する。不明点があればユーザーに質問する。
  - Orval 再生成（`cd client && npx orval`）で新APIの型定義を生成する。

- [x] 11. フロントエンド: 企業登録・一覧ページの実装
  - [x] 11.1 `client/src/app/companies/page.tsx` を作成し、企業一覧ページを実装する
    - 企業一覧テーブル（名前、URL、ステータス、最終分析日時、スコア）
    - 企業登録フォーム（URL入力 + 登録ボタン）
    - ステータスバッジ表示（pending, crawling, analyzing, completed, failed）
    - Orval 生成フックを使用
    - _Requirements: 2.1, 2.3_
  - [x] 11.2 `client/src/app/companies/[companyId]/page.tsx` を作成し、企業詳細ページを実装する
    - 企業基本情報、最新分析結果の表示
    - 分析履歴タブ
    - Deep Analysis 実行フォーム（テンプレート選択）
    - 再クロール・再分析ボタン
    - _Requirements: 2.2, 6.1, 6.2_

- [x] 12. 最終チェックポイント - 全体統合確認
  - 全テストが通ることを確認する。不明点があればユーザーに質問する。

## 備考

- `*` マーク付きタスクはオプションであり、MVP速度を優先する場合はスキップ可能
- 各タスクは要件番号で追跡可能
- チェックポイントで段階的に動作確認を行う
- プロパティテストは hypothesis ライブラリを使用し、各テスト最低100回のイテレーションで実行する
- 既存の collector/service.py, analysis/prompts.py, shared/ モジュールは変更しない
