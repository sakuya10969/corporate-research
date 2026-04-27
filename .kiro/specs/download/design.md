# 設計書: download

## 概要

WeasyPrint（PDF）とpython-docx（Word）を使用したサーバーサイドファイル生成。`markdown_page` フィールドを変換元として使用し、`GET /api/analysis/{result_id}/download?format=pdf|docx` エンドポイントで返却する。

## アーキテクチャ

```
GET /api/analysis/{result_id}/download?format=pdf|docx
  └── analysis/router.py
        └── AnalysisResultRepository.find_by_id()
              └── download/generator.py
                    ├── generate_pdf(markdown_page, company_name, date) → bytes
                    └── generate_docx(result, company_name, date) → bytes
```

## コンポーネントとインターフェース

### `server/src/download/generator.py`

```python
def generate_pdf(markdown_page: str, company_name: str, date: str) -> bytes:
    # markdown → HTML 変換（markdown ライブラリ使用）
    # Noto Sans JP フォント CSS 適用
    # WeasyPrint で HTML → PDF バイト列生成

def generate_docx(result: AnalysisResult, company_name: str, date: str) -> bytes:
    # python-docx で Document 作成
    # 見出し（Heading 1/2）・表・リスト構造を適用
    # BytesIO でバイト列として返す
```

### `server/src/analysis/router.py`（追加エンドポイント）

```python
@router.get("/analysis/{result_id}/download")
async def download_analysis(
    result_id: UUID,
    format: Literal["pdf", "docx"],
    session: AsyncSession = Depends(get_session)
) -> Response:
    result = await AnalysisResultRepository.find_by_id(session, result_id)
    if not result:
        raise HTTPException(status_code=404)
    
    company_name = result.structured["company_profile"]["name"] or "企業"
    date = result.created_at.strftime("%Y-%m-%d")
    filename = f"{company_name}_{date}.{format}"
    
    if format == "pdf":
        content = generate_pdf(result.markdown_page, company_name, date)
        media_type = "application/pdf"
    else:
        content = generate_docx(result, company_name, date)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
```

### フロントエンド

#### `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`（変更）
- Mantine `Menu` コンポーネントでドロップダウン（PDF / Word 2択）
- 選択時に `fetch(downloadUrl)` → `response.blob()` → `URL.createObjectURL()` → `<a>` タグクリック

```typescript
const handleDownload = async (format: "pdf" | "docx") => {
  const res = await fetch(`/api/analysis/${resultId}/download?format=${format}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${companyName}_${date}.${format}`;
  a.click();
  URL.revokeObjectURL(url);
};
```

## データモデル

ダウンロード機能は既存の `AnalysisResult` ORM モデルを使用する。専用テーブルは不要。

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。*

Property 1: PDFファイル名の形式
*For any* 分析結果に対して、PDFダウンロードのレスポンスヘッダーに含まれるファイル名は `{企業名}_{YYYY-MM-DD}.pdf` の形式に従う
**Validates: Requirements 1.2**

Property 2: Wordファイル名の形式
*For any* 分析結果に対して、Wordダウンロードのレスポンスヘッダーに含まれるファイル名は `{企業名}_{YYYY-MM-DD}.docx` の形式に従う
**Validates: Requirements 2.2**

## エラーハンドリング

| エラー種別 | HTTPステータス | 説明 |
|-----------|--------------|------|
| result_id が存在しない | 404 | AnalysisResult not found |
| PDF生成失敗 | 500 | WeasyPrint エラー |
| Word生成失敗 | 500 | python-docx エラー |

## テスト戦略

### ユニットテスト
- `generate_pdf()` が非空のバイト列を返すことを確認
- `generate_docx()` が非空のバイト列を返すことを確認
- 存在しない result_id に対して 404 が返ることを確認

### プロパティベーステスト
- Property 1, 2: 任意の企業名・日付に対してファイル名形式が正しいことを検証（最低100回）
- タグ形式: `Feature: download, Property {N}: {property_text}`
