# BrightDays Fleet. Needs uv (https://docs.astral.sh/uv/) and a filled-in .env.
.PHONY: help install dev web seed test safety lint audit check

PORT ?= 8000

help:
	@echo "make install   install dependencies (uv sync)"
	@echo "make dev       run the API + dashboard on http://localhost:$(PORT)"
	@echo "make web       serve only the static dashboard (no backend; try /?mock=1)"
	@echo "make seed      reset the SQLite database to the BrightDays seed"
	@echo "make test      unit + API tests (no API keys needed)"
	@echo "make safety    12-transcript safety suite against real Gemini (needs GEMINI_API_KEY)"
	@echo "make lint      ruff"
	@echo "make audit     pip-audit + bandit"
	@echo "make check     everything CI runs"

install:
	uv sync --all-extras --dev

dev:
	uv run uvicorn app.main:app --reload --port $(PORT)

web:
	python3 -m http.server $(PORT) --directory web

seed:
	uv run python -m app.db.seed

test:
	uv run pytest --ignore=tests/safety -q

safety:
	uv run pytest tests/safety -q

lint:
	uv run ruff check .
	uv run ruff format --check .

audit:
	uv run pip-audit
	uv run bandit -r app -q -ll

check: lint test audit
