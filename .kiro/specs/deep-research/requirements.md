# 要件定義: deep-research

## はじめに

保存済みの企業データをもとに自由文で追加質問できる深掘り分析機能（F-007）。openai-agents SDKのAgentループを使用し、質問・回答を会話形式で表示する。data-persistence スペックの実装が前提。

## 用語集

- **System**: 企業分析エージェント全体
- **DeepResearchService**: 深掘り分析サービス
- **DeepResearchSession**: 深掘り分析セッション（`deep_research_sessions` テーブル）
- **DeepResearchMessage**: 深掘り質問・回答メッセージ（`deep_research_messages` テーブル）
- **DeepResearchTab**: 深掘り分析タブUIコンポーネント

## 要件

### 要件1: 深掘り分析 API（F-007）

**ユーザーストーリー:** ユーザーとして、保存済み企業データに対して自由文で追加質問したい。そうすることで、特定の観点から詳細な分析を得られる。

#### 受け入れ基準

1. WHEN `POST /api/companies/{company_id}/deep-research` が呼ばれた場合, THE DeepResearchService SHALL 保存済みの `structured` と `summary` データをコンテキストとして使用してAIが回答を生成する
2. WHEN 保存済みデータだけでは不足する場合, THE DeepResearchService SHALL 追加のWebページ収集を実行して回答を補完する
3. THE System SHALL 質問と回答を `deep_research_sessions` / `deep_research_messages` テーブルに保存する
4. WHEN `session_id` がリクエストに含まれる場合, THE DeepResearchService SHALL 既存セッションに会話を継続する
5. WHEN `session_id` がリクエストに含まれない場合, THE DeepResearchService SHALL 新規セッションを作成する
6. IF 指定された `company_id` が存在しない場合, THEN THE System SHALL HTTP 404エラーを返す

---

### 要件2: 深掘り分析UI（F-007）

**ユーザーストーリー:** ユーザーとして、分析結果ページで会話形式の深掘り質問UIを使いたい。そうすることで、直感的に追加質問できる。

#### 受け入れ基準

1. WHEN 分析結果が表示された場合, THE DeepResearchTab SHALL 分析結果ウィジェットに「深掘り分析」タブを表示する
2. WHEN 「深掘り分析」タブが選択された場合, THE DeepResearchTab SHALL Textareaと送信ボタンを表示する
3. WHEN 質問が送信された場合, THE DeepResearchTab SHALL 質問と回答を会話形式（交互）で表示する
4. WHILE 回答を生成中の場合, THE DeepResearchTab SHALL ローディング表示を行う
5. THE DeepResearchTab SHALL セッションIDを保持して継続会話に対応する
