# 要件定義: analysis-history

## はじめに

企業ごとの分析実行履歴を一覧表示する機能（F-008）。`analysis_runs` テーブルを使用して、実行日時・種別・状態・処理時間を表示する。data-persistence スペックの実装が前提。

## 用語集

- **System**: 企業分析エージェント全体
- **AnalysisRunRepository**: 分析実行履歴のリポジトリ
- **HistoryTab**: 分析履歴タブUIコンポーネント
- **RunType**: 分析種別（initial / refresh / deep_research）
- **RunStatus**: 実行状態（pending / running / completed / failed）

## 要件

### 要件1: 分析履歴 API（F-008）

**ユーザーストーリー:** ユーザーとして、企業ごとの分析実行履歴をAPIで取得したい。そうすることで、過去の分析実行状況を確認できる。

#### 受け入れ基準

1. WHEN `GET /api/companies/{company_id}/runs` が呼ばれた場合, THE System SHALL 該当企業の分析実行履歴を新しい順で返す
2. THE System SHALL 各履歴に `run_id`, `run_type`, `status`, `started_at`, `completed_at`, `duration_ms` を含める
3. IF 指定された `company_id` が存在しない場合, THEN THE System SHALL HTTP 404エラーを返す

---

### 要件2: 分析履歴タブ表示（F-008）

**ユーザーストーリー:** ユーザーとして、分析結果ページで過去の分析実行履歴を確認したい。そうすることで、いつどの種類の分析を実行したかを把握できる。

#### 受け入れ基準

1. WHEN 分析結果が表示された場合, THE HistoryTab SHALL 分析結果ウィジェットに「分析履歴」タブを表示する
2. WHEN 「分析履歴」タブが選択された場合, THE HistoryTab SHALL 実行日時・種別（initial/refresh/deep_research）・状態（pending/running/completed/failed）・処理時間を一覧表示する
3. WHEN 実行状態が `completed` の場合, THE HistoryTab SHALL 緑色のバッジで表示する
4. WHEN 実行状態が `failed` の場合, THE HistoryTab SHALL 赤色のバッジで表示する
