.PHONY: sync test lint format check

UV_CACHE_DIR ?= /tmp/uv-cache

sync:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync --dev

test:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run pytest

lint:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check .

format:
	UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff format .

check: format lint test
