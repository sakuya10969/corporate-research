# 要件定義: diff-refresh

## はじめに

同じ企業を再分析する際、前回から変化のあったページのみを対象に効率的に更新する差分更新分析機能（F-006）。SHA-256コンテンツハッシュとHTTPヘッダー（ETag/Last-Modified）を組み合わせて変更を検知し、差分レポートを生成する。data-persistence スペックの実装が前提。

## 用語集

- **System**: 企業分析エージェント全体
- **CollectorService**: 企業サイトの情報収集サービス
- **AnalysisService**: 分析フローのオーケストレーションサービス
- **PageSnapshot**: ページ取得スナップショット（`page_snapshots` テーブル）
- **DiffReport**: 差分レポート（変更点のテキスト）
- **DiffAlert**: 差分表示UIコンポーネント

## 要件

### 要件1: ページ変更検知（F-006）

**ユーザーストーリー:** ユーザーとして、再分析時に変更のあったページだけを効率的に処理してほしい。そうすることで、分析時間とコストを削減できる。

#### 受け入れ基準

1. WHEN ページを取得した場合, THE CollectorService SHALL 抽出テキストのSHA-256ハッシュを計算して `page_snapshots` テーブルに保存する
2. WHEN HTTPレスポンスにETagヘッダーが存在する場合, THE CollectorService SHALL ETagを優先的に変更検知に使用する
3. WHEN HTTPレスポンスにLast-Modifiedヘッダーが存在する場合, THE CollectorService SHALL Last-Modifiedを変更検知に使用する
4. WHEN 再分析（run_type=refresh）が実行された場合, THE CollectorService SHALL 前回のcontent_hashと比較して変更のあったページのみを再取得する
5. WHEN ページに変更がない場合, THE CollectorService SHALL そのページの再取得をスキップする

---

### 要件2: 差分レポート生成（F-006）

**ユーザーストーリー:** ユーザーとして、再分析時に前回からの変更点を確認したい。そうすることで、企業の最新動向を素早く把握できる。

#### 受け入れ基準

1. WHEN 再分析が完了した場合, THE AnalysisService SHALL 前回の `structured` データと比較して差分レポートを生成する
2. THE System SHALL 差分レポートに新規追加ニュース・変更された企業プロフィール項目・新規プロダクト・財務情報の変化を含める
3. WHEN 変更がなかった場合, THE AnalysisService SHALL 差分レポートに「変更なし」と記録する
4. THE System SHALL 差分レポートを `analysis_results.diff_report` カラムに保存する

---

### 要件3: 差分表示UI（F-006）

**ユーザーストーリー:** ユーザーとして、差分レポートを分析結果ページで確認したい。そうすることで、前回分析からの変化を視覚的に把握できる。

#### 受け入れ基準

1. WHEN `diff_report` フィールドが存在する場合, THE DiffAlert SHALL 「前回分析からの変更点」Alertバナーを表示する
2. WHEN `diff_report` フィールドが存在しない場合, THE DiffAlert SHALL Alertバナーを表示しない
