---
inclusion: always
---

# 開発コマンドルール

コードの実行・検証・整形などを行う際は、プロジェクトで定義済みのコマンドエイリアスを必ず使用すること。
直接 `ruff`, `biome`, `alembic`, `next`, `tsc` 等のコマンドを叩かず、以下のエイリアス経由で実行する。

## サーバー（server/Makefile）

server/ ディレクトリで `make <target>` を使用する。

| 目的 | コマンド | 備考 |
|---|---|---|
| 開発サーバー起動 | `make dev` | FastAPI dev モード |
| リント | `make lint` | ruff check |
| リント自動修正 | `make lint-fix` | ruff check --fix |
| フォーマット | `make format` | ruff format |
| フォーマット確認 | `make format-check` | ruff format --check |
| import 整理 | `make imports` | ruff isort fix |
| import 確認 | `make imports-check` | ruff isort check |
| 全自動修正 | `make fix` | lint-fix + imports + format |
| 全チェック | `make check` | lint + format-check + imports-check |
| OpenAPI スキーマ出力 | `make openapi` | scripts/export_openapi.py |
| マイグレーション作成 | `make migrate m="説明"` | alembic autogenerate |
| マイグレーション適用 | `make upgrade` | alembic upgrade head |
| マイグレーション巻戻し | `make downgrade` | alembic downgrade -1 |
| マイグレーション履歴 | `make db-history` | alembic history |

## クライアント（client/package.json）

client/ ディレクトリで `bun run <script>` を使用する。

| 目的 | コマンド | 備考 |
|---|---|---|
| 開発サーバー起動 | `bun run dev` | Next.js dev |
| ビルド | `bun run build` | Next.js build |
| 本番サーバー起動 | `bun run start` | Next.js start |
| 全チェック | `bun run check` | biome check |
| 全チェック＋自動修正 | `bun run check:fix` | biome check --write |
| リント | `bun run lint` | biome check |
| リント自動修正 | `bun run lint:fix` | biome check --fix |
| フォーマット | `bun run format` | biome format --write |
| フォーマット確認 | `bun run format:check` | biome format |
| import 整理 | `bun run imports` | biome assist --write |
| import 確認 | `bun run imports:check` | biome assist check |
| 型チェック | `bun run typecheck` | tsc --noEmit |
| API クライアント生成 | `bun run generate` | orval |

## 運用ルール

- サーバー側のコードを変更・追加した後は `make fix`（server/）を実行して整形すること。
- クライアント側のコードを変更・追加した後は `bun run check:fix`（client/）を実行して整形すること。
- DB モデルを変更した場合は `make migrate m="変更内容"` → `make upgrade` を実行すること。
- API スキーマに変更が入った場合は `make openapi`（server/）→ `bun run generate`（client/）の順で再生成すること。
