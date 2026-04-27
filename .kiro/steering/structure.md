---
inclusion: auto
---

# ディレクトリ構成・アーキテクチャ — 企業分析エージェント

## 全体構成

```
corporate-research/
├── client/                     # フロントエンド（Next.js）
├── server/                     # バックエンド（FastAPI）
├── docs/                       # プロジェクトドキュメント
├── .kiro/                      # Kiro 設定・steering
│   └── steering/
│       ├── product.md
│       ├── tech.md
│       └── structure.md
└── AGENTS.md
```

## フロントエンド — FSD（Feature-Sliced Design）

### レイヤ構成

FSD の標準レイヤのうち、MVP で使用するものを以下に示す。

| レイヤ | 役割 | MVP での使用 |
|--------|------|-------------|
| app | アプリ全体の初期化、プロバイダー、グローバル設定 | ○ |
| pages | ページ単位のコンポーネント（Next.js App Router のルート） | ○ |
| widgets | ページ内の大きなUI ブロック（複数 feature の組み合わせ） | ○ |
| features | ユーザー操作に対応する機能単位 | ○ |
| entities | ビジネスエンティティ（企業情報等のドメインモデル） | ○ |
| shared | 共通ユーティリティ、UI 部品、API クライアント、型定義 | ○ |

### ディレクトリ構成

```
client/src/
├── app/                        # Next.js App Router（FSD の app レイヤ兼用）
│   ├── layout.tsx              # ルートレイアウト（MantineProvider 等）
│   ├── page.tsx                # トップページ
│   ├── globals.css
│   ├── favicon.ico
│   └── analysis/               # 分析ページ（将来的にルート追加）
│       └── page.tsx
│
├── widgets/                    # ページ内の大きな UI ブロック
│   └── analysis-result/        # 分析結果表示ウィジェット
│       ├── ui/
│       │   └── AnalysisResult.tsx
│       └── index.ts
│
├── features/                   # ユーザー操作に対応する機能
│   └── company-search/         # 企業名入力・検索機能
│       ├── ui/
│       │   └── CompanySearchForm.tsx
│       ├── model/
│       │   └── schema.ts       # Valibot バリデーションスキーマ
│       └── index.ts
│
├── entities/                   # ビジネスエンティティ
│   └── company/                # 企業エンティティ
│       ├── ui/
│       │   └── CompanyCard.tsx  # 企業情報の表示コンポーネント
│       ├── model/
│       │   └── types.ts        # 企業関連の型定義（手動定義分）
│       └── index.ts
│
└── shared/                     # 共通リソース
    ├── api/
    │   ├── generated/           # Orval 自動生成（編集禁止）
    │   │   ├── analysis/        # 分析エンドポイント
    │   │   │   └── analysis.ts
    │   │   ├── auth/            # 認証エンドポイント
    │   │   │   └── auth.ts
    │   │   ├── companies/       # 企業・履歴・深掘りエンドポイント
    │   │   │   └── companies.ts
    │   │   ├── compare/         # 比較エンドポイント
    │   │   │   └── compare.ts
    │   │   ├── health/          # ヘルスチェックエンドポイント
    │   │   │   └── health.ts
    │   │   ├── search/          # 企業検索エンドポイント
    │   │   │   └── search.ts
    │   │   ├── share/           # シェアエンドポイント
    │   │   │   └── share.ts
    │   │   └── model/           # リクエスト / レスポンス型
    │   ├── client.ts            # 認証済み Axios クライアント（Clerk JWT 付与）
    │   ├── instance.ts          # Axios インスタンス設定（Orval mutator）
    │   └── index.ts
    ├── ui/                      # 共通 UI コンポーネント
    │   └── index.ts
    ├── lib/                     # 共通ユーティリティ関数
    │   └── index.ts
    └── config/                  # 環境変数・定数
        └── env.ts
```

### FSD の依存ルール

```
app → pages → widgets → features → entities → shared
（上位レイヤは下位レイヤのみ参照可能。逆方向の依存は禁止）
```

- `features` は `entities` と `shared` を参照できるが、`widgets` は参照できない
- `shared` はどのレイヤからも参照されるが、他のレイヤを参照しない
- 各スライス（例: `company-search`）は `index.ts` で公開 API を定義し、内部実装を隠蔽する

### 命名規則（フロントエンド）

| 対象 | 規則 | 例 |
|------|------|-----|
| ディレクトリ | kebab-case | `company-search`, `analysis-result` |
| コンポーネントファイル | PascalCase.tsx | `CompanySearchForm.tsx` |
| ユーティリティファイル | camelCase.ts | `formatDate.ts` |
| 型定義ファイル | camelCase.ts | `types.ts`, `schema.ts` |
| barrel export | index.ts | 各スライスのルートに配置 |

## バックエンド — モジュラーモノリス

### 設計方針

- `src/` 直下にモジュールを配置
- 各モジュールは独立したドメイン責務を持つ
- モジュール間の依存は `shared` を経由するか、明示的なインターフェースを通じて行う
- FastAPI の Router を各モジュールで定義し、`main.py` で集約

### ディレクトリ構成

```
server/
├── main.py                     # FastAPI アプリケーションエントリポイント
├── pyproject.toml
├── .env                        # 環境変数（Git 管理外）
│
└── src/
    ├── analysis/               # 分析モジュール（MVP の中核）
    │   ├── __init__.py
    │   ├── router.py           # FastAPI Router（エンドポイント定義）
    │   ├── service.py          # ビジネスロジック（分析フローの制御）
    │   ├── schemas.py          # Pydantic スキーマ（リクエスト / レスポンス）
    │   └── prompts.py          # LLM プロンプトテンプレート
    │
    ├── collector/              # 情報収集モジュール
    │   ├── __init__.py
    │   ├── service.py          # Web スクレイピング・情報収集ロジック
    │   └── parsers.py          # HTML パーサー（BeautifulSoup）
    │
    └── shared/                 # 共通モジュール
        ├── __init__.py
        ├── config.py           # pydantic-settings による設定管理
        ├── llm.py              # LangChain LLM クライアント初期化
        └── exceptions.py       # 共通例外定義
```

