# 企業分析エージェント（Corporate Research Agent）

企業URLを入力するだけで、その企業サイトから公開情報を自動収集・整理・要約し、構造化された分析結果を返す業務支援プロダクト。

チャットUIではなく、「企業分析」という業務フローを自動化するタスク完了型プロダクトとして設計されています。

## 技術スタック

### フロントエンド

| 技術 | 役割 |
|------|------|
| Next.js 16 | App Router、SSR |
| React 19 | コンポーネントベースUI |
| TypeScript 5 | 型安全性 |
| Mantine 9 | UIコンポーネント |
| TanStack React Query 5 | サーバー状態管理 |
| Valibot | フォームバリデーション |
| Orval | OpenAPI → APIクライアント自動生成 |
| Biome | リンター / フォーマッター |

### バックエンド

| 技術 | 役割 |
|------|------|
| FastAPI | 非同期API、OpenAPIスキーマ自動生成 |
| Python 3.14+ | — |
| LangChain + langchain-azure-ai | LLMチェーン構築 |
| Azure AI Foundry | LLMモデルホスティング基盤 |
| httpx + BeautifulSoup | 非同期Web情報収集・HTMLパース |
| pydantic-settings | 型安全な設定管理 |
| Ruff | リンター / フォーマッター |

## ディレクトリ構成

```
corporate-research/
├── client/                  # フロントエンド（Next.js / FSD）
│   └── src/
│       ├── app/             # App Router（レイアウト、ページ）
│       ├── widgets/         # 大きなUIブロック（分析結果表示等）
│       ├── features/        # 機能単位（企業URL入力等）
│       ├── entities/        # ビジネスエンティティ（企業情報表示）
│       └── shared/          # 共通（APIクライアント、設定）
├── server/                  # バックエンド（FastAPI / モジュラーモノリス）
│   ├── main.py              # エントリポイント
│   └── src/
│       ├── analysis/        # 分析モジュール（フロー制御、LLM処理）
│       ├── collector/       # 情報収集モジュール（スクレイピング）
│       └── shared/          # 共通（設定、LLMクライアント、例外）
├── docs/                    # プロジェクトドキュメント
└── DESIGN.md                # デザインシステム定義
```

## セットアップ

### 前提条件

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)（Python パッケージマネージャー）
- Node.js 20+
- [Bun](https://bun.sh/)（パッケージマネージャー）

### バックエンド

```bash
cd server

# 依存関係のインストール
uv sync

# 環境変数の設定
cp .env.example .env
# .env を編集して以下を設定:
#   CLIENT_ID="[your-client-id]"
#   CLIENT_SECRET="[your-client-secret]"
#   TENANT_ID="[your-tenant-id]"
#   AZURE_AI_PROJECT_ENDPOINT="[your-endpoint]"
#   LLM_MODEL_NAME="gpt-4.1-mini"
#   AZURE_OPENAI_ENDPOINT="[your-azure-openai-endpoint]"
#   AZURE_OPENAI_API_KEY="[your-api-key]"
#   AZURE_DEPLOYMENT="gpt-4.1-mini"
#   API_VERSION="2025-01-01-preview"

# 開発サーバー起動
uv run fastapi dev main.py
```

サーバーは http://localhost:8000 で起動します。

#### 利用可能なコマンド

```bash
make dev            # 開発サーバー起動
make lint           # Ruff lint チェック
make lint-fix       # Ruff lint 自動修正
make format         # Ruff フォーマット
make format-check   # Ruff フォーマットチェック（CI用）
make openapi        # OpenAPI スキーマエクスポート
```

### フロントエンド

```bash
cd client

# 依存関係のインストール
bun install

# APIクライアントの生成
bun run generate

# 開発サーバー起動
bun dev
```

クライアントは http://localhost:3000 で起動します。

#### 利用可能なスクリプト

```bash
bun dev             # 開発サーバー起動
bun run build       # プロダクションビルド
bun start           # プロダクションサーバー起動
bun run lint        # Biome lint チェック
bun run lint:fix    # Biome lint 自動修正
bun run format      # Biome フォーマット（書き込み）
bun run format:check # Biome フォーマットチェック（CI用）
bun run typecheck   # TypeScript 型チェック
bun run generate    # Orval API クライアント生成
```

## API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/analysis` | 企業分析を実行（リクエスト: `{ "company_url": "https://example.co.jp/" }`） |
| GET | `/api/health` | ヘルスチェック |

OpenAPI ドキュメント: http://localhost:8000/docs

## アーキテクチャ

- フロントエンド: [Feature-Sliced Design（FSD）](https://feature-sliced.design/) に基づくレイヤ構成
- バックエンド: モジュラーモノリス。将来の LangGraph 導入を見据えた設計
- API連携: FastAPI の OpenAPI スキーマ → Orval で TypeScript クライアント + React Query フックを自動生成

### 分析フロー

```
企業URL入力 → サイト情報収集（サイトマップ/内部リンク探索）
  → 構造保持テキスト抽出・ページ分類
  → Stage 1: LLM 構造化抽出（企業プロフィール、財務、ニュース等）
  → Stage 2: LLM 要約・SWOT分析・競合推定
  → Markdownレポート生成
  → 構造化された分析結果を返却
```

## ドキュメント

| ファイル | 内容 |
|---------|------|
| [docs/project-overview.md](docs/project-overview.md) | プロジェクト概要・MVPスコープ |
| [docs/tech-stack.md](docs/tech-stack.md) | 技術スタック詳細 |
| [docs/architecture-philosophy.md](docs/architecture-philosophy.md) | アーキテクチャ思想（FSD / モジュラーモノリス） |
| [docs/domain-design.md](docs/domain-design.md) | ドメイン設計・エンティティ定義 |
| [docs/api-design.md](docs/api-design.md) | APIデザイン・スキーマ定義 |
| [docs/specs.md](docs/specs.md) | 機能仕様一覧 |
| [DESIGN.md](DESIGN.md) | デザインシステム（カラー、タイポグラフィ、コンポーネント） |

## ライセンス

Private
