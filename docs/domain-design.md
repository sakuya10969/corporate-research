# ドメイン設計

## ドメイン概要

企業分析エージェントのコアドメインは「企業分析」である。ユーザーが企業名を入力し、システムが情報収集・整理・AI分析を経て構造化された分析結果を返す、というフローが中心となる。

## エンティティ

### AnalysisRequest（分析リクエスト）

ユーザーからの分析依頼を表す。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| company_name | str | 分析対象の企業名 |

MVP ではシンプルに企業名のみ。将来的には分析観点（テンプレート）や追加パラメータを拡張可能。

### CompanyInfo（企業情報）

情報収集モジュールが収集・前処理した企業情報を表す。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| company_name | str | 企業名 |
| sources | list[SourceInfo] | 収集元情報のリスト（カテゴリ・メタデータ付き） |
| raw_content | str | LLM向けに整形済みのコンテキスト文字列（カテゴリ別グルーピング） |
| classified_sections | list[dict] | カテゴリ分類済みセクション一覧 |

### SourceInfo（収集元情報）

個々の情報ソースを表す。ページ分類・メタデータ付き。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| url | str | 収集元URL |
| title | str | ページタイトル |
| content | str | 構造保持抽出テキスト（表・リスト構造維持） |
| category | str | ページカテゴリ（会社概要/事業内容/IR・財務情報/プレスリリース・ニュース/採用情報/その他） |
| meta | dict | OGP・meta description 等のメタデータ |

### AnalysisResult（分析結果）

AI による分析結果を表す。APIレスポンスとしてフロントエンドに返却される。2段階パイプライン（構造化抽出 → 要約生成）で生成される。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| company_name | str | 企業名 |
| structured | StructuredData | 構造化抽出結果（企業プロフィール、事業領域、製品、財務、ニュース、リスク） |
| summary | SummaryData | 要約・SWOT分析・競合推定・今後の展望 |
| sources | list[SourceInfo] | 参照した情報ソース（カテゴリ付き） |
| raw_sources | list[RawSource] | 生テキストソース |

## サービス

### AnalysisService（分析サービス）

分析フロー全体のオーケストレーションを担当する。2段階パイプラインで処理する。

責務：
- 分析リクエストの受付
- CollectorService を呼び出して情報収集（サイトマップ探索・ページ分類付き）
- Stage 1: LLM で構造化抽出（企業プロフィール、事業領域、財務、ニュース、リスク）
- Stage 2: LLM で要約・SWOT・競合推定・展望を生成
- 結果を AnalysisResult として構造化して返却

```
analyze_company(request: AnalysisRequest) -> AnalysisResult
```

将来 LangGraph を導入する際は、このサービスのフロー制御部分をグラフに置き換える。

### CollectorService（情報収集サービス）

Web 上の企業情報を収集・前処理・分類する。

責務：
- 入力の正規化（企業名 → 公式サイトURL推定、URL入力対応）
- サイトマップ探索（/sitemap.xml）またはトップページからの内部リンク探索（深さ1-2）
- 各ページの取得・構造保持テキスト抽出・ページカテゴリ分類
- Google検索による補完収集
- 前処理（ボイラープレート除去、正規化、LLM向けコンテキスト整形）
- 収集結果を CompanyInfo として構造化

```
collect_company_info(company_name: str) -> CompanyInfo
```

## モジュールとエンティティの対応

| モジュール | 管理するエンティティ | サービス |
|-----------|-------------------|---------|
| analysis | AnalysisRequest, AnalysisResult, StructuredData, SummaryData | AnalysisService |
| collector | CompanyInfo, SourceInfo | CollectorService |
| shared | 設定、LLMクライアント、共通例外、HTTPクライアント、テキスト前処理 | — |

## データフロー

```
AnalysisRequest
    ↓
AnalysisService.analyze_company()
    ↓
CollectorService.collect_company_info()
  ├── URL正規化（企業名 → 公式サイトURL推定）
  ├── サイトマップ探索 or 内部リンク探索
  ├── ページ取得・構造保持テキスト抽出・カテゴリ分類
  ├── Google検索補完
  └── 前処理・LLM向けコンテキスト整形
    ↓
CompanyInfo（分類済み・前処理済み）
    ↓
Stage 1: LLM 構造化抽出 → StructuredData
    ↓
Stage 2: LLM 要約・SWOT生成 → SummaryData
    ↓
AnalysisResult
```

## 将来の拡張ポイント

| 拡張 | 影響 |
|------|------|
| 分析履歴管理 | AnalysisResult の永続化、新規エンティティ AnalysisHistory の追加 |
| 分析テンプレート | AnalysisRequest にテンプレートIDを追加、AnalysisTemplate エンティティ |
| 比較分析 | ComparisonRequest / ComparisonResult エンティティの追加 |
| LangGraph 化 | AnalysisService のフロー制御をグラフに置き換え。エンティティは変更不要 |
