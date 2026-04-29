# 技術仕様

各機能の内部処理・データモデル・アーキテクチャ方針を定義する。
ユーザー視点の機能一覧は `features.md` を、APIエンドポイント定義は `api-design.md` を参照。

---

## 実装済み仕様

### S-001: 情報収集パイプライン（F-001, F-002）

#### 入力バリデーション

| レイヤ | ツール | ルール |
|--------|-------|--------|
| フロントエンド | Valibot | URL必須、`http://` or `https://` 始まり、空白のみ不可 |
| バックエンド | Pydantic | 同上（信頼境界） |

#### 収集処理

- `httpx` + `BeautifulSoup` + `lxml` で企業サイトの公開ページを非同期クロール
- サイトマップ探索 → 内部リンク探索の順で最大15ページを取得
- Google検索は使用しない。企業サイトの一次情報のみ
- 収集したページはカテゴリ分類される（企業情報、IR、ニュース、採用等）

#### AI分析（2段階処理）

| Stage | 処理 | 入力 | 出力 |
|-------|------|------|------|
| Stage 1: 構造化抽出 | 収集テキストから定型情報を抽出 | raw_sources | StructuredData |
| Stage 2: 要約・分析 | 構造化データをもとに要約・SWOT等を生成 | StructuredData | SummaryData + ScoreData |

- openai-agents SDK（`Agent` + `Runner.run()`）で Azure OpenAI を呼び出す
- `ModelSettings(temperature=0)` で再現性を確保
- プロンプトは `prompts.py` にプレーン文字列定数として定義

### S-002: データ永続化（F-005）

#### データモデル

| テーブル | 主キー | 役割 |
|---------|--------|------|
| `companies` | `company_id` (UUID) | 企業マスタ（URL、社名、正規化ドメイン） |
| `analysis_results` | `result_id` (UUID) | 分析結果（structured/summary を JSONB で保存） |
| `analysis_runs` | `run_id` (UUID) | 分析実行履歴（種別・状態・開始/完了日時） |
| `page_snapshots` | `snapshot_id` (UUID) | ページスナップショット（content_hash, etag, last_modified） |

#### キャッシュ戦略

- 同一URLの再入力時、DBに保存済みの最新結果を返却する
- `force_refresh=true` パラメータで強制再分析が可能
- 企業は `company_id` で一意に管理し、URLの正規化（末尾スラッシュ等）で同一企業を判定

#### 設計方針

- PostgreSQL を正本データストアとして使用
- 構造化データ（structured / summary）はJSONBカラムで保存
- 企業は `company_id` で一意に管理し、比較機能等で再利用

### S-003: 差分更新（F-006）

#### 変更検知の仕組み

- ページごとに `content_hash`（SHA-256）を `page_snapshots` テーブルに保持
- `fetched_at` で前回取得日時を管理
- HTTPヘッダーに ETag / Last-Modified がある場合はそれを優先利用
- ニュース・IR・採用ページは変化頻度が高いため優先的に更新対象

#### 差分レポート生成

- `run_type=refresh` 時に前回の `structured` データと比較
- `generate_diff_report` 関数で差分を検出し、Markdownレポートとして出力
- 変更がなかった場合は空の差分レポートを返却

### S-004: 深掘り分析（F-007）

#### データモデル

| テーブル | 役割 |
|---------|------|
| `deep_research_sessions` | セッション管理（company_id に紐づく） |
| `deep_research_messages` | 質問・回答の履歴（session_id に紐づく） |

#### 処理フロー

- openai-agents の `Agent` ループで回答を生成
- 保存済みの `structured` + `summary` をコンテキストとして使用
- 保存データだけでは不足する場合、追加収集を自動実行
- セッションIDを保持して継続会話に対応

### S-005: ダウンロード生成（F-009）

| フォーマット | 生成方法 |
|------------|---------|
| PDF | `markdown_page` → HTML変換 → WeasyPrint でPDF生成。Noto Sans JP フォント使用 |
| Word | python-docx で構造化ドキュメント生成（見出し・表・リスト対応） |

- `GET /api/analysis/{result_id}/download?format=pdf|docx`
- `Content-Disposition: attachment` でブラウザダウンロードを強制

### S-006: 分析テンプレート（F-010）

#### テンプレート制御

