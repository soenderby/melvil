# Melvil - Agent Guidelines

This document provides context and guidelines for AI agents working on the Melvil codebase.

## Project Overview

**Melvil** is a learning-directed knowledge management system that helps readers decide what to read based on their learning goals. It automates "inspectional reading" at scale—generating summaries, extracting concepts, and recommending relevant materials and chapters.

### Core Value Proposition
- Sync with Zotero libraries
- Generate multi-level summaries via LLM
- Score material relevance against learning goals
- Recommend specific chapters, not just books

## Architecture

### Technology Stack
- **Database**: SQLite (single file, zero infrastructure)
- **Vector Search**: sqlite-vec
- **LLM**: Claude API (summarization, concept extraction)
- **Embeddings**: OpenAI text-embedding-3-small
- **CLI**: Click + Rich
- **Zotero**: Direct SQLite access + pyzotero

### Key Files
```
melvil/
├── design.md              # Full system design document
├── AGENTS.md              # This file
├── src/                   # Source code (when created)
│   ├── cli.py             # CLI entry point
│   ├── db.py              # SQLite operations
│   ├── zotero.py          # Zotero integration
│   ├── enrich.py          # LLM summarization
│   └── relevance.py       # Scoring and recommendations
└── tests/
```

## Development Phases

1. **Librarian** (MVP): Add, sync, summarize, search
2. **Advisor**: Goals, relevance scoring, recommendations
3. **Guide**: Chapter-level analysis, reading plans
4. **Cartographer**: Prerequisites, knowledge graphs (future)

## Agent Coordination

This project uses **MCP Agent Mail** for agent coordination.

### When Starting Work
1. Register with the project using `register_agent`
2. Check inbox for any messages from other agents
3. Reserve files you plan to modify using `file_reservation_paths`

### When Collaborating
- Use `send_message` to communicate with other agents
- Check `fetch_inbox` periodically for updates
- Acknowledge important messages with `acknowledge_message`

### File Ownership
Before modifying files, check for existing reservations to avoid conflicts.

## Code Style

### Python
- Python 3.11+
- Type hints required
- Use `pydantic` for data models
- Async where beneficial (LLM calls, I/O)
- Format with `ruff`

### CLI Design
- Commands are verbs: `add`, `sync`, `show`, `search`
- Nouns are titles, not IDs: `melvil show "DDIA"`
- Output is scannable: percentages, clear verdicts
- Fast: common queries < 500ms

### Database
- SQLite only (no external databases in Phase 1-3)
- Use JSON columns for arrays
- FTS5 for full-text search
- sqlite-vec for vector similarity

## Key Design Decisions

1. **Zotero is source of truth** — Melvil enriches, doesn't replace
2. **Metadata-first** — Full PDFs optional, not required
3. **CLI-first** — No web UI until proven necessary
4. **Simple scoring** — Cosine similarity + concept overlap, not elaborate formulas
5. **User agency** — Show information, let users decide

## Testing

- Unit tests for core logic
- Integration tests for Zotero sync
- CLI tests using Click's test runner

## Common Tasks

### Adding a new CLI command
1. Add command function in `src/cli.py`
2. Use `@click.command()` decorator
3. Add to appropriate command group
4. Update design.md if significant

### Adding LLM functionality
1. Define prompt in `src/prompts/`
2. Use structured output parsing
3. Cache responses where appropriate
4. Handle rate limits gracefully

### Modifying the database schema
1. Update schema in `src/db.py`
2. Add migration if needed
3. Update design.md Appendix A

## Resources

- **Design Document**: `design.md` — Full system specification
- **Adler's Framework**: "How to Read a Book" — Conceptual foundation
