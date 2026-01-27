# Melvil

Melvil is a concept mapping system for readers who learn by connecting ideas across sources.
It tracks books, concepts, and the relationships between them.

## Development

### Tests

Install dev dependencies and run tests with uv:

```bash
uv sync --dev
uv run pytest
```

Or use the Makefile:

```bash
make test
```

If you see `No module named pytest`, make sure you ran `uv sync --dev` first.

### Optional features

Install extras for visualization and PDF TOC import:

```bash
uv sync --extra viz --extra pdf
```

Or with pip:

```bash
pip install ".[viz,pdf]"
```
