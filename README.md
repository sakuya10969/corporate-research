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
| openai-agents（OpenAI Agents SDK） | Agent / Runner によるLLM呼び出し |
| openai（AsyncAzureOpenAI） | Azure OpenAI エンドポイント接続 |
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
uv run dev            # 開発サーバー起動
uv run lint           # Ruff lint チェック
uv run lint-fix       # Ruff lint 自動修正
uv run format         # Ruff フォーマット
uv run format-check   # Ruff フォーマットチェック（CI用）
uv run openapi        # OpenAPI スキーマエクスポート
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
| POST | `/api/analysis` | 企業分析を実行 |
| GET | `/api/analysis/{result_id}` | 分析結果を取得 |
| GET | `/api/analysis/{result_id}/download` | PDF / Word ダウンロード（`?format=pdf\|docx`） |
| POST | `/api/analysis/{result_id}/share` | 共有リンクを発行 |
| GET | `/api/share/{share_id}` | 共有リンクから分析結果を取得 |
| GET | `/api/companies/{company_id}/runs` | 分析履歴一覧 |
| POST | `/api/companies/{company_id}/deep-research` | 深掘り分析（保存済みデータ前提） |
| GET | `/api/search` | 企業名からURL候補を検索（`?q=企業名`） |
| POST | `/api/compare` | 複数企業の比較分析（最大3社） |
| GET | `/api/health` | ヘルスチェック |

OpenAPI ドキュメント: http://localhost:8000/docs

## アーキテクチャ

- フロントエンド: [Feature-Sliced Design（FSD）](https://feature-sliced.design/) に基づくレイヤ構成
- バックエンド: モジュラーモノリス。`analysis` / `collector` / `shared` の3モジュール構成
- LLM: OpenAI Agents SDK（`openai-agents`）の `Agent` + `Runner` で2エージェントパイプラインを構成
- API連携: FastAPI の OpenAPI スキーマ → Orval で TypeScript クライアント + React Query フックを自動生成

### 分析フロー

```
企業URL入力 → サイト情報収集（サイトマップ/内部リンク探索）
  → 構造保持テキスト抽出・ページ分類
  → extraction_agent: 構造化抽出（企業プロフィール、財務、ニュース等）
  → summary_agent: 要約・SWOT分析・競合推定・スコアリング
  → Markdownレポート生成 + DB永続化
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
