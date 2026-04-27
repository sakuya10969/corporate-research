# 要件定義: download

## はじめに

分析結果をPDFまたはWord形式でダウンロードできる機能（F-009）。サーバーサイドでファイルを生成してブラウザにダウンロードさせる。data-persistence スペックの実装が前提。

## 用語集

- **System**: 企業分析エージェント全体
- **DownloadGenerator**: PDF/Word生成モジュール
- **DownloadButton**: ダウンロードUIコンポーネント
- **WeasyPrint**: サーバーサイドHTML→PDF変換ライブラリ
- **python-docx**: サーバーサイドWord文書生成ライブラリ

## 要件

### 要件1: PDFダウンロード（F-009）

**ユーザーストーリー:** ユーザーとして、分析結果をPDF形式でダウンロードしたい。そうすることで、印刷・提出・共有に活用できる。

#### 受け入れ基準

1. WHEN `GET /api/analysis/{result_id}/download?format=pdf` が呼ばれた場合, THE DownloadGenerator SHALL `markdown_page` をHTMLに変換してWeasyPrintでPDFを生成する
2. THE System SHALL PDFレスポンスに `Content-Disposition: attachment; filename="{企業名}_{YYYY-MM-DD}.pdf"` ヘッダーを付与する
3. THE System SHALL PDFにNoto Sans JPフォントを適用して日本語を正しく表示する
4. IF 指定された `result_id` が存在しない場合, THEN THE System SHALL HTTP 404エラーを返す

---

### 要件2: Wordダウンロード（F-009）

**ユーザーストーリー:** ユーザーとして、分析結果をWord形式でダウンロードしたい。そうすることで、編集・企業研究ノートへの貼り付けに活用できる。

#### 受け入れ基準

1. WHEN `GET /api/analysis/{result_id}/download?format=docx` が呼ばれた場合, THE DownloadGenerator SHALL python-docxで構造化Wordドキュメントを生成する
2. THE System SHALL Wordレスポンスに `Content-Disposition: attachment; filename="{企業名}_{YYYY-MM-DD}.docx"` ヘッダーを付与する
3. THE DownloadGenerator SHALL Wordドキュメントに見出し・表・リスト構造を適用する
4. IF 指定された `result_id` が存在しない場合, THEN THE System SHALL HTTP 404エラーを返す

---

### 要件3: ダウンロードUI（F-009）

**ユーザーストーリー:** ユーザーとして、分析結果ページからワンクリックでダウンロード形式を選択したい。そうすることで、手軽にファイルを取得できる。

#### 受け入れ基準

1. WHEN 分析結果が表示された場合, THE DownloadButton SHALL ダウンロードボタンを表示する
2. WHEN ダウンロードボタンが押された場合, THE DownloadButton SHALL PDF / Word の2択メニューを表示する
3. WHEN ユーザーがフォーマットを選択した場合, THE DownloadButton SHALL fetch → Blob → `<a>` タグでブラウザダウンロードを実行する
