# 未着手タスク一覧

参照ドキュメント:
- [specs.md](./specs.md) — 機能仕様
- [api-design.md](./api-design.md) — APIデザイン・スキーマ定義
- [domain-design.md](./domain-design.md) — ドメイン設計
- [history.md](./history.md) — 完了タスク履歴

---

## Phase 5: V1 — データ永続化基盤

### T-018: DB スキーマ定義 & マイグレーション（F-005）

- 対象: `server/alembic/`, `server/src/db/`
- 内容:
  - `companies` テーブル（company_id, url, name, normalized_domain, created_at）
  - `analysis_results` テーブル（result_id, company_id, structured JSONB, summary JSONB, sources JSONB, markdown_page, created_at）
  - `analysis_runs` テーブル（run_id, company_id, result_id, run_type, status, started_at, completed_at, error_message）
  - Alembic マイグレーションファイル作成
  - pgvector extension 有効化（docker/init.sql 済み）
- 参照: specs.md F-005、domain-design.md

### T-019: DB クライアント & リポジトリ層（F-005）

- 対象: `server/src/shared/db.py`, `server/src/company/repository.py`
- 内容:
  - SQLAlchemy async engine / session 設定
  - `CompanyRepository` — upsert, find_by_url
  - `AnalysisResultRepository` — save, find_latest_by_company
  - `AnalysisRunRepository` — create, update_status
- 参照: specs.md F-005

### T-020: 分析サービスへの永続化統合（F-005）

- 対象: `server/src/analysis/service.py`
- 内容:
  - 分析完了後に `analysis_results` / `analysis_runs` へ保存
  - 同一 URL の再入力時に過去データを返却 or 再分析を選択できるロジック
  - `AnalysisResponse` に `is_cached: bool`, `analyzed_at: datetime` を追加
- 参照: specs.md F-005

### T-021: 永続化対応 API エンドポイント更新（F-005）

- 対象: `server/src/analysis/router.py`, `server/src/analysis/schemas.py`
- 内容:
  - `POST /api/analysis` に `force_refresh: bool = False` パラメータ追加
  - キャッシュヒット時は DB から返却（LLM 呼び出しなし）
  - `GET /api/companies/{company_id}/history` — 分析履歴一覧（F-008 前提）
- 参照: specs.md F-005, F-008

### T-022: フロントエンド — キャッシュ通知 UI（F-005）

- 対象: `client/src/features/company-search/`, `client/src/widgets/analysis-result/`
- 内容:
  - 過去分析済みの場合に「前回分析: {日時}」バナーを表示
  - 「最新情報で更新する」ボタンで `force_refresh=true` 再送信
- 参照: specs.md F-005

---

## Phase 6: V1 — 分析履歴管理（F-008）

### T-023: 分析履歴 API（F-008）

- 対象: `server/src/analysis/router.py`
- 内容:
  - `GET /api/companies/{company_id}/runs` — 実行履歴一覧（run_type, status, started_at, completed_at）
  - `GET /api/analysis/{result_id}` — 過去の分析結果取得
- 参照: specs.md F-008

### T-024: フロントエンド — 分析履歴タブ（F-008）

- 対象: `client/src/widgets/analysis-result/`
- 内容:
  - 分析結果ページに「分析履歴」タブ追加
  - 実行日時・種別（initial / refresh / deep_research）・状態（completed / failed）一覧表示
  - 過去の結果を選択して表示切り替え
- 参照: specs.md F-008

---

## Phase 7: V1 — ダウンロード機能（F-009）

### T-025: サーバーサイド PDF / Word 生成エンドポイント（F-009）

- 対象: `server/src/download/`, `server/src/analysis/router.py`
- 内容:
  - `uv add weasyprint python-docx` で依存追加
  - `GET /api/analysis/{result_id}/download?format=pdf` — WeasyPrint で HTML→PDF 変換して返却
  - `GET /api/analysis/{result_id}/download?format=docx` — python-docx で Word 生成して返却
  - PDF: `markdown_page` を HTML に変換 → Noto Sans JP フォント適用 → WeasyPrint でレンダリング
  - Word: python-docx で見出し・表・リスト構造を持つ `.docx` を生成
  - レスポンス: `FileResponse` / `StreamingResponse` + `Content-Disposition: attachment`
  - ファイル名: `{企業名}_{YYYY-MM-DD}.pdf` / `.docx`
- 参照: specs.md F-009

### T-026: フロントエンド — PDF / Word ダウンロード UI（F-009）

- 対象: `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`
- 内容:
  - 「ダウンロード」ボタン（ドロップダウン）追加
  - PDF / Word の2択を表示
  - 選択後に `/api/analysis/{result_id}/download?format=pdf|docx` へリクエストしてブラウザダウンロード
  - ダウンロード中はローディング状態表示
- 参照: specs.md F-009

---

## Phase 8: V1 — 差分更新分析（F-006）

### T-027: ページハッシュ管理（F-006）

- 対象: `server/src/collector/service.py`, `server/src/db/`
- 内容:
  - `page_snapshots` テーブル（url, content_hash, etag, last_modified, fetched_at）
  - 前回取得時のハッシュと比較し、変化があったページのみ再取得
  - ETag / Last-Modified ヘッダー対応
