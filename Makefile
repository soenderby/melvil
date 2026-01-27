.PHONY: sync test lint format check

sync:
	uv sync --dev

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

check: format lint test
