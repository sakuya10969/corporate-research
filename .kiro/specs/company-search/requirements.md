# 要件定義: company-search

## はじめに

企業名入力でURL候補をオートコンプリート表示する機能（F-011）。DuckDuckGo Instant Answer APIを使用してAPIキー不要で企業の公式サイトURL候補を最大5件取得する。候補選択後はURLフィールドへ自動入力するが、自動分析は実行しない。

## 用語集

- **System**: 企業分析エージェント全体
- **SearchService**: 企業名検索サービス
- **AutocompleteInput**: オートコンプリートUIコンポーネント

## 要件

### 要件1: 企業名検索 API（F-011）

**ユーザーストーリー:** ユーザーとして、企業名を入力するだけで公式サイトURLの候補を取得したい。そうすることで、URLを知らなくても分析を開始できる。

#### 受け入れ基準

1. WHEN `GET /api/search?q={企業名}` が呼ばれた場合, THE SearchService SHALL DuckDuckGo Instant Answer APIを使用してURL候補を取得する
2. THE System SHALL URL候補を最大5件に絞って返す
3. THE System SHALL 各候補に企業名・URL・説明文を含める
4. WHEN 検索結果が0件の場合, THE System SHALL 空の `results` 配列を返す
5. IF 企業名が空文字の場合, THEN THE System SHALL HTTP 400エラーを返す

---

### 要件2: オートコンプリートUI（F-011）

**ユーザーストーリー:** ユーザーとして、企業名を入力しながらURL候補をリアルタイムで確認したい。そうすることで、正確なURLを素早く選択できる。

#### 受け入れ基準

1. WHEN ユーザーが企業名を入力した場合, THE AutocompleteInput SHALL デバウンス処理（300ms）後に検索APIを呼び出す
2. WHEN 検索結果が返った場合, THE AutocompleteInput SHALL 候補リストをドロップダウンで表示する
3. WHEN ユーザーが候補を選択した場合, THE AutocompleteInput SHALL URLフィールドに選択したURLを自動入力する
4. WHEN ユーザーが候補を選択した場合, THE AutocompleteInput SHALL 自動的に分析を開始しない
5. WHEN 検索結果が0件の場合, THE AutocompleteInput SHALL 「見つかりませんでした。URLを直接入力してください」と表示する
