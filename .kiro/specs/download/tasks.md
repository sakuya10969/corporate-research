# 実装計画: download

## 概要

WeasyPrint（PDF）とpython-docx（Word）を使用したサーバーサイドファイル生成機能と、フロントエンドのダウンロードUIを実装する。data-persistence スペックの完了が前提。

## タスク

- [x] 1. サーバーサイド PDF / Word 生成エンドポイント
  - [x] 1.1 依存ライブラリ追加
    - `uv add weasyprint python-docx markdown` で依存追加
  - [x] 1.2 DownloadGenerator 実装
    - `server/src/download/generator.py` — `generate_pdf()`, `generate_docx()` 実装
    - Noto Sans JP フォント CSS 適用（PDF）
    - 見出し・表・リスト構造（Word）
    - _要件: 1.1, 1.3, 2.1, 2.3_
  - [x] 1.3 ダウンロードエンドポイント追加
    - `server/src/analysis/router.py` に `GET /api/analysis/{result_id}/download?format=pdf|docx` 追加
    - Content-Disposition: attachment ヘッダー付与
    - 存在しない result_id に対して 404 を返す
    - _要件: 1.2, 1.4, 2.2, 2.4_

- [x] 2. フロントエンド — ダウンロード UI
  - `client/src/widgets/analysis-result/ui/AnalysisResult.tsx` に Mantine Menu ドロップダウン追加
  - PDF / Word 2択メニュー
  - fetch → Blob → `<a>` タグでブラウザダウンロード
  - _要件: 3.1, 3.2, 3.3_

- [x] 3. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
