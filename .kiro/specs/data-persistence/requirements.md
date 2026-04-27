# 要件定義: data-persistence

## はじめに

企業分析結果をPostgreSQLデータベースに永続化する機能。同一URLの再入力時にキャッシュを活用し、過去の分析結果を再利用または強制再分析できるようにする。

## 用語集

- **System**: 企業分析エージェント全体
- **AnalysisService**: 分析フローのオーケストレーションサービス
- **CompanyRepository**: 企業マスタのリポジトリ
- **AnalysisResultRepository**: 分析結果のリポジトリ
- **AnalysisRunRepository**: 分析実行履歴のリポジトリ
- **CacheNotification**: キャッシュ済み通知UI

## 要件

### 要件1: 分析結果の永続化（F-005）

**ユーザーストーリー:** ユーザーとして、分析した企業の情報をDBに保存してほしい。そうすることで、同じ企業を再入力したときに過去データを活用できる。

#### 受け入れ基準

1. WHEN 企業分析が完了した場合, THE AnalysisService SHALL 企業情報を `companies` テーブルに保存する
2. WHEN 企業分析が完了した場合, THE AnalysisService SHALL 分析結果を `analysis_results` テーブルに保存する
3. WHEN 企業分析が完了した場合, THE AnalysisService SHALL 分析実行記録を `analysis_runs` テーブルに保存する
4. THE System SHALL `result_id`, `company_id`, `is_cached`, `analyzed_at` をレスポンスに含める

---

### 要件2: キャッシュ通知と再分析選択（F-005）

**ユーザーストーリー:** ユーザーとして、同じ企業URLを再入力したときに過去の分析済みであることを知りたい。そうすることで、不要な再分析を避けられる。

#### 受け入れ基準

1. WHEN 同一URLが再入力された場合, THE System SHALL 過去の分析結果をDBから返却し `is_cached: true` をレスポンスに含める
2. WHEN `is_cached: true` のレスポンスを受け取った場合, THE CacheNotification SHALL 「前回分析: {日時}」バナーを表示する
3. WHEN ユーザーが「最新情報で更新する」ボタンを押した場合, THE System SHALL `force_refresh: true` で再分析を実行する
4. WHEN `force_refresh: true` が指定された場合, THE AnalysisService SHALL キャッシュを無視して新規分析を実行する

---

### 要件3: 分析結果の取得（F-005）

**ユーザーストーリー:** ユーザーとして、過去の分析結果をIDで取得したい。そうすることで、特定の分析結果を参照できる。

#### 受け入れ基準

1. WHEN `GET /api/analysis/{result_id}` が呼ばれた場合, THE System SHALL 指定IDの分析結果を返す
2. IF 指定IDの分析結果が存在しない場合, THEN THE System SHALL HTTP 404エラーを返す
