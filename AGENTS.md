# Melvil - Agent Guidelines

Guidelines for AI agents working on the Melvil codebase.

## Project Overview

**Melvil** is a concept mapping system for readers who learn by connecting ideas across sources. It externalizes the mental map that forms when reading broadly—tracking books, the concepts they contain, and how ideas relate.

### Core Value Proposition
- Track books with reading depth (listed → mapped → reading → read → deep)
- Create first-class concepts that span multiple books
- Link concepts to each other and to the books that discuss them
- Write atomic notes (Zettelkasten-style) tied to concepts and sources
- Navigate and export the concept map

### Target User
A reader who:
- Reads broadly across many books and papers
- Cannot possibly read everything end-to-end
- Maps books shallowly first (TOC, key concepts)
- Builds understanding through connections
- Is familiar with Zettelkasten or networked-note methods

## Architecture

### Technology Stack
- **Database**: SQLite (single file, FTS5 for search)
- **CLI**: Click + Rich (Python)
- **PDF parsing**: PyMuPDF (TOC extraction)
- **Zotero**: Direct SQLite access + pyzotero API

### Key Tables
```
books           -- Sources (books, papers, articles)
chapters        -- Table of contents structure
concepts        -- First-class ideas that span sources
book_concepts   -- Links between books and concepts
concept_links   -- Relationships between concepts
notes           -- Atomic Zettelkasten-style notes
note_links      -- Links between notes
aliases         -- Short names for books
```

### Key Files
```
melvil/
├── docs/
│   ├── SPEC_MVP.md        # Phase 1 spec (concept mapping) - START HERE
│   ├── SPEC_FULL.md       # Full system vision
│   ├── QUESTIONS.md       # Open design questions
│   ├── semantic_archive_design_orientation_literature_guide.md
│   └── archive/           # Historical documents
├── AGENTS.md              # This file
├── src/                   # Source code
│   ├── cli.py             # CLI entry point
│   ├── db.py              # SQLite operations
│   ├── models.py          # Data models
│   ├── zotero.py          # Zotero integration
│   └── export.py          # Export functions
└── tests/
```

## Development Phases

1. **Phase 1: Concept Mapping (MVP)**
   - Add books and capture TOC
   - Create concepts with definitions
   - Link concepts to books and each other
   - Write atomic notes
   - CLI map exploration and export

2. **Phase 2: Deep Reading & Visualization**
   - Passage capture with page-level provenance
   - Full-text search within PDFs
   - Graph visualization (TUI or web)
   - Gap analysis and reading suggestions

3. **Phase 3: Intelligence & Integration**
   - LLM-assisted concept extraction
   - Import from Obsidian, Roam, Kindle
   - Export to Obsidian, Anki, Notion

## Key Design Decisions

1. **Concepts are first-class** — Ideas exist independent of any single source
2. **Shallow before deep** — Map a book's territory before reading deeply
3. **Books have depth levels** — listed → mapped → reading → read → deep
4. **Notes are atomic** — One idea per note, Zettelkasten style
5. **Titles over IDs** — CLI uses `"DDIA"` not `42`
6. **Zotero is optional** — Works standalone with manual book entry

## CLI Design Patterns

### Commands use titles, not IDs
```bash
melvil show "DDIA"                    # Good
melvil show 42                        # Avoid
```

### Aliases for frequently-used books
```bash
melvil alias "DDIA" "Designing Data-Intensive Applications"
melvil show "DDIA"
```

### Concept commands
```bash
melvil concept "consensus"            # Create concept
melvil concept show "consensus"       # Show details
melvil concept link "consensus" --book "DDIA" --chapter 9
melvil concept relate "consensus" "linearizability" --type related
```

### Note commands
```bash
melvil note --concept "consensus" "My insight about consensus..."
melvil note --book "DDIA" --type literature "Summary of chapter 9..."
melvil quote --book "DDIA" --location "p.324" "Exact quote..."
```

## Code Style

### Python
- Python 3.11+
- Type hints required
- Use `pydantic` for data models
- Format with `ruff`

