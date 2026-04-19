.PHONY: dev lint lint-fix format format-check openapi

# 開発サーバー起動
dev:
	uv run fastapi dev main.py

# Ruff lint チェック
lint:
	uv run ruff check .

# Ruff lint 自動修正
lint-fix:
	uv run ruff check --fix .

# Ruff フォーマット
format:
	uv run ruff format .

# Ruff フォーマットチェック（CI用）
format-check:
	uv run ruff format --check .

# OpenAPI スキーマエクスポート
openapi:
	uv run python scripts/export_openapi.py
