# 設計書: company-search

## 概要

DuckDuckGo Instant Answer API（`https://api.duckduckgo.com/?q={query}&format=json`）を使用した企業名検索。APIキー不要。フロントエンドはMantine Autocomplete + `useDebouncedValue` でリアルタイム候補表示を実現する。

## アーキテクチャ

```
GET /api/search?q={企業名}
  └── search/router.py
        └── SearchService.search_company(query)
              └── DuckDuckGo Instant Answer API
                    └── CompanySearchResponse（最大5件）

フロントエンド:
  features/company-search/ui/CompanySearchForm.tsx
    └── Mantine Autocomplete
          └── useDebouncedValue(query, 300)
                └── useGetSearchApiSearchGet (Orval生成フック)
```

## コンポーネントとインターフェース

### `server/src/search/service.py`

```python
class SearchService:
    async def search_company(self, query: str) -> CompanySearchResponse:
        # DuckDuckGo Instant Answer API 呼び出し
        # https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1
        # RelatedTopics から企業候補を抽出
        # 最大5件に絞って返す
```

### `server/src/search/router.py`

```python
@router.get("/search")
async def search_company(q: str) -> CompanySearchResponse:
    if not q.strip():
        raise HTTPException(status_code=400, detail="検索クエリを入力してください")
    return await SearchService().search_company(q)
```

### `server/src/search/schemas.py`

```python
class CompanyCandidate(BaseModel):
    name: str
    url: str
    description: str

class CompanySearchResponse(BaseModel):
    query: str
    results: list[CompanyCandidate]  # 最大5件
```

### フロントエンド

#### `client/src/features/company-search/ui/CompanySearchForm.tsx`（変更）

```tsx
const [companyName, setCompanyName] = useState("");
const [debouncedName] = useDebouncedValue(companyName, 300);

const { data: searchResults } = useGetSearchApiSearchGet(
  { q: debouncedName },
  { enabled: debouncedName.length > 0 }
);

<Autocomplete
  label="企業名で検索"
  placeholder="例: トヨタ、Sony"
  value={companyName}
  onChange={setCompanyName}
  data={searchResults?.results.map(r => ({ value: r.url, label: r.name })) ?? []}
  onOptionSubmit={(url) => {
    setCompanyUrl(url);  // URLフィールドに自動入力（分析は実行しない）
  }}
  nothingFoundMessage="見つかりませんでした。URLを直接入力してください"
/>
```

## データモデル

### CompanySearchResponse
`docs/api-design.md` の `CompanySearchResponse` スキーマに準拠。

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。*

Property 1: 検索結果件数の上限
*For any* 検索クエリに対して、返却される候補件数は 0 以上 5 以下である
**Validates: Requirements 1.2**

Property 2: 候補フィールドの完全性
*For any* 検索結果の候補に対して、`name`, `url`, `description` フィールドが全て存在する
**Validates: Requirements 1.3**

## エラーハンドリング

| エラー種別 | HTTPステータス | 説明 |
|-----------|--------------|------|
| 空クエリ | 400 | 検索クエリが空 |
| DuckDuckGo API 失敗 | 500 | 外部API呼び出しエラー |

## テスト戦略

### ユニットテスト
- 空クエリに対して 400 が返ることを確認
- DuckDuckGo APIレスポンスのパース処理

### プロパティベーステスト
- Property 1: 任意のクエリに対して結果件数が 0〜5 であることを検証（最低100回）
- Property 2: 任意の検索結果に対してフィールド完全性を検証
- タグ形式: `Feature: company-search, Property {N}: {property_text}`
