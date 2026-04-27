# 設計書: company-analysis-core

## 概要

企業分析エージェントのMVPコア機能の技術設計。フロントエンドはNext.js + Mantine + FSD構成、バックエンドはFastAPI + openai-agents SDKによる2段階LLMパイプラインで実装する。

## アーキテクチャ

```
[フロントエンド: Next.js App Router + FSD]
  app/page.tsx
    └── features/company-search (CompanySearchForm)
    └── widgets/analysis-result (AnalysisResult)
          └── entities/company (CompanyCard)

[バックエンド: FastAPI モジュラーモノリス]
  POST /api/analysis
    └── analysis/router.py
          └── analysis/service.py (AnalysisService)
                └── collector/service.py (CollectorService)
                └── analysis/prompts.py (Stage1/Stage2 プロンプト)
```

## コンポーネントとインターフェース

### バックエンド

#### `server/src/analysis/router.py`
- `POST /api/analysis` — AnalysisRequest を受け取り AnalysisResponse を返す
- `GET /api/health` — ヘルスチェック

#### `server/src/analysis/service.py`
```python
async def analyze_company(request: AnalysisRequest, session: AsyncSession) -> AnalysisResponse:
    # 1. CollectorService.collect_company_info() で情報収集
    # 2. Stage 1: extraction_agent で構造化抽出
    # 3. Stage 2: summary_agent で要約・SWOT生成
    # 4. Markdownレポート生成
    # 5. AnalysisResponse を返す
```

#### `server/src/collector/service.py`
```python
async def collect_company_info(company_url: str) -> CompanyInfo:
    # 1. URL正規化
    # 2. /sitemap.xml 探索 → なければ内部リンク探索
    # 3. 各ページ取得・HTMLパース・カテゴリ分類
    # 4. LLM向けコンテキスト整形
```

#### `server/src/analysis/prompts.py`
- `EXTRACTION_SYSTEM` / `EXTRACTION_HUMAN` — Stage 1 プロンプト（構造化抽出）
- `SUMMARY_SYSTEM` / `SUMMARY_HUMAN` — Stage 2 プロンプト（要約・SWOT）

#### `server/src/shared/llm.py`
```python
def init_llm() -> None:
    # AsyncAzureOpenAI クライアントを set_default_openai_client() で注入
```

### フロントエンド

#### `client/src/features/company-search/`
- `model/schema.ts` — Valibot スキーマ（URL必須・http/https必須・空白不可）
- `ui/CompanySearchForm.tsx` — TextInput + Button、ローディング状態、バリデーションエラー表示

#### `client/src/widgets/analysis-result/`
- `ui/AnalysisResult.tsx` — スケルトンUI・エラー表示・結果カード表示

#### `client/src/entities/company/`
- `ui/CompanyCard.tsx` — 汎用カードコンポーネント

#### `client/src/shared/api/`
- `instance.ts` — Axios インスタンス（baseURL: NEXT_PUBLIC_API_URL）
- `generated/` — Orval 自動生成コード（手動編集禁止）

## データモデル

### AnalysisRequest
```python
class AnalysisRequest(BaseModel):
    company_url: str  # http/https で始まるURL
```

### AnalysisResponse
```python
class AnalysisResponse(BaseModel):
    company_url: str
    structured: StructuredData
    summary: SummaryData
    sources: list[SourceInfo]
    raw_sources: list[RawSource]
    markdown_page: str
    diff_report: str | None
```

### StructuredData
```python
class StructuredData(BaseModel):
    company_profile: CompanyProfile
    business_domains: list[str]
    products: list[str]
    financials: Financials
    news: list[NewsItem]
    risks: list[RiskItem]
```

### SummaryData
```python
class SummaryData(BaseModel):
    overview: str
    business_model: str
    swot: SwotAnalysis
    risks: list[str]
    competitors: list[str]
    outlook: str
```

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。プロパティはヒューマンリーダブルな仕様と機械検証可能な正確性保証の橋渡しをする。*

Property 1: URLバリデーション — 無効入力の拒否
*For any* 文字列入力に対して、`http://` または `https://` で始まらない文字列はバリデーターによって拒否される
**Validates: Requirements 1.2, 1.3, 1.4**

Property 2: 空白入力の拒否
*For any* 空白文字のみで構成された文字列は、バリデーターによって送信が拒否される
**Validates: Requirements 1.4**

Property 3: 分析結果の構造完全性
*For any* 有効な企業URLに対して、分析結果は structured・summary・sources・markdown_page フィールドを全て含む
**Validates: Requirements 2.4, 2.5**

Property 4: エラー時のレスポンス形式
*For any* 分析エラーに対して、レスポンスは `{"detail": "string"}` 形式のエラーボディを含む
**Validates: Requirements 2.6, 2.7**

## エラーハンドリング

| エラー種別 | HTTPステータス | 説明 |
|-----------|--------------|------|
| バリデーションエラー | 400 | URLが無効 |
| 情報収集失敗 | 500 | CollectionError |
| AI処理失敗 | 500 | AnalysisError |
| 外部サービス不可 | 503 | ExternalServiceError |

`server/src/shared/exceptions.py` に共通例外を定義し、FastAPI の exception handler で HTTP レスポンスに変換する。

## テスト戦略

### ユニットテスト
- Valibot スキーマのバリデーションロジック（有効URL・無効URL・空白）
- CollectorService のURL正規化・サイトマップ解析
- AnalysisService のレスポンス構造検証

### プロパティベーステスト
- Property 1, 2: Hypothesis で任意の文字列を生成し、バリデーターが正しく拒否することを検証（最低100回）
- Property 3: 任意の有効URLに対して分析結果の必須フィールドが全て存在することを検証
- タグ形式: `Feature: company-analysis-core, Property {N}: {property_text}`
