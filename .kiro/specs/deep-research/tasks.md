# 実装計画: deep-research

## 概要

openai-agents SDKを使用した深掘り分析APIとフロントエンドの会話形式UIを実装する。data-persistence スペックの完了が前提。

## タスク

- [x] 1. 深掘り分析 API
  - [x] 1.1 DBモデル追加
    - `server/src/db/models.py` に DeepResearchSession, DeepResearchMessage ORM モデル追加
    - Alembic autogenerate でマイグレーション生成・適用
    - _要件: 1.3_
  - [x] 1.2 DeepResearchService 実装
    - `server/src/deep_research/service.py` — openai-agents Agent ループで回答生成
    - 保存済み structured + summary をコンテキストとして使用
    - セッション取得 or 新規作成ロジック
    - メッセージ保存（deep_research_sessions / deep_research_messages）
    - _要件: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 1.3 エンドポイント追加
    - `server/src/analysis/router.py` に `POST /api/companies/{company_id}/deep-research` 追加
    - DeepResearchRequest / DeepResearchResponse スキーマ定義
    - 存在しない company_id に対して 404 を返す
    - _要件: 1.6_

- [x] 2. フロントエンド — 深掘り質問 UI
  - `client/src/widgets/analysis-result/ui/AnalysisResult.tsx` の「深掘り分析」タブに会話形式UI追加
  - Textarea + 送信ボタン
  - 質問・回答を交互に表示（会話形式）
  - ローディング表示
  - セッションID保持で継続会話対応
  - _要件: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
