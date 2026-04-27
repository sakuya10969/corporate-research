# 実装計画: compare

## 概要

asyncio.gather による並行分析・AI比較サマリー生成・comparison_sessions 保存と、フロントエンドの比較ページを実装する。data-persistence スペックの完了が前提。

## タスク

- [x] 1. 複数企業比較
  - [x] 1.1 DBモデル追加
    - `server/src/db/models.py` に ComparisonSession ORM モデル追加
    - Alembic autogenerate でマイグレーション生成・適用
    - _要件: 1.5_
  - [x] 1.2 スキーマ定義
    - `server/src/analysis/schemas.py` に CompareRequest, CompareResponse スキーマ追加
    - company_urls: 2〜3件のバリデーション
    - _要件: 1.2, 1.3, 1.6_
  - [x] 1.3 COMPARISON_SYSTEM プロンプト追加
    - `server/src/analysis/prompts.py` に COMPARISON_SYSTEM 定数追加
    - _要件: 1.4_
  - [x] 1.4 CompareService 実装
    - `server/src/analysis/compare_service.py` 新規作成
    - asyncio.gather で並行分析
    - COMPARISON_SYSTEM プロンプトで比較サマリー生成
    - comparison_sessions テーブルに保存
    - _要件: 1.1, 1.4, 1.5_
  - [x] 1.5 比較エンドポイント追加
    - `server/src/analysis/router.py` に `POST /api/compare` 追加
    - 2件未満・4件以上に対して 400 を返す
    - `server/main.py` への統合確認
    - _要件: 1.3_
  - [x] 1.6 フロントエンド — 比較ページ
    - `client/src/app/compare/page.tsx` 新規作成
    - URL入力フィールド × 最大3（動的追加）
    - 「比較分析する」ボタン → POST /api/compare
    - 横並び比較テーブル（企業プロフィール・財務・SWOT・スコア）
    - AIによる比較サマリー表示
    - _要件: 2.1, 2.2, 2.3, 2.4_
  - [x] 1.7 トップページにリンク追加
    - `client/src/app/page.tsx` に「複数企業を比較する →」リンク追加
    - _要件: 2.5_

- [x] 2. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