- テンプレートはプロンプトレベルで制御する（スキーマ変更なし）
- `get_summary_system(template)` でテンプレート別にStage 2のシステムプロンプトを分岐
- `AnalysisRequest` の `template` フィールドで指定（省略時は `general`）

#### テンプレートIDと出力の違い

| ID | 追加出力 |
|----|---------|
| `general` | なし（全項目均等） |
| `job_hunting` | 「就活生へのアドバイス」セクション追加 |
| `investment` | 投資判断サマリー追加 |
| `competitor` | 競合マップ追加 |
| `partnership` | 提携可能性サマリー追加 |

### S-007: 企業名検索（F-011）

- DuckDuckGo Instant Answer API（無料・APIキー不要）を使用
- `GET /api/search?q={企業名}` で最大5件の候補を返却
- フロントエンド: Mantine Autocomplete + `useDebouncedValue` でオートコンプリート

### S-008: 分析結果シェア（F-012）

- `POST /api/analysis/{result_id}/share` で `share_id` を生成（UUID先頭8文字）
- `GET /api/share/{share_id}` で認証不要の公開取得
- Next.js App Router の `generateMetadata` でOGPメタタグを動的生成
- 共有URLの有効期限はなし（永続）

### S-009: 複数企業比較（F-013）

- `POST /api/compare` で最大3社を `asyncio.gather` で並行分析
- 各社の分析結果をまとめてLLMに渡し、比較サマリーを生成（`COMPARISON_SYSTEM` プロンプト）
- `comparison_sessions` テーブルに保存
- 保存済みデータがある企業はキャッシュを再利用

### S-010: スコアリング（F-014）

- Stage 2のLLM呼び出しでスコアも同時生成（追加コスト最小化）
- `ScoreData`: 5観点 × `score`（0〜100整数）+ `reason`（根拠1〜2文）
- `AnalysisResponse` の `scores` フィールドとして返却

#### スコアの根拠データ

| 観点 | 主な根拠 |
|------|---------|
| 財務健全性 | financials |
| 成長性 | outlook, news |
| 競合優位性 | swot.strengths, competitors |
| リスク度 | risks |
| 情報透明性 | sources の数・カテゴリ多様性 |

### S-011: ユーザー認証（F-015）

#### 認証フロー

| 系統 | 方式 |
|------|------|
| Next.js 内部 | Clerk Session Cookie。Server Component / Route Handler は Cookie ベースで認証状態を取得 |
| FastAPI 連携 | Clerk JWT を Authorization ヘッダーに付与。FastAPI 側で JWKS 検証 |

#### データモデル

| テーブル | 主キー | カラム |
|---------|--------|--------|
| `users` | `clerk_user_id` (TEXT) | email, display_name, created_at, updated_at |

#### JWT検証

- `python-jose` で Clerk JWKS から公開鍵を取得（TTL付きキャッシュ）
- 署名・`exp`・`iss` を検証。失敗時は HTTP 401
- `get_current_user_id` 依存性で `sub` クレーム（Clerk User ID）を抽出

#### ユーザー同期

- ログイン後に `POST /api/users/sync` で upsert
- `clerk_user_id` が存在しない場合は INSERT、存在する場合は UPDATE
- 冪等性を保証（同一入力で複数回実行しても結果は同一）

---

## 未実装仕様

### S-012: RAG統合（将来）

- 社内ナレッジベースを検索拡張生成（RAG）で分析コンテキストに統合
- pgvector による embedding は補助的な検索用途に限定し、業務データの正本はリレーショナルDBで持つ
- 深掘り質問時に社内情報も参照して回答を生成

---

## アーキテクチャ方針

### LLM基盤

- openai-agents SDK（`Agent` + `Runner.run()`）を使用
- Azure OpenAI 経由で呼び出し（`AsyncAzureOpenAI` + `set_default_openai_client`）
- LangChain は廃止済み

### LangGraphの位置づけ

現時点では未導入。将来的に以下の用途で段階的に導入する：

- 保存済み企業データを前提とした再分析・差分更新の高度化
- 深掘り質問時の状態付きワークフロー（途中再開・追加収集の制御）
- チェックポイントを活かした長時間処理の管理

毎回フルスクレイピング → フル再分析するだけの用途には使用しない。

### 避けるべき設計

- 毎回URLを入力するたびにフルスクレイピング → フル再分析する設計
- ベクトルDB / embedding側だけに企業の正本状態を持たせる設計
- 分析結果を毎回RAGで再生成し、永続化しない設計
