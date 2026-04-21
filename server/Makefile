UV ?= uv run

.PHONY: dev lint lint-fix format format-check openapi

dev:
	$(UV) fastapi dev main.py

lint:
	$(UV) ruff check .

lint-fix:
	$(UV) ruff check --fix .

format:
	$(UV) ruff format .

format-check:
	$(UV) ruff format --check .

openapi:
	$(UV) python scripts/export_openapi.py
