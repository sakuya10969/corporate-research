---
name: fsd-architecture
description: Feature-Sliced Design（FSD）のレイヤ構成・依存ルール・命名規則。client/src/ 配下のコードを書く際に使用する。
license: MIT
metadata:
  author: project
  version: "1.0"
---

# FSD（Feature-Sliced Design）— このプロジェクトでの使い方

## レイヤ構成と依存方向

```
app → widgets → features → entities → shared
```

上位レイヤは下位レイヤのみ参照可。逆方向は禁止。

| レイヤ | 役割 | 例 |
|--------|------|-----|
| `app/` | Next.js App Router。レイアウト・ページ・プロバイダー | `layout.tsx`, `page.tsx` |
| `widgets/` | ページ内の大きなUIブロック（複数featureの組み合わせ） | `analysis-result/` |
| `features/` | ユーザー操作に対応する機能単位 | `company-search/` |
| `entities/` | ビジネスエンティティの表示 | `company/` |
| `shared/` | 共通リソース。他レイヤを参照しない | `api/`, `config/` |

## ディレクトリ構成

```
client/src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── compare/page.tsx
│   └── share/[shareId]/page.tsx
├── widgets/
│   └── analysis-result/
│       ├── ui/AnalysisResult.tsx
│       └── index.ts          ← 公開APIをここで定義
├── features/
│   └── company-search/
│       ├── ui/CompanySearchForm.tsx
│       ├── model/schema.ts   ← Valibotスキーマ
│       └── index.ts
├── entities/
│   └── company/
│       ├── ui/CompanyCard.tsx
│       └── index.ts
└── shared/
    ├── api/
    │   ├── generated/        ← Orval自動生成（編集禁止）
    │   ├── instance.ts       ← Axiosインスタンス
    │   └── index.ts
    └── config/env.ts
```

## 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| ディレクトリ | kebab-case | `company-search` |
| コンポーネント | PascalCase.tsx | `CompanySearchForm.tsx` |
| ユーティリティ | camelCase.ts | `formatDate.ts` |
| barrel export | index.ts | 各スライスのルートに必須 |

## 各スライスの公開API（index.ts）

スライス内部の実装は隠蔽し、`index.ts` で公開するものだけをエクスポートする。

```typescript
// features/company-search/index.ts
export { CompanySearchForm } from "./ui/CompanySearchForm";
export type { CompanySearchSchema } from "./model/schema";
```

## API通信

`shared/api/generated/` は Orval が自動生成するため手動編集禁止。

```typescript
// Orval生成のReact Queryフックを使う
import { usePostAnalysis } from "@/shared/api/generated/default/default";

const mutation = usePostAnalysis();
mutation.mutate({ company_url: "https://example.co.jp/" });
```

## バリデーション（Valibot）

フォーム入力のバリデーションは Valibot を使う（Zodは使わない）。

```typescript
// features/company-search/model/schema.ts
import * as v from "valibot";

export const CompanySearchSchema = v.object({
  company_url: v.pipe(
    v.string(),
    v.nonEmpty("URLを入力してください"),
    v.url("有効なURLを入力してください"),
    v.startsWith("http", "http:// または https:// で始めてください"),
  ),
});
```

## よくある違反パターン

```typescript
// ❌ features から widgets を参照
import { AnalysisResult } from "@/widgets/analysis-result";

// ❌ shared から features を参照
import { CompanySearchForm } from "@/features/company-search";

// ❌ generated/ を直接編集
// client/src/shared/api/generated/default/default.ts を手動編集

// ✅ 正しい依存方向
// widgets → features → entities → shared
```
