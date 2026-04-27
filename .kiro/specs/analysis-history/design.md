# 設計書: analysis-history

## 概要

`analysis_runs` テーブルを使用した分析履歴管理。バックエンドはAnalysisRunRepositoryの `list_by_company()` を利用し、フロントエンドはMantine Tabsで「分析履歴」タブを追加する。

## アーキテクチャ

```
GET /api/companies/{company_id}/runs
  └── analysis/router.py
        └── AnalysisRunRepository.list_by_company(session, company_id)
              └── analysis_runs テーブル（data-persistence で作成済み）

フロントエンド:
  widgets/analysis-result/ui/AnalysisResult.tsx
    └── Mantine Tabs
          ├── 「分析結果」タブ（既存）
          └── 「分析履歴」タブ（新規）
                └── useGetCompanyRunsApiCompaniesCompanyIdRunsGet (Orval生成フック)
```

## コンポーネントとインターフェース

### バックエンド

#### `server/src/analysis/router.py`（追加エンドポイント）
```python
@router.get("/companies/{company_id}/runs")
async def get_company_runs(
    company_id: UUID,
    session: AsyncSession = Depends(get_session)
) -> list[AnalysisRunResponse]:
    runs = await AnalysisRunRepository.list_by_company(session, company_id)
    if not runs and not await CompanyRepository.exists(session, company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    return [AnalysisRunResponse.from_orm(run) for run in runs]
```

#### `server/src/analysis/schemas.py`（追加スキーマ）
```python
class AnalysisRunResponse(BaseModel):
    run_id: UUID
    run_type: str  # initial / refresh / deep_research
    status: str    # pending / running / completed / failed
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    template: str
    error_message: str | None
```

### フロントエンド

#### `client/src/widgets/analysis-result/ui/AnalysisResult.tsx`（変更）
- Mantine `Tabs` コンポーネントで「分析結果」「分析履歴」「深掘り分析」タブを追加
- 「分析履歴」タブ内で `useGetCompanyRunsApiCompaniesCompanyIdRunsGet` フックを使用
- 各履歴行に実行日時・種別バッジ・状態バッジ・処理時間を表示

## データモデル

### AnalysisRunResponse
```typescript
interface AnalysisRunResponse {
  run_id: string;
  run_type: "initial" | "refresh" | "deep_research";
  status: "pending" | "running" | "completed" | "failed";
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  template: string;
  error_message: string | null;
}
```

## 正確性プロパティ

*プロパティとは、システムの全ての有効な実行において成立すべき特性・振る舞いの形式的な記述である。*

Property 1: 履歴の順序保証
*For any* 企業IDに対して、返却される分析履歴は `started_at` の降順（新しい順）で並んでいる
**Validates: Requirements 1.1**

Property 2: 履歴フィールドの完全性
*For any* 分析実行履歴エントリに対して、`run_id`, `run_type`, `status`, `started_at` フィールドが全て存在する
**Validates: Requirements 1.2**

## エラーハンドリング

| エラー種別 | HTTPステータス | 説明 |
|-----------|--------------|------|
| company_id が存在しない | 404 | Company not found |

## テスト戦略

### ユニットテスト
- `list_by_company()` が新しい順で返すことを確認
- 存在しない company_id に対して 404 が返ることを確認

### プロパティベーステスト
- Property 1: 任意の数の分析実行を作成し、取得結果が常に降順であることを検証（最低100回）
- Property 2: 任意の分析実行に対して必須フィールドが全て存在することを検証
- タグ形式: `Feature: analysis-history, Property {N}: {property_text}`
