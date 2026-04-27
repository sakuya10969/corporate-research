# 要件定義: compare

## はじめに

2〜3社の企業URLを入力して並行分析・比較できる機能（F-013）。`asyncio.gather` で並行実行し、横並び比較テーブルとAIによる比較サマリーを生成する。data-persistence スペックの実装が前提。

## 用語集

- **System**: 企業分析エージェント全体
- **CompareService**: 複数企業比較サービス
- **ComparePage**: 比較分析ページ（`/compare`）
- **ComparisonTable**: 横並び比較テーブルUIコンポーネント
- **comparison_sessions**: 比較セッション保存テーブル

## 要件

### 要件1: 複数企業並行分析 API（F-013）

**ユーザーストーリー:** ユーザーとして、複数の企業URLを一度に入力して並行分析・比較したい。そうすることで、企業間の違いを効率的に把握できる。

#### 受け入れ基準

1. WHEN `POST /api/compare` が呼ばれた場合, THE CompareService SHALL 指定された企業URLを `asyncio.gather` で並行分析する
2. THE System SHALL 比較対象を最小2社・最大3社に制限する
3. IF `company_urls` が2件未満または4件以上の場合, THEN THE System SHALL HTTP 400エラーを返す
4. WHEN 全企業の分析が完了した場合, THE CompareService SHALL AIによる比較サマリーを生成する
5. THE System SHALL 比較結果を `comparison_sessions` テーブルに保存する
6. THE System SHALL レスポンスに各企業の分析結果・比較サマリー・使用テンプレートを含める

---

### 要件2: 比較表示UI（F-013）

**ユーザーストーリー:** ユーザーとして、複数企業の分析結果を横並びで比較したい。そうすることで、企業間の強み・弱みを直感的に把握できる。

#### 受け入れ基準

1. THE ComparePage SHALL `/compare` パスで企業URL入力フィールドを最大3つ表示する
2. WHEN 「比較分析する」ボタンが押された場合, THE ComparePage SHALL `POST /api/compare` を呼び出す
3. WHEN 比較結果が返った場合, THE ComparisonTable SHALL 企業プロフィール・財務情報・SWOT分析・スコアを横並びで表示する
4. WHEN 比較結果が返った場合, THE ComparePage SHALL AIによる比較サマリーを表示する
5. THE ComparePage SHALL トップページから「複数企業を比較する」リンクで遷移できる
