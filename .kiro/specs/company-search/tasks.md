# 実装計画: company-search

## 概要

DuckDuckGo Instant Answer APIを使用した企業名検索エンドポイントと、フロントエンドのオートコンプリートUIを実装する。

## タスク

- [x] 1. 企業名検索 URL 補完
  - [x] 1.1 SearchService 実装
    - `server/src/search/service.py` — DuckDuckGo Instant Answer API 呼び出し
    - 最大5件に絞る処理
    - _要件: 1.1, 1.2, 1.3, 1.4_
  - [x] 1.2 スキーマ定義
    - `server/src/search/schemas.py` — CompanyCandidate, CompanySearchResponse
    - _要件: 1.3_
  - [x] 1.3 ルーター実装
    - `server/src/search/router.py` — `GET /api/search?q={企業名}`
    - 空クエリに対して 400 を返す
    - `server/main.py` に search_router 登録
    - _要件: 1.5_
  - [x] 1.4 フロントエンド — オートコンプリートUI
    - `client/src/features/company-search/ui/CompanySearchForm.tsx` に Mantine Autocomplete 追加
    - `useDebouncedValue(query, 300)` でデバウンス処理
    - 候補選択時にURLフィールドへ自動入力（分析は実行しない）
    - 0件時に「見つかりませんでした。URLを直接入力してください」表示
    - _要件: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