### Database
- SQLite only (single file)
- JSON columns for arrays (authors, aliases, identifiers)
- Foreign keys with ON DELETE CASCADE
- Case-insensitive COLLATE NOCASE for names

### CLI
- Commands are verbs: `add`, `show`, `link`, `relate`
- Flags for modifiers: `--type`, `--book`, `--concept`
- Output via Rich for formatting

## Common Tasks

### Adding a CLI command
1. Add command function in `src/cli.py`
2. Use `@click.command()` decorator
3. Add to appropriate command group
4. Update docs if significant

### Adding a database table
1. Add CREATE TABLE to `src/db.py`
2. Add indexes for common queries
3. Add model class if using pydantic
4. Update SPEC_MVP.md schema section

### Testing
- Run tests via the Makefile: `make test`
- Unit tests for core logic
- Integration tests for database operations
- CLI tests using Click's CliRunner

## Agent Coordination

This project uses **MCP Agent Mail** for agent coordination.

### When Starting Work
1. Register with the project using `register_agent`
2. Check inbox for messages from other agents
3. Reserve files you plan to modify using `file_reservation_paths`

### When Collaborating
- Use `send_message` to communicate with other agents
- Check `fetch_inbox` periodically for updates
- Acknowledge important messages with `acknowledge_message`

## Resources

- **MVP Spec**: `docs/SPEC_MVP.md` — Start here
- **Full Vision**: `docs/SPEC_FULL.md`
- **Open Questions**: `docs/QUESTIONS.md`
- **Zettelkasten Reference**: Ahrens, "How to Take Smart Notes"

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds


<!-- BEGIN BEADS INTEGRATION -->
## Issue Tracking with bd (beads)

**IMPORTANT**: This project uses **bd (beads)** for ALL issue tracking. Do NOT use markdown TODOs, task lists, or other tracking methods.

### Why bd?

- Dependency-aware: Track blockers and relationships between issues
- Git-friendly: Auto-syncs to JSONL for version control
- Agent-optimized: JSON output, ready work detection, discovered-from links
- Prevents duplicate tracking systems and confusion

### Quick Start

**Check for ready work:**

```bash
bd ready --json
```

**Create new issues:**

```bash
bd create "Issue title" --description="Detailed context" -t bug|feature|task -p 0-4 --json
bd create "Issue title" --description="What this issue is about" -p 1 --deps discovered-from:bd-123 --json
```

**Claim and update:**

```bash
bd update bd-42 --status in_progress --json
bd update bd-42 --priority 1 --json
```

**Complete work:**

```bash
bd close bd-42 --reason "Completed" --json
```

### Issue Types

- `bug` - Something broken
- `feature` - New functionality
- `task` - Work item (tests, docs, refactoring)
- `epic` - Large feature with subtasks
- `chore` - Maintenance (dependencies, tooling)

### Priorities

- `0` - Critical (security, data loss, broken builds)
- `1` - High (major features, important bugs)
- `2` - Medium (default, nice-to-have)
- `3` - Low (polish, optimization)
- `4` - Backlog (future ideas)

### Workflow for AI Agents

1. **Check ready work**: `bd ready` shows unblocked issues
2. **Claim your task**: `bd update <id> --status in_progress`
3. **Work on it**: Implement, test, document
4. **Discover new work?** Create linked issue:
   - `bd create "Found bug" --description="Details about what was found" -p 1 --deps discovered-from:<parent-id>`
5. **Complete**: `bd close <id> --reason "Done"`

### Auto-Sync

bd automatically syncs with git:

- Exports to `.beads/issues.jsonl` after changes (5s debounce)
- Imports from JSONL when newer (e.g., after `git pull`)
- No manual export/import needed!

### Important Rules

- ✅ Use bd for ALL task tracking
- ✅ Always use `--json` flag for programmatic use
- ✅ Link discovered work with `discovered-from` dependencies
- ✅ Check `bd ready` before asking "what should I work on?"
- ❌ Do NOT create markdown TODO lists
- ❌ Do NOT use external issue trackers
- ❌ Do NOT duplicate tracking systems

For more details, see README.md and docs/QUICKSTART.md.

<!-- END BEADS INTEGRATION -->
