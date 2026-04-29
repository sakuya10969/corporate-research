UV ?= uv run

.PHONY: dev lint lint-fix format format-check imports imports-check fix check openapi \
        migrate upgrade downgrade db-history

# --- Dev ---
dev:
	$(UV) fastapi dev main.py

# --- Lint / Format ---
lint:
	$(UV) ruff check src/

lint-fix:
	$(UV) ruff check --fix src/

format:
	$(UV) ruff format src/

format-check:
	$(UV) ruff format --check src/

imports:
	$(UV) ruff check --select I --fix src/

imports-check:
	$(UV) ruff check --select I src/

fix: lint-fix imports format

check: lint format-check imports-check

# --- OpenAPI ---
openapi:
	$(UV) python scripts/export_openapi.py

# --- Alembic ---
# 使い方: make migrate m="add users table"
migrate:
	$(UV) alembic revision --autogenerate -m "$(m)"

upgrade:
	$(UV) alembic upgrade head

downgrade:
	$(UV) alembic downgrade -1

db-history:
	$(UV) alembic history --verbose
