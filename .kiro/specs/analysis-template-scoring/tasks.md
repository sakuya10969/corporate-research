# 実装計画: analysis-template-scoring

## 概要

テンプレート別プロンプト分岐とStage 2 LLMでのスコア同時生成を実装する。スキーマ変更は最小限。

## タスク

- [x] 1. 分析テンプレート
  - [x] 1.1 プロンプト拡張
    - `server/src/analysis/prompts.py` に `TEMPLATE_INSTRUCTIONS` 辞書と `get_summary_system(template)` 関数追加
    - 5テンプレート（general/job_hunting/investment/competitor/partnership）のプロンプト分岐
    - _要件: 1.1, 1.2, 1.3_
  - [x] 1.2 スキーマ拡張
    - `server/src/analysis/schemas.py` の `AnalysisRequest` に `template` フィールド追加
    - `AnalysisResponse` に `template` フィールド追加
    - _要件: 1.4_
  - [x] 1.3 フロントエンド — テンプレート選択UI
    - `client/src/features/company-search/ui/CompanySearchForm.tsx` に Mantine Select 追加
    - 5テンプレートの選択肢を表示
    - _要件: 3.1_

- [x] 2. 分析スコアリング
  - [x] 2.1 スコアスキーマ定義
    - `server/src/analysis/schemas.py` に ScoreItem, ScoreData スキーマ追加
    - `AnalysisResponse` に `scores: ScoreData | None` フィールド追加
    - _要件: 2.1, 2.2_
  - [x] 2.2 Stage 2 LLMでスコア同時生成
    - `server/src/analysis/service.py` の Stage 2 呼び出しでスコアも同時生成
    - `server/src/analysis/prompts.py` に SCORING_INSTRUCTION 追加
    - _要件: 2.3_
  - [x] 2.3 スコア永続化
    - `server/src/analysis/service.py` で `analysis_results.scores` に保存
    - _要件: 2.4_
  - [x] 2.4 フロントエンド — ScoreCard コンポーネント
    - `client/src/entities/company/ui/ScoreCard.tsx` 新規作成
    - 5観点のスコアバー（Mantine Progress）+ 根拠テキスト
    - LLM推定値である旨の注記
    - _要件: 3.2, 3.3, 2.5_

- [x] 3. チェックポイント — 全テスト通過確認
  - 全テストが通過していることを確認する。問題があればユーザーに確認する。