### モジュールの責務

| モジュール | 責務 | 主要技術 |
|-----------|------|---------|
| `analysis` | 分析リクエストの受付、フロー制御、結果返却 | FastAPI, LangChain |
| `collector` | Web 情報の収集・パース | httpx, BeautifulSoup, lxml |
| `shared` | 設定管理、LLM クライアント、共通例外 | pydantic-settings, langchain-azure-ai |

### MVP での分析フロー

```
[POST /api/analysis]
    ↓
[analysis.router] → リクエスト受付・バリデーション
    ↓
[analysis.service] → フロー制御
    ↓
[collector.service] → Web 情報収集
    ↓
[analysis.service] → LangChain チェーンで要約・分析
    ↓                    ↑
    ↓              [shared.llm] → Azure AI Foundry
    ↓
[analysis.schemas] → レスポンス構造化
    ↓
[JSON レスポンス返却]
```

### 命名規則（バックエンド）

| 対象 | 規則 | 例 |
|------|------|-----|
| モジュールディレクトリ | snake_case | `analysis`, `collector` |
| Python ファイル | snake_case.py | `service.py`, `router.py` |
| クラス | PascalCase | `AnalysisService`, `CompanyInfo` |
| 関数 | snake_case | `analyze_company`, `collect_info` |
| Pydantic モデル | PascalCase | `AnalysisRequest`, `AnalysisResponse` |
| 定数 | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT`, `MAX_RETRIES` |

### main.py の構成イメージ

```python
from fastapi import FastAPI
from src.analysis.router import router as analysis_router

app = FastAPI(
    title="企業分析エージェント API",
    version="0.1.0",
)

app.include_router(analysis_router, prefix="/api")
```

## OpenAPI スキーマ生成から Orval 生成までの流れ

### 1. バックエンド（FastAPI）

FastAPI が Pydantic モデルから自動的に OpenAPI スキーマを生成・公開する。

```
GET http://localhost:8000/openapi.json
```

### 2. Orval 設定（`client/orval.config.ts`）

```typescript
import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: {
      target: "../server/openapi.json",
    },
    output: {
      target: "./src/shared/api/generated",
      schemas: "./src/shared/api/generated/model",
      client: "react-query",
      httpClient: "axios",
      mode: "tags-split",          // FastAPI タグ単位でファイル分割
      override: {
        mutator: {
          path: "./src/shared/api/instance.ts",
          name: "customInstance",
        },
        query: {
          useQuery: true,
          useMutation: true,
        },
      },
    },
  },
});
```

### 3. 生成コマンド

```bash
# client/ ディレクトリで実行
npx orval
```

### 4. 生成物の利用

```typescript
// features/company-search/ui/CompanySearchForm.tsx
import { useSearchCompanyApiSearchGet } from "@/shared/api/generated/search/search";
import { usePostAnalysisApiAnalysisPost } from "@/shared/api/generated/analysis/analysis";

const { data } = useSearchCompanyApiSearchGet({ q: "トヨタ" });
const mutation = usePostAnalysisApiAnalysisPost();
mutation.mutate({ data: { url: "https://toyota.co.jp", template: "general" } });
```

## フロントエンドとバックエンドの責務分離

| 責務 | フロントエンド | バックエンド |
|------|-------------|------------|
| 入力バリデーション | Valibot（UX 向上のため） | Pydantic（信頼境界） |
| API 通信 | Orval 生成クライアント | — |
| 状態管理 | React Query + useState | — |
| 情報収集 | — | httpx + BeautifulSoup |
| AI 処理 | — | LangChain + Azure AI Foundry |
| フロー制御 | — | analysis.service |
| 結果の構造化 | 表示用の整形のみ | Pydantic スキーマで構造化 |
| エラーハンドリング | UI 表示 | 例外定義・HTTP ステータス |

原則：ロジックはバックエンドに集約し、フロントエンドは「表示」と「入力」に専念する。

## 将来的な LangGraph 導入に備えた設計方針

MVP 段階で以下を意識しておくことで、LangGraph 導入時の破綻を防ぐ：

1. 処理単位のモジュール化
   - 情報収集、要約、分析をそれぞれ独立した関数 / クラスとして実装
   - LangGraph のノードとしてそのまま組み込めるようにする

2. モジュール間の疎結合
   - `collector` と `analysis` は明確に分離
   - `analysis.service` がオーケストレーションを担当し、各処理を呼び出す構成
   - LangGraph 導入時は `analysis.service` のフロー制御部分をグラフに置き換える

3. 入出力の型定義
   - 各処理の入出力を Pydantic モデルで明確に定義
   - LangGraph の State として再利用可能

4. プロンプトの外部化
   - `prompts.py` にプロンプトテンプレートを集約
   - LangGraph のノードごとにプロンプトを差し替え可能

### LangGraph 移行時のイメージ

```
MVP:
  analysis.service → collector.service → LangChain chain → response

将来:
  analysis.graph (LangGraph)
    ├── Node: collect    → collector.service
    ├── Node: summarize  → LangChain chain
    ├── Node: analyze    → LangChain chain
    └── Node: format     → response builder
```

`analysis.service` の逐次呼び出しを LangGraph のグラフ定義に置き換えるだけで移行できる構成を目指す。
