# 要件定義: analysis-template-scoring

## はじめに

分析目的別テンプレート選択（F-010）と5観点スコアリング（F-014）を組み合わせた機能。テンプレートはプロンプトレベルで制御し、スコアはStage 2 LLM呼び出しと同時に生成する。

## 用語集

- **System**: 企業分析エージェント全体
- **AnalysisService**: 分析フローのオーケストレーションサービス
- **TemplateSelector**: テンプレート選択UIコンポーネント
- **ScoreCard**: スコア表示UIコンポーネント
- **Template**: 分析テンプレート（general / job_hunting / investment / competitor / partnership）
- **ScoreData**: 5観点スコアデータ（score + reason）

## 要件

### 要件1: 分析テンプレート選択（F-010）

**ユーザーストーリー:** 就活生・投資家・事業開発担当者として、分析の目的に応じたテンプレートを選択したい。そうすることで、自分の目的に合った観点で分析結果を得られる。

#### 受け入れ基準

1. THE System SHALL `general`, `job_hunting`, `investment`, `competitor`, `partnership` の5種類のテンプレートをサポートする
2. WHEN `template` パラメータが指定されない場合, THE AnalysisService SHALL `general` テンプレートをデフォルトとして使用する
3. WHEN テンプレートが指定された場合, THE AnalysisService SHALL 指定テンプレートに対応したプロンプトでStage 2 LLMを呼び出す
4. THE System SHALL テンプレートIDをレスポンスの `template` フィールドに含める

---

### 要件2: 分析スコアリング（F-014）

**ユーザーストーリー:** ユーザーとして、分析結果を数値スコアで直感的に把握したい。そうすることで、企業の強み・弱みを素早く理解できる。

#### 受け入れ基準

1. WHEN 分析が完了した場合, THE AnalysisService SHALL 財務健全性・成長性・競合優位性・リスク度・情報透明性の5観点を各0〜100でスコアリングする
2. THE System SHALL 各スコアに根拠テキスト（reason）を1〜2文で付与する
3. THE AnalysisService SHALL スコア生成をStage 2 LLM呼び出しと同時に実行する（追加LLM呼び出しなし）
4. THE System SHALL スコアを `analysis_results.scores` カラム（JSONB）に保存する
5. THE System SHALL スコアはLLMによる推定値であり客観的評価ではない旨をUIに明示する

---

### 要件3: テンプレート選択・スコア表示UI

**ユーザーストーリー:** ユーザーとして、フォームでテンプレートを選択し、分析結果でスコアを確認したい。そうすることで、目的に合った分析と結果の把握が容易になる。

#### 受け入れ基準

1. WHEN 企業URL入力フォームが表示された場合, THE TemplateSelector SHALL テンプレート選択Selectコンポーネントを表示する
2. WHEN 分析が完了した場合, THE ScoreCard SHALL 5観点のスコアバーと根拠テキストを表示する
3. THE ScoreCard SHALL スコアが0〜100の範囲であることを視覚的に表示する
