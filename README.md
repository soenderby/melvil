# Melvil

Melvil is a concept mapping system for readers who learn by connecting ideas across sources.
It tracks books, concepts, and the relationships between them.

## Usage (MVP)

### Install

Install with uv (recommended):

```bash
uv sync
```

Or with pip:

```bash
pip install .
```

### Database location

Melvil uses a single SQLite file. By default it lives at `~/.melvil/melvil.db`.
Override it with either:

- `melvil --db /path/to/melvil.db`
- `MELVIL_DB_PATH=/path/to/melvil.db`

### Quickstart

Add a book (or import from Zotero):

```bash
melvil add "Designing Data-Intensive Applications" --author "Martin Kleppmann" --year 2017
melvil add "Designing Data-Intensive Applications" --from-zotero
```

Add an alias and set reading depth:

```bash
melvil alias "DDIA" "Designing Data-Intensive Applications"
melvil depth "DDIA" mapped
```

Capture the table of contents:

```bash
melvil toc add "DDIA" --number 1 --title "Reliable, Scalable, and Maintainable Applications" --pages 1-38
melvil toc import "DDIA" --from-pdf /path/to/ddia.pdf
```

Create concepts and link them to books:

```bash
melvil concept "consensus" --definition "Agreement in distributed systems."
melvil concept link "consensus" --book "DDIA" --chapter 9 --location "p.324" --note "Leader election."
melvil concept relate "consensus" "linearizability" --type related
```

Write notes and quotes (wikilinks create or connect concepts):

```bash
melvil note --concept "consensus" "Consensus != just leader election."
melvil note --book "DDIA" --chapter 9 --location "p.330" "Raft simplifies consensus by..."
melvil quote --book "DDIA" --location "p.324" "Exact quote text..."
melvil note --type relation "Consensus relates to [[linearizability]] because..."
```

Explore your map:

```bash
melvil map
melvil map --concept "consensus"
melvil map --book "DDIA"
melvil map --related "consensus"
melvil books
melvil concepts --book "DDIA"
melvil notes --concept "consensus"
```

Export the concept map:

```bash
melvil export --format markdown
melvil export --format json
melvil export --format dot
melvil export --format obsidian --output /path/to/vault
```

### Optional features

Visualization and PDF TOC import require extras:

```bash
uv sync --extra viz --extra pdf
```

Or with pip:

```bash
pip install ".[viz,pdf]"
```

Visualize:

```bash
melvil viz
melvil viz --focus "consensus"
melvil viz --book "DDIA" --related
```

Search notes:

```bash
melvil notes search "consensus OR linear*"
```

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
