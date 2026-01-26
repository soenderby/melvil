# Melvil - Agent Guidelines

This document provides context and guidelines for AI agents working on the Melvil codebase.

## Project Overview

**Melvil** is a semantic archive for learning-directed reading. It preserves sources, captures meaning in multiple forms, and helps users recompute relevance as their questions change. The MVP starts with a synthesis workspace for assembling sourced passages.

### Core Value Proposition
- Preserve sources with provenance and time awareness
- Assemble passage-based syntheses with clear source links
- Support iterative retrieval, inspection, and synthesis workflows

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
├── docs/
│   ├── SPEC_MVP.md        # MVP spec (synthesis workspace) - START HERE
│   ├── SPEC_FULL.md       # Full system spec (all phases)
│   ├── QUESTIONS.md       # Open design questions for user research
│   ├── semantic_archive_design_orientation_literature_guide.md  # Conceptual foundations
│   └── archive/           # Historical documents (reference only)
├── AGENTS.md              # This file
├── src/                   # Source code (when created)
│   ├── cli.py             # CLI entry point
│   ├── db.py              # SQLite operations
│   ├── zotero.py          # Zotero integration
│   └── synthesize.py      # Synthesis workspace
└── tests/
```

## Development Phases

1. **Synthesis Workspace (MVP)**: Minimal ingest + passage capture + assembly + export
2. **Clarify + Correct**: Correction loop, term definitions, concept browsing
3. **Retrieval Expansion**: FTS + embeddings, comparisons, interpretations

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
- Commands are verbs: `synthesize`, `add-source`, `add-passage`, `export`
- Nouns are titles, not IDs: `melvil synth add-source "DDIA"`
- Output is scannable: sources, page refs, provenance
- Fast: common queries < 500ms

### Database
- SQLite only (no external databases in Phase 1-3)
- Use JSON columns for arrays
- FTS5 and sqlite-vec added in Phase 3

## Key Design Decisions

1. **Zotero is source of truth** — Melvil enriches, doesn't replace
2. **Capture first, structure progressively** — Start with sources and passages
3. **Provenance-first** — Every derived artifact links back to sources
4. **No black-box recommendations** — Retrieval is inspectable and iterative
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
4. Update `docs/SPEC_MVP.md` or `docs/SPEC_FULL.md` if significant

### Adding LLM functionality
1. Define prompt in `src/prompts/`
2. Use structured output parsing
3. Cache responses where appropriate
4. Handle rate limits gracefully

### Modifying the database schema
1. Update schema in `src/db.py`
2. Add migration if needed
3. Update `docs/SPEC_FULL.md`

## Resources

- **Full System Spec**: `docs/SPEC_FULL.md`
- **MVP Spec**: `docs/SPEC_MVP.md`
- **Orientation Guide**: `docs/semantic_archive_design_orientation_literature_guide.md`
- **Adler's Framework**: "How to Read a Book" — Conceptual foundation
