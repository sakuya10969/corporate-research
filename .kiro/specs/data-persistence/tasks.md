# 実装計画: data-persistence

## 概要

PostgreSQL + SQLAlchemy async + Alembic によるデータ永続化基盤の実装。企業マスタ・分析結果・分析実行履歴の3テーブルを構築し、AnalysisServiceにキャッシュチェックと永続化ロジックを統合する。

## タスク

- [x] 1. DBスキーマ定義 & マイグレーション
  - `server/src/db/models.py` — Company, AnalysisResult, AnalysisRun ORM モデル定義
  - Alembic autogenerate でマイグレーションファイル生成
  - `uv run alembic upgrade head` で適用
  - _要件: 1.1, 1.2, 1.3_

- [x] 2. DBクライアント & リポジトリ層
  - [x] 2.1 DBクライアント実装
    - `server/src/shared/db.py` — async engine, get_session (FastAPI Depends 対応)
    - _要件: 1.1_
  - [x] 2.2 CompanyRepository 実装
    - `upsert()`, `find_by_url()` メソッド
    - _要件: 1.1, 2.1_
  - [x] 2.3 AnalysisResultRepository 実装
    - `save()`, `find_latest_by_company()`, `find_by_id()`, `find_by_share_id()`, `list_by_company()` メソッド
    - _要件: 1.2, 3.1, 3.2_
  - [x] 2.4 AnalysisRunRepository 実装
    - `create()`, `update_status()`, `list_by_company()` メソッド
    - _要件: 1.3_

- [x] 3. 分析サービスへの永続化統合
  - `server/src/analysis/service.py` にキャッシュチェック・永続化ロジックを追加
  - 同一URL再入力時に DB から返却（is_cached: true）
  - force_refresh=true 時はキャッシュ無視して新規分析
  - 分析完了後に companies / analysis_results / analysis_runs へ保存
  - _要件: 1.1, 1.2, 1.3, 1.4, 2.1, 2.4_

- [x] 4. 永続化対応 API エンドポイント更新
  - `server/src/analysis/schemas.py` — AnalysisRequest に force_refresh, template 追加; AnalysisResponse に result_id, company_id, is_cached, analyzed_at 追加
  - `server/src/analysis/router.py` — GET /api/analysis/{result_id} エンドポイント追加
  - _要件: 1.4, 3.1, 3.2_

- [x] 5. フロントエンド — キャッシュ通知 UI
  - `client/src/features/company-search/ui/CompanySearchForm.tsx` にキャッシュ通知バナー追加
  - is_cached=true 時に「前回分析: {日時}」バナー表示
  - 「最新情報で更新する」ボタンで force_refresh=true 再送信
  - _要件: 2.2, 2.3_

- [x] 6. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
