# Melvil System Spec

## Purpose

Melvil is a **semantic archive** for learning-directed reading. It preserves sources, captures meaning in multiple forms, and helps users recompute relevance as their questions change.

This document describes the full system across all phases. For MVP-specific details, see `SPEC_MVP.md`.

---

## Core Problem

The challenge is not storing information, but **preserving and reactivating meaning**.

Key constraints:
- Relevance is contextual and question-dependent.
- Meaning evolves over time and varies by reader.
- No single representation captures everything.

Therefore, Melvil must support:
- Multiple representations of the same material
- Question-driven, iterative retrieval
- Transparency and provenance
- Evolution of understanding over time

---

## Design Principles

1. **Capture first, structure progressively** — Preserve raw sources; let structure emerge.
2. **Provenance and inspectability** — Every derived artifact traces to sources.
3. **Retrieval as a process** — Support iteration, not just one-shot answers.
4. **User agency** — Show information and let users decide.
5. **Summaries orient; sources decide** — Derived content guides; originals verify.

---

## Current Scope (Phases 1-2)

### What Melvil Does Now

**Phase 1 (MVP)** delivers a synthesis workspace:
- Index PDFs for full-text search
- Find passages across indexed materials
- Capture passages with source references
- Assemble passages and notes into syntheses
- Export to Markdown with provenance

**Phase 2** adds retrieval and enrichment:
- Semantic search via embeddings
- Cross-library search (beyond single workspace)
- LLM-assisted concept extraction
- Import from external sources (Kindle, Readwise)
- User corrections to LLM outputs

### What Melvil Does NOT Do (Yet)

- Automated reading recommendations
- Relevance scoring
- Knowledge graphs or argument mapping
- Multi-user collaboration

---

## Phased Delivery

### Phase 1: Synthesis Workspace (MVP)

**Goal**: Help users assemble and synthesize from sources they're actively reading.

**Capabilities**:
- Create synthesis workspaces around topics
- Add sources from Zotero or manually
- Index PDFs for full-text search
- Find and capture passages
- Add structured notes (thesis, terms, arguments)
- Export to Markdown

**Data model**: Materials, source snapshots, passages, synthesis projects, synthesis items, FTS index.

**See**: `SPEC_MVP.md` for complete specification.

### Phase 2: Retrieval Expansion

**Goal**: Find relevant passages across entire library, not just active workspace.

**Capabilities**:
- Embedding-based semantic search
- Cross-library passage retrieval
- LLM-assisted concept extraction from passages
- Term definition extraction with source links
- Import highlights from Kindle, Readwise, Apple Books
- User correction workflow for LLM outputs

**New data**:

```sql
-- Embeddings for semantic search
passage_embeddings (
  id INTEGER PRIMARY KEY,
  passage_id INTEGER NOT NULL REFERENCES passages(id),
  model_version TEXT NOT NULL,      -- e.g., "text-embedding-3-small-2024"
  embedding BLOB NOT NULL,          -- Vector data
  created_at TIMESTAMP
)

-- LLM-extracted concepts
concepts (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  normalized_name TEXT,             -- Canonical form for matching
  created_at TIMESTAMP
)

-- Concept occurrences in passages
concept_occurrences (
  id INTEGER PRIMARY KEY,
  concept_id INTEGER NOT NULL REFERENCES concepts(id),
  passage_id INTEGER NOT NULL REFERENCES passages(id),
  material_id INTEGER NOT NULL REFERENCES materials(id),
  confidence REAL,                  -- LLM confidence (0-1)
  user_confirmed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP
)

-- Term definitions extracted from sources
term_definitions (
  id INTEGER PRIMARY KEY,
  term TEXT NOT NULL,
  term_as_written TEXT,             -- Original form in source
  material_id INTEGER NOT NULL REFERENCES materials(id),
  passage_id INTEGER REFERENCES passages(id),
  definition TEXT NOT NULL,
  extraction_model TEXT,            -- Model that extracted this
  user_edited BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP
)

-- External highlight imports
imported_highlights (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,             -- 'kindle', 'readwise', 'apple_books'
  external_id TEXT,                 -- ID in source system
  material_id INTEGER REFERENCES materials(id),
  text TEXT NOT NULL,
  location TEXT,                    -- Source-specific location info
  imported_at TIMESTAMP,
  converted_to_passage_id INTEGER REFERENCES passages(id)
)
```

**Provenance model** (Phase 2 adds LLM outputs):

```sql
-- For LLM-derived content, track extraction details
llm_extractions (
  id INTEGER PRIMARY KEY,
  target_type TEXT NOT NULL,        -- 'concept', 'term_definition', 'summary'
  target_id INTEGER NOT NULL,
  model TEXT NOT NULL,              -- e.g., "claude-3-sonnet-20240229"
  prompt_version TEXT,              -- Version of extraction prompt
  raw_response TEXT,                -- Full LLM response for debugging
  created_at TIMESTAMP
)
```

### Phase 3: Structured Meaning (Future)

**Goal**: Support deeper analysis with structured representations.

**Potential capabilities** (subject to validation):
- Argument structure extraction
- Cross-source interpretation tracking
- Concept relationship mapping
- Reading path suggestions