- 参照: specs.md F-006

### T-028: 差分分析サービス（F-006）

- 対象: `server/src/analysis/service.py`
- 内容:
  - `run_type=refresh` 時は変化ページのみを対象に再分析
  - 差分レポート生成（新規ニュース・変更プロフィール・新規プロダクト・財務変化）
  - `diff_report` フィールドを AnalysisResponse に反映
- 参照: specs.md F-006

### T-029: フロントエンド — 差分表示（F-006）

- 対象: `client/src/widgets/analysis-result/`
- 内容:
  - 変更があったセクションを強調表示（バッジ or ボーダー色変更）
  - 差分レポートセクションの追加
- 参照: specs.md F-006

---

## Phase 9: V1 — 深掘り分析（F-007）

### T-030: 深掘り分析 API（F-007）

- 対象: `server/src/analysis/`, `server/src/deep_research/`
- 内容:
  - `POST /api/companies/{company_id}/deep-research` — 質問を受け付けて回答
  - 保存済みデータを優先使用、不足時のみ追加収集
  - openai-agents の Agent ループで状態付きワークフロー実装
  - 質問・回答履歴を DB に保存
- 参照: specs.md F-007

### T-031: フロントエンド — 深掘り質問 UI（F-007）

- 対象: `client/src/widgets/analysis-result/`
- 内容:
  - 分析結果ページ下部に「深掘り質問」入力欄追加
  - 質問・回答を会話形式で表示
  - ローディング中はストリーミング表示（任意）
- 参照: specs.md F-007

---

## Phase 10: V2 — 分析テンプレート & スコアリング（F-010, F-014）

### T-032: 分析テンプレート（F-010）

- 対象: `server/src/analysis/prompts.py`, `server/src/analysis/schemas.py`
- 内容:
  - `template: Literal["general","job_hunting","investment","competitor","partnership"] = "general"` を AnalysisRequest に追加
  - テンプレート別プロンプト分岐（EXTRACTION_SYSTEM / SUMMARY_SYSTEM をテンプレートで切り替え）
- 参照: specs.md F-010

### T-033: 分析スコアリング（F-014）

- 対象: `server/src/analysis/service.py`, `server/src/analysis/schemas.py`
- 内容:
  - Stage 2（要約生成）の LLM 呼び出しでスコアも同時生成
  - `ScoreData`（財務健全性・成長性・競合優位性・リスク度・情報透明性: 各 0〜100 + 根拠文）
  - AnalysisResponse に `scores: ScoreData` 追加
  - フロントエンド: レーダーチャート表示（Recharts 等）
- 参照: specs.md F-014

---

## Phase 11: V2 — 企業名検索・シェア・比較（F-011, F-012, F-013）

### T-034: 企業名検索 URL 補完（F-011）

- 対象: `server/src/search/`, `client/src/features/company-search/`
- 内容:
  - `GET /api/search?q={企業名}` — DuckDuckGo Instant Answer API で公式 URL 候補を最大5件返却
  - フロントエンド: 入力フォームにオートコンプリート候補表示
- 参照: specs.md F-011

### T-035: 分析結果シェア（F-012）

- 対象: `server/src/analysis/router.py`, `client/src/app/share/`
- 内容:
  - `GET /api/share/{share_id}` — 公開分析結果取得（認証不要）
  - share_id: analysis_id の先頭8文字
  - フロントエンド: `/share/{share_id}` ページ（読み取り専用）+ OGP メタタグ
  - 「シェア」ボタン → URL クリップボードコピー
- 参照: specs.md F-012

### T-036: 複数企業比較（F-013）

- 対象: `server/src/analysis/`, `client/src/app/compare/`
- 内容:
  - `POST /api/compare` — 最大3社の分析を並行実行して比較レスポンス返却
  - AIによる比較コメント生成
  - フロントエンド: 比較モード UI（横並びテーブル・SWOT カード・レーダーチャート）
  - URL パラメータ共有（`?compare=url1,url2,url3`）
- 参照: specs.md F-013

---

## タスク依存関係

```
T-018 (DB スキーマ)
  ↓
T-019 (リポジトリ層) ← T-018
  ↓
T-020 (永続化統合) ← T-019
T-021 (API 更新) ← T-019
T-022 (キャッシュ UI) ← T-021
  ↓
T-023 (履歴 API) ← T-019
T-024 (履歴 UI) ← T-023
T-025 (PDF/Word 生成 API) ← T-020
T-026 (PDF/Word DL UI) ← T-025
  ↓
T-027 (ページハッシュ) ← T-019
T-028 (差分分析) ← T-020, T-027
T-029 (差分 UI) ← T-028
  ↓
T-030 (深掘り API) ← T-020
T-031 (深掘り UI) ← T-030
  ↓
T-032 (テンプレート) ← T-020
T-033 (スコアリング) ← T-032
T-034 (企業名検索) ← T-020
T-035 (シェア) ← T-020
T-036 (比較) ← T-020, T-035
```
