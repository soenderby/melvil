# Melvil MVP Spec (Synthesis Workspace)

## Purpose

Deliver immediate value by helping users **find, capture, and synthesize** passages from their reading. The MVP provides a synthesis workspace with passage search, explicit provenance, and structured export.

---

## MVP Goals

1. **Index materials** for full-text search within the workspace.
2. **Find passages** across indexed materials using text search.
3. **Capture passages** with stable source references.
4. **Assemble excerpts** into a structured synthesis with notes.
5. **Export** the workspace to Markdown with full provenance.

---

## Non-Goals (MVP)

- Automated recommendations or relevance scoring.
- Semantic/embedding-based search (Phase 2).
- Concept extraction, term definitions, or argument maps (Phase 2).
- Cross-library search beyond the current workspace (Phase 2).
- Mobile capture or import from Kindle/Readwise (Phase 2).

---

## Primary Workflow

1. **Create workspace** for a topic or question.
2. **Add sources** from Zotero or manual entry.
3. **Index sources** to enable full-text search.
4. **Find passages** using text search across indexed sources.
5. **Capture passages** from search results or manual entry.
6. **Add notes** (thesis, terms, arguments, interpretations).
7. **Assemble** passages and notes into a working outline.
8. **Export** the synthesis to Markdown.

---

## Data Model

### Materials