This phase is not yet specified. Design will be informed by user feedback from Phases 1-2.

---

## Architecture

### Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Database | SQLite | Single file, zero infrastructure, FTS5 built-in |
| Vector search | sqlite-vec | Keeps everything in one database |
| LLM | Claude API | Long context, good at extraction |
| Embeddings | OpenAI text-embedding-3-small | Reliable, good quality/cost ratio |
| CLI | Click + Rich | Standard Python CLI, good UX |
| PDF extraction | pdfplumber / PyMuPDF | Pure Python, no external dependencies |

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Zotero    │────▶│  Materials  │────▶│   Source    │
│   Library   │     │   Table     │     │  Snapshots  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │  PDF Files  │────▶│  Passages   │
                    │             │     │  (indexed)  │
                    └─────────────┘     └─────────────┘
                                               │
                           ┌───────────────────┼───────────────────┐
                           ▼                   ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
                    │  FTS Index  │     │  Synthesis  │     │  Embeddings │
                    │  (Phase 1)  │     │  Workspace  │     │  (Phase 2)  │
                    └─────────────┘     └─────────────┘     └─────────────┘
```

### Future Architecture (Vision)

The full semantic archive vision includes a layered architecture where meaning emerges from interaction between layers:

```
Layer 4: Structured Meaning
         Claims, arguments, interpretations, relationships
                    ↑
Layer 3: Semantic Embeddings
         Vector representations for similarity and discovery
                    ↑
Layer 2: Information Retrieval
         FTS for precise, auditable keyword search
                    ↑
Layer 1: Metadata & Facets
         Authors, dates, domains, projects
                    ↑
Layer 0: Immutable Sources
         PDFs, notes, snapshots (versioned, preserved)
```

**Current implementation**: Phases 1-2 implement Layers 0-3. Layer 4 (structured meaning) is deferred pending user validation.

---

## CLI Design

### Command Structure

```
melvil
├── zotero
│   └── sync              # Sync from Zotero library
├── alias                 # Set title alias
├── show <title>          # Show material details
├── synthesize <topic>    # Create synthesis workspace
└── synth
    ├── show              # Show workspace
    ├── list              # List workspaces
    ├── add-source        # Add source to workspace
    ├── index             # Index source for search
    ├── find              # Search passages
    ├── capture           # Capture passage
    ├── note              # Add note
    ├── reorder           # Reorder items
    └── export            # Export to Markdown
```

### Design Principles

1. **Nouns are titles, not IDs**: `melvil show "DDIA"` not `melvil show abc123`
2. **Commands are verbs**: `synthesize`, `find`, `capture`, `export`
3. **Output is scannable**: Show sources, page references, provenance
4. **Fast feedback**: Common operations < 500ms

### Output Standards

All passage displays include:
- Source title
- Page reference (when available)
- Chapter (when available)

Search results show:
- Match snippet with highlighting
- Source and location
- Result number for quick capture

---

## Zotero Integration

### Sync Behavior

```bash
melvil zotero sync
```

1. Connect to local Zotero SQLite database
2. Import/update materials metadata
3. Link to PDF attachments (if present)
4. Preserve Zotero item keys for reference

### Design Decisions

- **Zotero remains source of truth** for bibliography
- **One-way sync**: Zotero → Melvil (no writes back)
- **Non-destructive**: Melvil enriches, doesn't modify
- **Graceful degradation**: Works without Zotero (manual entry)

### Known Limitations

- Zotero database locked while Zotero is running (use API fallback)
- Schema may change across Zotero versions
- Synced vs. local-only libraries behave differently

---

## Anti-Patterns to Avoid

Based on the orientation guide, Melvil explicitly avoids:

1. **Overconfident summarization** — All LLM outputs are provisional and editable
2. **Relevance as black box** — Search shows why results match
3. **Premature ontology** — Structure emerges from use, not upfront design
4. **Single-mode interaction** — Supports search, browse, assemble, export
5. **Forgetting time** — Source snapshots preserve state at capture

---

## Evaluation Metrics

### Phase 1 (MVP)

| Metric | Target |
|--------|--------|
| Time to first capture | < 5 minutes from install |
| Search latency (10k passages) | < 500ms |
| Passage provenance completeness | 100% have source + page |
| Export fidelity | All items preserved with references |

### Phase 2

| Metric | Target |
|--------|--------|
| Semantic search relevance | Top-5 contains relevant passage 80%+ |
| Concept extraction accuracy | User confirms 70%+ without edits |
| Import success rate | 95%+ Kindle/Readwise highlights import |

---

## Open Questions

See `QUESTIONS.md` for unresolved design questions requiring user research before Phase 2.

---

## Document Status

| Document | Purpose | Status |
|----------|---------|--------|
| `SPEC_MVP.md` | Phase 1 implementation spec | Active |
| `SPEC_FULL.md` | Full system vision (this doc) | Active |
| `QUESTIONS.md` | User research questions | Active |
| `semantic_archive_design_orientation_literature_guide.md` | Conceptual foundations | Reference |
| `AGENTS.md` | Developer/agent guidelines | Active |
| `docs/archive/*` | Historical documents | Archived |
