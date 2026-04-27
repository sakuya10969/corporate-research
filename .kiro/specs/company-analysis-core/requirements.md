# 要件定義: company-analysis-core

## はじめに

企業分析エージェントのMVPコア機能。ユーザーが企業URLを入力し、AIが企業サイトを自動収集・分析して構造化された結果を表示する。Markdownレポートの折りたたみ表示も含む。

## 用語集

- **System**: 企業分析エージェント全体
- **Validator**: フロントエンドのValibotバリデーター
- **CollectorService**: 企業サイトの情報収集サービス
- **AnalysisService**: LLMを用いた分析サービス
- **AnalysisResult**: 分析結果表示ウィジェット

## 要件

### 要件1: 企業URL入力フォーム（F-001）

**ユーザーストーリー:** 就活生・投資家として、企業URLを入力して分析を開始したい。そうすることで、企業情報を素早く収集できる。

#### 受け入れ基準

1. THE System SHALL 企業URLを入力するテキストフィールドと「分析する」ボタンを表示する
2. WHEN ユーザーがURLを未入力のまま送信しようとした場合, THE Validator SHALL 「URLを入力してください」というエラーメッセージを表示する
3. WHEN ユーザーが `http://` または `https://` で始まらないURLを入力した場合, THE Validator SHALL 「http:// または https:// で始まるURLを入力してください」というエラーメッセージを表示する
4. WHEN ユーザーが空白のみの文字列を入力した場合, THE Validator SHALL 送信を拒否してエラーメッセージを表示する
5. WHILE 分析が実行中の場合, THE System SHALL フォームを無効化して二重送信を防止する

---

### 要件2: 企業分析実行（F-002）

**ユーザーストーリー:** ユーザーとして、企業URLを送信するだけで企業の公開情報を自動収集・AI分析してほしい。そうすることで、手動で情報を集める手間を省ける。

#### 受け入れ基準

1. WHEN 有効な企業URLが送信された場合, THE CollectorService SHALL 対象ドメイン内の公開ページを最大15ページ収集する
2. WHEN サイトマップ（/sitemap.xml）が存在する場合, THE CollectorService SHALL サイトマップを優先してURL一覧を取得する
3. IF サイトマップが存在しない場合, THEN THE CollectorService SHALL トップページからの内部リンクを深さ1〜2で探索する
4. WHEN ページ収集が完了した場合, THE AnalysisService SHALL Stage 1 LLMで企業プロフィール・事業領域・財務情報・ニュース・リスクを構造化抽出する
5. WHEN Stage 1が完了した場合, THE AnalysisService SHALL Stage 2 LLMで企業概要・事業モデル・SWOT分析・競合推定・今後の展望を生成する
6. IF 情報収集に失敗した場合, THEN THE System SHALL HTTP 500エラーレスポンスを返す
7. IF 外部LLMサービスが利用不可の場合, THEN THE System SHALL HTTP 503エラーレスポンスを返す

---

### 要件3: 分析結果表示（F-003）

**ユーザーストーリー:** ユーザーとして、分析結果をわかりやすいカード形式で確認したい。そうすることで、企業情報を素早く把握できる。

#### 受け入れ基準

1. WHILE 分析が実行中の場合, THE AnalysisResult SHALL スケルトンUIを表示する
2. WHEN 分析が完了した場合, THE AnalysisResult SHALL 企業名・URLをヘッダーに表示する
3. WHEN 分析が完了した場合, THE AnalysisResult SHALL 企業概要・企業プロフィール・事業モデル・事業領域・プロダクト・財務情報・SWOT分析・リスク要因・競合企業・今後の展望・ニュース・参照ソースをカード形式で表示する
4. WHEN データが存在しないセクションがある場合, THE AnalysisResult SHALL そのセクションを非表示にする
5. IF 分析でエラーが発生した場合, THEN THE AnalysisResult SHALL エラーメッセージを表示する

---

### 要件4: Markdownレポート出力（F-004）

**ユーザーストーリー:** ユーザーとして、分析結果をMarkdown形式で確認・コピーしたい。そうすることで、外部ツールに貼り付けて活用できる。

#### 受け入れ基準

1. WHEN 分析が完了した場合, THE AnalysisResult SHALL 分析結果ページ下部に「レポート全文を表示」ボタンを表示する
2. WHEN ユーザーが「レポート全文を表示」をクリックした場合, THE AnalysisResult SHALL Markdownレポートを展開表示する
3. THE System SHALL Markdownレポートに企業プロフィール・事業領域・プロダクト・財務情報・ニュース・企業概要・事業モデル・SWOT分析・リスク要因・競合企業・今後の展望・参照ソースを含める
