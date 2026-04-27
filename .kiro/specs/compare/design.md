# 設計書: compare

## 概要

`asyncio.gather` による並行分析と、COMPARISON_SYSTEMプロンプトを使用したAI比較サマリー生成。比較結果は `comparison_sessions` テーブルに保存する。フロントエンドは `/compare` ページで横並び比較テーブルを表示する。

## アーキテクチャ

```
POST /api/compare { company_urls: [...], template }
  └── analysis/router.py
        └── CompareService.compare(company_urls, template)
              ├── asyncio.gather(*[analyze_company(url) for url in company_urls])
              ├── LLM: COMPARISON_SYSTEM プロンプトで比較サマリー生成
              └── comparison_sessions テーブルに保存
                    └── CompareResponse

フロントエンド:
  client/src/app/compare/page.tsx
    └── URL入力 × 最大3
    └── ComparisonTable（横並び比較）
    └── 比較サマリー表示
```

## コンポーネントとインターフェース

### `server/src/analysis/compare_service.py`

```python
class CompareService:
    async def compare(
        self,
        company_urls: list[str],
        template: str,
        session: AsyncSession
    ) -> CompareResponse:
        # 1. asyncio.gather で並行分析
        results = await asyncio.gather(*[
            self.analysis_service.analyze_company(
                AnalysisRequest(company_url=url, template=template), session
            )
            for url in company_urls
        ])
        # 2. 比較サマリー生成
        comparison_summary = await self._generate_comparison_summary(results)
        # 3. comparison_sessions に保存
        await self._save_comparison(session, results, comparison_summary, template)
        return CompareResponse(
            companies=list(results),
            comparison_summary=comparison_summary,
            template=template
        )

    async def _generate_comparison_summary(
        self, results: list[AnalysisResponse]
    ) -> str:
        # COMPARISON_SYSTEM プロンプトで各社の summary を渡して比較コメント生成
```

### `server/src/analysis/router.py`（追加エンドポイント）

```python
@router.post("/compare")
async def compare_companies(
    request: CompareRequest,
    session: AsyncSession = Depends(get_session)
) -> CompareResponse:
    if not (2 <= len(request.company_urls) <= 3):
        raise HTTPException(status_code=400, detail="2〜3社のURLを指定してください")
    return await CompareService().compare(request.company_urls, request.template, session)
```

### `server/src/analysis/schemas.py`（追加スキーマ）

```python
class CompareRequest(BaseModel):
    company_urls: list[str]  # 2〜3件
    template: str = "general"

class CompareResponse(BaseModel):
    companies: list[AnalysisResponse]
    comparison_summary: str
    template: str
```

### `server/src/analysis/prompts.py`（追加）

```python
COMPARISON_SYSTEM = """
あなたは企業分析の専門家です。
以下の複数企業の分析結果を比較し、各企業の強み・弱み・差別化要因を自然文で説明してください。
どの企業がどの観点で優れているかを具体的に述べてください。
"""
```

### DBモデル（`server/src/db/models.py` 追加）

```python
class ComparisonSession(Base):
    __tablename__ = "comparison_sessions"
    comparison_id: UUID (PK)
    company_ids: list[UUID] (ARRAY)
    result_ids: list[UUID] (ARRAY)
    comparison_summary: dict | None (JSONB)
    template: str
    share_id: str | None (UNIQUE)
    shared_at: datetime | None
    llm_model: str | None
    tokens_used: int | None
    processing_ms: int | None
    created_at: datetime
    updated_at: datetime
```

### フロントエンド

#### `client/src/app/compare/page.tsx`（新規）

```tsx
// URL入力フィールド × 最大3（動的追加）
// 「比較分析する」ボタン → POST /api/compare
// ComparisonTable: 横並び比較（企業プロフィール・財務・SWOT・スコア）
// 比較サマリーテキスト表示
```

#### `client/src/app/page.tsx`（変更）

```tsx
// 「複数企業を比較する →」リンク追加
<Link href="/compare">複数企業を比較する →</Link>
```

## データモデル

### CompareRequest / CompareResponse
`docs/api-design.md` の `CompareRequest` / `CompareResponse` スキーマに準拠。

### comparison_sessions
`docs/database-design.md` の `comparison_sessions` テーブル定義に準拠。

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。*

Property 1: 比較件数の制約
*For any* `company_urls` リストに対して、2件未満または4件以上の場合は HTTP 400 エラーが返される
**Validates: Requirements 1.2, 1.3**

Property 2: 並行分析の結果完全性
*For any* 2〜3社の企業URLリストに対して、レスポンスの `companies` 配列の長さは入力 `company_urls` の長さと等しい
**Validates: Requirements 1.1, 1.6**

Property 3: 比較サマリーの存在
*For any* 有効な比較リクエストに対して、レスポンスの `comparison_summary` は空文字列でない
**Validates: Requirements 1.4**

## エラーハンドリング

| エラー種別 | HTTPステータス | 説明 |
|-----------|--------------|------|
| company_urls が2件未満または4件以上 | 400 | バリデーションエラー |
| いずれかの企業分析が失敗 | 500 | 並行分析エラー |
| 比較サマリー生成失敗 | 500 | LLM呼び出しエラー |

## テスト戦略

### ユニットテスト
- 1件・4件のURLリストに対して 400 が返ることを確認
- 2件・3件のURLリストで正常に処理されることを確認

### プロパティベーステスト
- Property 1: 任意の件数のURLリストに対してバリデーションが正しく動作することを検証（最低100回）
- Property 2: 任意の2〜3社URLリストに対して結果配列の長さが入力と一致することを検証
- Property 3: 任意の有効リクエストに対して比較サマリーが空でないことを検証
- タグ形式: `Feature: compare, Property {N}: {property_text}`