```sql
materials (
  id INTEGER PRIMARY KEY,
  type TEXT NOT NULL,           -- 'book', 'paper', 'article'
  title TEXT NOT NULL,
  authors TEXT,                 -- JSON array of author names
  year INTEGER,
  identifiers TEXT,             -- JSON: {isbn, doi, arxiv, etc.}
  zotero_key TEXT,              -- Link to Zotero item (if imported)
  content_path TEXT,            -- Path to PDF/EPUB (if available)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Source Snapshots

A source snapshot captures the state of a material at a specific point in time. This enables passages to reference a specific edition even if the user later acquires a different version.

```sql
source_snapshots (
  id INTEGER PRIMARY KEY,
  material_id INTEGER NOT NULL REFERENCES materials(id),
  captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- What was captured
  source_type TEXT NOT NULL,    -- 'pdf', 'epub', 'metadata_only'
  file_path TEXT,               -- Path at capture time (may move later)
  file_hash TEXT,               -- SHA-256 of file content (NULL if no file)

  -- Metadata snapshot (Zotero data at capture time)
  metadata_snapshot TEXT,       -- JSON of metadata at capture

  -- Edition tracking
  edition_info TEXT             -- User note: "2nd ed", "Kindle", ISBN, etc.
)
```

### Passages

```sql
passages (
  id INTEGER PRIMARY KEY,
  material_id INTEGER NOT NULL REFERENCES materials(id),
  source_snapshot_id INTEGER NOT NULL REFERENCES source_snapshots(id),

  -- Location
  page_start INTEGER,
  page_end INTEGER,
  chapter TEXT,                 -- Optional chapter name/number

  -- Content
  text TEXT NOT NULL,

  -- Tracking
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Synthesis Projects

```sql
synthesis_projects (
  id INTEGER PRIMARY KEY,
  topic TEXT NOT NULL,
  guiding_questions TEXT,       -- JSON array of questions
  status TEXT DEFAULT 'active', -- 'active', 'paused', 'completed'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Synthesis Items

```sql
synthesis_items (
  id INTEGER PRIMARY KEY,
  synthesis_id INTEGER NOT NULL REFERENCES synthesis_projects(id),
  item_type TEXT NOT NULL,      -- 'passage', 'thesis', 'term', 'argument', 'interpretation', 'note'

  -- For passages: reference to captured passage
  passage_id INTEGER REFERENCES passages(id),

  -- For notes: inline text
  note_text TEXT,

  -- Ordering within synthesis
  position INTEGER,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Full-Text Search Index (Workspace-Scoped)

FTS5 virtual table for searching within a synthesis workspace. Cross-library search is Phase 2.

```sql
-- FTS index for passage text within indexed materials
passage_fts (
  passage_id INTEGER,
  material_id INTEGER,
  text TEXT
)

-- FTS index for synthesis items (passages + notes)
synthesis_fts (
  synthesis_id INTEGER,
  item_id INTEGER,
  item_type TEXT,
  text TEXT
)
```

### Title Aliases

```sql
aliases (
  id INTEGER PRIMARY KEY,
  alias TEXT NOT NULL UNIQUE,   -- e.g., "DDIA"
  material_id INTEGER NOT NULL REFERENCES materials(id)
)
```

---

## Title Resolution

The CLI uses titles (not IDs) as identifiers. Resolution order:

1. **Exact alias match** (case-insensitive): `"DDIA"` → material with that alias
2. **Exact title match** (case-insensitive): `"Designing Data-Intensive Applications"`
3. **Prefix match**: `"Designing Data"` → matches if unique
4. **Fuzzy match**: Trigram similarity > 0.6

**Multiple matches**: Prompt user to select with numbered list.

**No match**: Suggest closest matches or offer manual entry.

```bash
$ melvil show "designing"

Multiple matches for "designing":
  1. Designing Data-Intensive Applications (Kleppmann, 2017)
  2. Designing Distributed Systems (Burns, 2018)

Select [1-2] or enter full title:
```

**Setting aliases**:
```bash
$ melvil alias "DDIA" "Designing Data-Intensive Applications"
Alias set: DDIA → Designing Data-Intensive Applications
```

---

## CLI Surface

### Workspace Management

```bash
# Create a new synthesis workspace
melvil synthesize "consistency models"

# View workspace status
melvil synth show "consistency models"

# List all workspaces
melvil synth list
```

### Source Management

```bash
# Add source from Zotero (by title)
melvil synth add-source "DDIA"

# Add source manually
melvil synth add-source --manual "Paxos Made Simple" --authors "Lamport" --year 2001

# Index a source for full-text search
melvil synth index "DDIA"

# Set a title alias
melvil alias "DDIA" "Designing Data-Intensive Applications"
```

### Finding Passages

```bash
# Search indexed sources in current workspace
melvil synth find "CAP theorem"

# Search within a specific source
melvil synth find "consistency" --in "DDIA"

# Show context around matches
melvil synth find "linearizability" --context 3
```

### Capturing Passages

```bash
# Capture from search result (by result number)
melvil synth capture 1

# Capture by page range with text extraction from PDF
melvil synth capture "DDIA" --page 323-325 --from-pdf

# Capture with manual text entry
melvil synth capture "DDIA" --page 323-325 --text "The CAP theorem..."

# Capture with chapter reference
melvil synth capture "DDIA" --chapter 9 --page 323-325 --from-pdf
```

### Adding Notes

```bash
# Add thesis note
melvil synth note --type thesis "Consistency requires explicit tradeoffs between availability and partition tolerance."

# Add term definition
melvil synth note --type term "Linearizability: appears as if only one copy of data exists, all operations atomic."

# Add argument
melvil synth note --type argument "CAP implies partitions force choice between latency and staleness."

# Add interpretation
melvil synth note --type interpretation "Kleppmann treats CAP as availability warning, not hard constraint."

# Add general note
melvil synth note "Need to compare with Brewer's original formulation."
```

### Assembly and Export

```bash
# Reorder items in workspace
melvil synth reorder

# Export to Markdown
melvil synth export "consistency models"

# Export to specific file
melvil synth export "consistency models" --output ./notes/consistency.md
```

---

## Passage Capture Flow

### From PDF (`--from-pdf`)

1. **Locate file**: Find PDF path from material record or source snapshot.
2. **Extract text**: Use PDF library to extract text from specified page range.
3. **Display for editing**: Show extracted text in `$EDITOR` (or inline if no editor).
4. **User confirms**: User edits text if needed, saves and exits editor.
5. **Create snapshot**: If no snapshot exists for this file, create one with file hash.
6. **Save passage**: Store passage with source_snapshot_id and page reference.

**Fallback behaviors**:
- **No PDF available**: Error with message "No PDF found for [title]. Use --text for manual entry."
- **Extraction fails**: Warn "Text extraction failed (scanned PDF?). Opening blank editor for manual entry."
- **Low-quality extraction**: Show extracted text with warning "Extraction may be incomplete. Please verify."

### Manual Entry (`--text`)

1. **Validate source**: Confirm material exists, prompt to add if not.
2. **Create snapshot**: Create metadata-only snapshot if none exists.
3. **Save passage**: Store with page reference and provided text.

### From Search Result (`capture <number>`)

1. **Reference search result**: Use passage location from search result.
2. **Expand context**: Optionally show surrounding text for user to adjust boundaries.
3. **Save passage**: Store with automatic source_snapshot_id from indexed source.

---

## Export Format

```markdown
# [Topic]

*Synthesis created: [date] | Last updated: [date]*

## Guiding Questions

1. [Question 1]
2. [Question 2]

---

## Sources

| # | Title | Author | Year |
|---|-------|--------|------|
| 1 | [Title] | [Authors] | [Year] |
| 2 | [Title] | [Authors] | [Year] |

---

## Passages

### 1. [First few words of passage...]

> [Full passage text]

*Source: [Title], p. [page_start]-[page_end] ([edition_info])*

### 2. [First few words...]

> [Passage text]

*Source: [Title], Chapter [chapter], p. [page]*

---

## Notes

### Thesis

[Thesis note text]

### Key Terms

- **[Term 1]**: [Definition]
- **[Term 2]**: [Definition]

### Arguments

1. [Argument text]
2. [Argument text]

### Interpretations

- [Interpretation text]
- [Interpretation text]

### Other Notes

- [General note]

---

*Exported from Melvil on [export date]*
```

---

## Acceptance Criteria

### Core Workflow
- [ ] User can create a workspace and add at least 3 sources in under 5 minutes.
- [ ] User can index a PDF and search its contents.
- [ ] `melvil synth find` returns results in under 1 second for 10k passages.
- [ ] User can capture a passage with `--from-pdf` and edit before saving.

### Provenance
- [ ] Every passage displays source title and page reference.
- [ ] Source snapshots include file hash when PDF is available.
- [ ] Export preserves all source references.

### Notes
- [ ] Workspace includes at least one each: thesis, term, argument, interpretation.
- [ ] Notes appear in export grouped by type.

### Export
- [ ] Export produces valid Markdown that renders correctly.
- [ ] Export includes all passages and notes with provenance.
- [ ] Re-export after changes produces updated file.

---

## Phase 2 Preview

The following are explicitly deferred to Phase 2:

- **Semantic search**: Embedding-based similarity search across passages.
- **Cross-library search**: Search all materials, not just workspace sources.
- **Concept extraction**: LLM-assisted concept and term identification.
- **Import sources**: Kindle highlights, Readwise, Apple Books.
- **Correction loops**: User corrections to LLM-generated content.
- **Term normalization**: Linking equivalent terms across sources.

---

## Technical Notes

### PDF Text Extraction
- Use `pdfplumber` or `PyMuPDF` for text extraction.
- Fall back gracefully for scanned PDFs (warn user, allow manual entry).
- Cache extracted text to avoid re-processing.

### FTS Implementation
- SQLite FTS5 with default tokenizer.
- Index on passage creation; rebuild on `melvil synth index`.
- Snippet generation for search results with `highlight()`.

### Performance Targets
- Workspace creation: < 100ms
- Add source (from Zotero): < 500ms
- Index source (per 100 pages): < 5 seconds
- Search (10k passages): < 500ms
- Export (100 items): < 1 second
