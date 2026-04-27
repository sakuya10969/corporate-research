# 設計書: share

## 概要

`analysis_results` テーブルの `share_id` / `shared_at` カラムを使用したシェア機能。Next.js App Routerの `generateMetadata` でOGPを動的生成する。

## アーキテクチャ

```
POST /api/analysis/{result_id}/share
  └── analysis/router.py
        └── AnalysisResultRepository.find_by_id()
              └── share_id = str(uuid4())[:8]
                    └── AnalysisResultRepository.update_share_id()

GET /api/share/{share_id}
  └── analysis/router.py
        └── AnalysisResultRepository.find_by_share_id()

フロントエンド:
  client/src/app/share/[shareId]/page.tsx
    └── generateMetadata() → OGP メタタグ
    └── AnalysisResult（読み取り専用）
```

## コンポーネントとインターフェース

### `server/src/analysis/router.py`（追加エンドポイント）

```python
@router.post("/analysis/{result_id}/share")
async def share_analysis(
    result_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> ShareResponse:
    result = await AnalysisResultRepository.find_by_id(session, result_id)
    if not result:
        raise HTTPException(status_code=404)
    # 既にシェア済みの場合は既存 share_id を返す
    if result.share_id:
        return ShareResponse(share_id=result.share_id)
    share_id = str(uuid4())[:8]
    await AnalysisResultRepository.update_share_id(session, result_id, share_id)
    return ShareResponse(share_id=share_id)

@router.get("/share/{share_id}")
async def get_shared_analysis(
    share_id: str,
    session: AsyncSession = Depends(get_session)
) -> AnalysisResponse:
    result = await AnalysisResultRepository.find_by_share_id(session, share_id)
    if not result:
        raise HTTPException(status_code=404)
    return AnalysisResponse.from_orm(result)
```

### `server/src/analysis/schemas.py`（追加スキーマ）

```python
class ShareResponse(BaseModel):
    share_id: str
```

### フロントエンド

#### `client/src/app/share/[shareId]/page.tsx`（新規）

```tsx
export async function generateMetadata({ params }): Promise<Metadata> {
  const result = await fetch(`/api/share/${params.shareId}`).then(r => r.json());
  return {
    title: `${result.structured.company_profile.name} の企業分析レポート`,
    description: result.summary.overview.slice(0, 150),
    openGraph: {
      title: `${result.structured.company_profile.name} の企業分析レポート`,
      description: result.summary.overview.slice(0, 150),
      url: `https://app.example.com/share/${params.shareId}`,
      type: "article",
    },
  };
}

export default function SharePage({ params }) {
  // 読み取り専用の AnalysisResult 表示
}
```

#### `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`（変更）

```tsx
// シェアボタン追加
const handleShare = async () => {
  const res = await fetch(`/api/analysis/${resultId}/share`, { method: "POST" });
  const { share_id } = await res.json();
  const url = `${window.location.origin}/share/${share_id}`;
  await navigator.clipboard.writeText(url);
  // コピー完了フィードバック表示
};
```

## データモデル

既存の `analysis_results` テーブルの `share_id` / `shared_at` カラムを使用。専用テーブルは不要。

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。*

Property 1: share_id の形式
*For any* 生成された `share_id` は8文字の英数字文字列である
**Validates: Requirements 1.1**

Property 2: シェアの冪等性
*For any* 既にシェア済みの分析結果に対して再度シェアリクエストを送った場合、返却される `share_id` は最初のシェア時と同一である
**Validates: Requirements 1.5**

Property 3: シェアラウンドトリップ
*For any* 分析結果をシェアして生成された `share_id` で `GET /api/share/{share_id}` を呼ぶと、元の分析結果と同一のデータが返る
**Validates: Requirements 2.1**

## エラーハンドリング

| エラー種別 | HTTPステータス | 説明 |
|-----------|--------------|------|
| result_id が存在しない | 404 | AnalysisResult not found |
| share_id が存在しない | 404 | Shared result not found |

## テスト戦略

### ユニットテスト
- share_id が8文字であることを確認
- 存在しない result_id に対して 404 が返ることを確認

### プロパティベーステスト
- Property 1: 任意の result_id に対して share_id が8文字であることを検証（最低100回）
- Property 2: 同一 result_id への複数回シェアリクエストで同一 share_id が返ることを検証
- Property 3: シェア→取得のラウンドトリップで同一データが返ることを検証
- タグ形式: `Feature: share, Property {N}: {property_text}`
