# 設計書: diff-refresh

## 概要

`page_snapshots` テーブルを使用したページ変更検知と差分分析。SHA-256ハッシュ・ETag・Last-Modifiedを組み合わせて変更ページを特定し、変更ページのみを再分析して差分レポートを生成する。

## アーキテクチャ

```
POST /api/analysis (force_refresh=true, run_type=refresh)
  └── AnalysisService.analyze_company()
        └── CollectorService.collect_with_diff()
              ├── page_snapshots テーブルから前回ハッシュ取得
              ├── ETag/Last-Modified ヘッダーチェック
              ├── content_hash 比較 → 変更ページのみ再取得
              └── page_snapshots テーブル更新
        └── generate_diff_report(prev_structured, new_structured)
              └── analysis_results.diff_report に保存
```

## コンポーネントとインターフェース

### `server/src/db/models.py`（追加モデル）

```python
class PageSnapshot(Base):
    __tablename__ = "page_snapshots"
    snapshot_id: UUID (PK)
    company_id: UUID (FK → companies)
    url: str
    normalized_url: str
    category: str | None
    content_hash: str          # SHA-256
    etag: str | None
    last_modified: str | None
    content_length: int | None
    title: str | None
    description: str | None
    og_title: str | None
    og_description: str | None
    status_code: int | None
    fetched_at: datetime
    is_changed: bool
    previous_hash: str | None
    created_at: datetime
    updated_at: datetime
    # UNIQUE (company_id, normalized_url)
```

### `server/src/collector/service.py`（変更）

```python
async def collect_with_diff(
    company_url: str,
    company_id: UUID,
    session: AsyncSession
) -> tuple[CompanyInfo, list[str]]:
    # 1. page_snapshots から前回スナップショット取得
    # 2. 各ページに対して:
    #    a. ETag/Last-Modified で条件付きリクエスト
    #    b. 304 Not Modified → スキップ
    #    c. 変更あり → SHA-256 計算 → ハッシュ比較
    # 3. 変更ページのみ再取得・パース
    # 4. page_snapshots 更新（is_changed フラグ）
    # 5. 変更ページURL一覧を返す
```

### `server/src/analysis/service.py`（変更）

```python
def generate_diff_report(
    prev_structured: dict,
    new_structured: dict
) -> str:
    # 企業プロフィール変更検知
    # 新規ニュース検知（title で差分）
    # 新規プロダクト検知
    # 財務情報変化検知
    # 変更なしの場合は「変更なし」を返す
```

### フロントエンド

#### `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`（変更）

```tsx
{result.diff_report && (
  <Alert icon={<IconAlertCircle />} title="前回分析からの変更点" color="blue">
    <Text style={{ whiteSpace: "pre-wrap" }}>{result.diff_report}</Text>
  </Alert>
)}
```

## データモデル

### PageSnapshot（DB）
`docs/database-design.md` の `page_snapshots` テーブル定義に準拠。

### AnalysisResponse（変更なし）
既存の `diff_report: str | None` フィールドを使用。

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。*

Property 1: ハッシュ一致時のスキップ
*For any* ページに対して、前回と同一のcontent_hashを持つページは再取得がスキップされ、`is_changed=false` として記録される
**Validates: Requirements 1.4, 1.5**

Property 2: 差分レポートの冪等性
*For any* 同一の `prev_structured` と `new_structured` に対して、`generate_diff_report()` は常に同じ結果を返す
**Validates: Requirements 2.1**

Property 3: 変更なし時のレポート
*For any* 前回と同一の `structured` データに対して、差分レポートは「変更なし」を含む
**Validates: Requirements 2.3**

## エラーハンドリング

| エラー種別 | 対応 |
|-----------|------|
| ETagリクエスト失敗 | フォールバックとしてcontent_hashで比較 |
| page_snapshots 取得失敗 | フルクロールにフォールバック |

## テスト戦略

### ユニットテスト
- `generate_diff_report()` の各変更パターン（ニュース追加・プロフィール変更・変更なし）

### プロパティベーステスト
- Property 1: 任意のページコンテンツに対してハッシュ一致時にスキップされることを検証（最低100回）
- Property 2: 任意の structured データペアに対して差分レポートの冪等性を検証
- Property 3: 同一データに対して「変更なし」が返ることを検証
- タグ形式: `Feature: diff-refresh, Property {N}: {property_text}`
