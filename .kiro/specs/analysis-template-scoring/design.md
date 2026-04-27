# 設計書: analysis-template-scoring

## 概要

テンプレート別プロンプト分岐（`get_summary_system(template)`）とStage 2 LLM呼び出しでのスコア同時生成。スキーマ変更は最小限で、`AnalysisRequest` に `template` フィールド、`AnalysisResponse` に `scores` フィールドを追加する。

## アーキテクチャ

```
POST /api/analysis { company_url, template }
  └── AnalysisService.analyze_company()
        ├── Stage 1: extraction_agent（テンプレート非依存）
        └── Stage 2: summary_agent
              ├── get_summary_system(template) でプロンプト分岐
              └── scores（5観点）も同時生成
                    └── analysis_results.scores (JSONB) に保存
```

## コンポーネントとインターフェース

### `server/src/analysis/prompts.py`（変更）

```python
TEMPLATE_INSTRUCTIONS = {
    "general": "全項目を均等に分析してください。",
    "job_hunting": "企業文化・採用情報・成長性・安定性を重点的に分析し、就活生へのアドバイスセクションを追加してください。",
    "investment": "財務指標・成長率・競合比較・リスク要因を重点的に分析し、投資判断サマリーを追加してください。",
    "competitor": "事業領域・プロダクト・差別化要因・市場ポジションを重点的に分析し、競合マップを追加してください。",
    "partnership": "技術力・事業シナジー・財務健全性を重点的に分析し、提携可能性サマリーを追加してください。",
}

def get_summary_system(template: str = "general") -> str:
    instruction = TEMPLATE_INSTRUCTIONS.get(template, TEMPLATE_INSTRUCTIONS["general"])
    return f"{SUMMARY_SYSTEM_BASE}\n\n{instruction}\n\n{SCORING_INSTRUCTION}"
```

### `server/src/analysis/schemas.py`（変更）

```python
class ScoreItem(BaseModel):
    score: int  # 0〜100
    reason: str

class ScoreData(BaseModel):
    financial_health: ScoreItem
    growth_potential: ScoreItem
    competitive_advantage: ScoreItem
    risk_level: ScoreItem
    information_transparency: ScoreItem

class AnalysisRequest(BaseModel):
    company_url: str
    force_refresh: bool = False
    template: str = "general"

class AnalysisResponse(BaseModel):
    # 既存フィールド...
    scores: ScoreData | None = None
    template: str = "general"
```

### フロントエンド

#### `client/src/features/company-search/ui/CompanySearchForm.tsx`（変更）

```tsx
<Select
  label="分析の目的"
  data={[
    { value: "general", label: "総合分析（デフォルト）" },
    { value: "job_hunting", label: "就活・転職リサーチ" },
    { value: "investment", label: "投資リサーチ" },
    { value: "competitor", label: "競合調査" },
    { value: "partnership", label: "提携先調査" },
  ]}
  value={template}
  onChange={setTemplate}
/>
```

#### ScoreCard コンポーネント（新規）

`client/src/entities/company/ui/ScoreCard.tsx`

```tsx
// 5観点のスコアバー（Progress）+ 根拠テキスト
// スコアはLLMによる推定値である旨の注記
```

## データモデル

### ScoreData（JSONB）
`docs/database-design.md` の `scores` JSONB スキーマに準拠：

```json
{
  "financial_health":          { "score": 75, "reason": "..." },
  "growth_potential":          { "score": 80, "reason": "..." },
  "competitive_advantage":     { "score": 70, "reason": "..." },
  "risk_level":                { "score": 40, "reason": "..." },
  "information_transparency":  { "score": 85, "reason": "..." }
}
```

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。*

Property 1: スコア範囲の不変条件
*For any* 分析結果に対して、5観点の全スコアは 0 以上 100 以下の整数である
**Validates: Requirements 2.1**

Property 2: テンプレートのデフォルト値
*For any* `template` パラメータを省略したリクエストに対して、レスポンスの `template` フィールドは `"general"` である
**Validates: Requirements 1.2**

Property 3: スコアフィールドの完全性
*For any* 分析結果に対して、`scores` オブジェクトは5つの観点（financial_health, growth_potential, competitive_advantage, risk_level, information_transparency）を全て含む
**Validates: Requirements 2.1, 2.2**

## エラーハンドリング

| エラー種別 | 対応 |
|-----------|------|
| 不正なテンプレートID | `general` にフォールバック |
| スコア生成失敗 | `scores: null` でレスポンス返却 |

## テスト戦略

### ユニットテスト
- `get_summary_system()` が各テンプレートで異なるプロンプトを返すことを確認
- 不正なテンプレートIDで `general` にフォールバックすることを確認

### プロパティベーステスト
- Property 1: 任意の分析結果に対してスコアが 0〜100 の範囲内であることを検証（最低100回）
- Property 2: template 省略時のデフォルト値を検証
- Property 3: 任意の分析結果に対してスコアフィールドの完全性を検証
- タグ形式: `Feature: analysis-template-scoring, Property {N}: {property_text}`
