UV ?= uv run

.PHONY: dev lint lint-fix format format-check check openapi \
        migrate upgrade downgrade db-history

# --- Dev ---
dev:
	$(UV) fastapi dev main.py

# --- Lint / Format ---
lint:
	$(UV) ruff check .

lint-fix:
	$(UV) ruff check --fix .

format:
	$(UV) ruff format src/

format-check:
	$(UV) ruff format --check src/

check: lint format-check

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
