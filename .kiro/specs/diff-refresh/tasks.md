# 実装計画: diff-refresh

## 概要

ページハッシュ管理・差分分析サービス・差分表示UIを実装する。data-persistence スペックの完了が前提。

## タスク

- [x] 1. ページハッシュ管理
  - `server/src/db/models.py` に PageSnapshot ORM モデル追加
  - Alembic autogenerate でマイグレーションファイル生成・適用
  - `page_snapshots` テーブル（content_hash, etag, last_modified, OGPメタ等）
  - _要件: 1.1_

- [x] 2. 差分分析サービス
  - [x] 2.1 CollectorService に差分収集ロジック追加
    - `server/src/collector/service.py` に `collect_with_diff()` 実装
    - ETag/Last-Modified 条件付きリクエスト
    - SHA-256 ハッシュ比較で変更ページのみ再取得
    - page_snapshots テーブル更新（is_changed フラグ）
    - _要件: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 2.2 AnalysisService に差分レポート生成追加
    - `server/src/analysis/service.py` に `generate_diff_report()` 実装
    - run_type=refresh 時に前回 structured と比較
    - 新規ニュース・プロフィール変更・新規プロダクト・財務変化を検知
    - 変更なし時は「変更なし」を記録
    - _要件: 2.1, 2.2, 2.3, 2.4_

- [x] 3. フロントエンド — 差分表示
  - `client/src/widgets/analysis-result/ui/AnalysisResult.tsx` に差分Alertバナー追加
  - diff_report 存在時のみ「前回分析からの変更点」Alert を表示
  - _要件: 3.1, 3.2_

- [x] 4. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
