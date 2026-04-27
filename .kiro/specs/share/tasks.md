# 実装計画: share

## 概要

シェアID生成・共有分析結果取得APIと、フロントエンドのシェアボタン・共有ページ（OGP対応）を実装する。data-persistence スペックの完了が前提。

## タスク

- [x] 1. 分析結果シェア
  - [x] 1.1 シェアエンドポイント実装
    - `server/src/analysis/router.py` に `POST /api/analysis/{result_id}/share` 追加
    - UUID v4 先頭8文字で share_id 生成
    - 既存 share_id がある場合は再利用（冪等性）
    - `analysis_results.share_id` / `shared_at` を更新
    - 存在しない result_id に対して 404 を返す
    - _要件: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [x] 1.2 共有分析結果取得エンドポイント実装
    - `server/src/analysis/router.py` に `GET /api/share/{share_id}` 追加
    - AnalysisResultRepository.find_by_share_id() を使用
    - 存在しない share_id に対して 404 を返す
    - _要件: 2.1, 2.2, 2.3_
  - [x] 1.3 フロントエンド — シェアボタン
    - `client/src/widgets/analysis-result/ui/AnalysisResult.tsx` にシェアボタン追加
    - POST /api/analysis/{result_id}/share → share_id 取得
    - 共有URL（/share/{share_id}）をクリップボードにコピー
    - コピー完了フィードバック表示
    - _要件: 3.1, 3.2, 3.3_
  - [x] 1.4 共有ページ実装
    - `client/src/app/share/[shareId]/page.tsx` 新規作成
    - 読み取り専用の AnalysisResult 表示
    - `generateMetadata()` で OGP メタタグ動的生成
    - og:title = `{企業名} の企業分析レポート`
    - og:description = overview 先頭150文字
    - _要件: 4.1, 4.2, 4.3, 4.4_

- [x] 2. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
