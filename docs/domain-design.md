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

情報収集モジュールが収集した生の企業情報を表す。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| company_name | str | 企業名 |
| sources | list[SourceInfo] | 収集元情報のリスト |
| raw_content | str | 収集した生テキスト（結合済み） |

### SourceInfo（収集元情報）

個々の情報ソースを表す。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| url | str | 収集元URL |
| title | str | ページタイトル |
| content | str | 抽出テキスト |

### AnalysisResult（分析結果）

AI による分析結果を表す。APIレスポンスとしてフロントエンドに返却される。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| company_name | str | 企業名 |
| summary | str | 企業概要の要約 |
| business_description | str | 事業内容の説明 |
| key_findings | list[str] | 主要な発見事項 |
| sources | list[SourceInfo] | 参照した情報ソース |

MVP ではこの構造で開始し、将来的にセクション（財務、競合、市場など）を追加拡張する。

## サービス

### AnalysisService（分析サービス）

分析フロー全体のオーケストレーションを担当する。

責務：
- 分析リクエストの受付
- CollectorService を呼び出して情報収集
- 収集情報を LangChain チェーンに渡して要約・分析
- 結果を AnalysisResult として構造化して返却

```
analyze_company(request: AnalysisRequest) -> AnalysisResult
```

将来 LangGraph を導入する際は、このサービスのフロー制御部分をグラフに置き換える。

### CollectorService（情報収集サービス）

Web 上の企業情報を収集・パースする。

責務：
- 企業名をもとに検索・情報収集
- HTML のパース・テキスト抽出
- 収集結果を CompanyInfo として構造化

```
collect_company_info(company_name: str) -> CompanyInfo
```

## モジュールとエンティティの対応

| モジュール | 管理するエンティティ | サービス |
|-----------|-------------------|---------|
| analysis | AnalysisRequest, AnalysisResult | AnalysisService |
| collector | CompanyInfo, SourceInfo | CollectorService |
| shared | 設定、LLMクライアント、共通例外 | — |

## データフロー

```
AnalysisRequest
    ↓
AnalysisService.analyze_company()
    ↓
CollectorService.collect_company_info()
    ↓
CompanyInfo
    ↓
LangChain チェーン（要約・分析）
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
