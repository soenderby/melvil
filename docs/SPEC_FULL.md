# Melvil System Spec

## Purpose

Melvil is a **concept mapping system** for readers who learn by connecting ideas across sources. It externalizes the mental map that forms when reading broadly—tracking books, the concepts they contain, and how ideas relate.

Named after Melvil Dewey, the system helps readers who:
- Read broadly across many books and papers
- Cannot possibly read everything end-to-end
- Map sources shallowly first, then dive deep selectively
- Build understanding through connections, not isolated facts
- Think in a Zettelkasten or networked-note style

---

## Core Problem

Readers building expertise face a structural challenge:

1. **Too many sources** — More relevant books exist than time to read them
2. **Knowledge is networked** — Understanding comes from connections across sources, not from any single book
3. **The map is in your head** — Mental connections are fragile and hard to navigate
4. **Deep reading is selective** — You can only go deep on some things; you need to choose wisely

Melvil addresses this by making the concept map **explicit, persistent, and navigable**.

---

## Design Principles

1. **Concepts are first-class** — Ideas exist independent of any single source
2. **Shallow before deep** — Map a book's territory before committing to read it
3. **Sources as evidence** — Books support and develop concepts; they don't own them
4. **Notes are atomic** — One idea per note, linked to concepts and sources
5. **The map grows** — Understanding accumulates; nothing is lost

---

## Conceptual Model

### The Knowledge Graph

```
                     ┌─────────────────────────────────┐
                     │           CONCEPTS              │
                     │  (ideas that span sources)      │
                     └─────────────┬───────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
     ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
     │  CONCEPT LINKS  │  │     NOTES       │  │  BOOK-CONCEPT   │
     │  (relationships │  │ (your thinking) │  │     LINKS       │
     │   between ideas)│  │                 │  │ (where concepts │
     └─────────────────┘  └─────────────────┘  │  are discussed) │
                                   │           └────────┬────────┘
                                   │                    │
                                   ▼                    ▼
                          ┌─────────────────┐  ┌─────────────────┐
                          │  NOTE LINKS     │  │     BOOKS       │
                          │ (connections    │  │   (sources)     │
                          │  between notes) │  └────────┬────────┘
                          └─────────────────┘           │
                                                       ▼
                                               ┌─────────────────┐
                                               │    CHAPTERS     │
                                               │   (structure)   │
                                               └─────────────────┘
```

### Reading Depth Progression

Books move through depth levels as engagement increases:

```
listed → mapped → reading → read → deep
   │        │        │        │       │
   │        │        │        │       └── Passages extracted, detailed notes
   │        │        │        └────────── Read through, concepts solidified
   │        │        └─────────────────── Currently reading
   │        └──────────────────────────── TOC reviewed, concepts identified
   └───────────────────────────────────── In system, not yet examined
```

### Note Types (Zettelkasten)

Following Ahrens' interpretation of Luhmann's system:

| Type | Purpose | Lifecycle |
|------|---------|-----------|
| **Fleeting** | Quick captures, unprocessed thoughts | Temporary; process into permanent or delete |
| **Literature** | Summarizes a source in your words | Stays attached to source |
| **Permanent** | Your own thinking, fully developed | Joins the concept network |

---

## Phased Delivery

### Phase 1: Concept Mapping (MVP)

**Goal**: Build and navigate the concept map.

**Capabilities**:
- Add books from Zotero or manually
- Capture table of contents
- Create concepts with definitions
- Link concepts to books (with location, treatment, importance)
- Link concepts to each other (related, prerequisite, contradicts, etc.)
- Write atomic notes tied to concepts and/or sources
- Explore the map via CLI

**See**: `SPEC_MVP.md` for complete specification.

### Phase 2: Deep Reading & Visualization

**Goal**: Support deep reading and make the map visual.

**Capabilities**:
- **Passage capture**: Extract quotes with page-level provenance
- **Full-text search**: Search within indexed PDFs
- **Graph visualization**: Interactive concept map (TUI or web)
- **Gap analysis**: Identify concepts you've mapped but not understood deeply
- **Reading suggestions**: "To understand X, you might read Y"

**New data structures**:

```sql
-- Passages for deep reading
passages (
  id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL REFERENCES books(id),
  chapter_id INTEGER REFERENCES chapters(id),

  -- Location
  page_start INTEGER,
  page_end INTEGER,

  -- Content
  text TEXT NOT NULL,

  -- Source verification
  source_hash TEXT,             -- Hash of PDF at capture time

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Connect passages to concepts
passage_concepts (
  id INTEGER PRIMARY KEY,
  passage_id INTEGER NOT NULL REFERENCES passages(id),
  concept_id INTEGER NOT NULL REFERENCES concepts(id),
  notes TEXT
)

-- Full-text search index
notes_fts USING fts5(title, body, content=notes)
passages_fts USING fts5(text, content=passages)
```

**Visualization approaches** (to be validated):
- Terminal: Tree view with Rich, graph with Textual
- Web: Force-directed graph with D3.js or similar
- Export: Graphviz DOT format, Obsidian canvas

### Phase 3: Intelligence & Integration

**Goal**: Help navigate the map and connect to other tools.

**Capabilities**:
- **Concept suggestions**: "This passage seems to discuss [concept]"
- **Relationship inference**: "X and Y often appear together; are they related?"
- **Import**: Obsidian vault, Roam export, existing Zettelkasten
- **Export**: Obsidian (with links), Anki (for review), Notion
- **Embeddings**: Semantic similarity for concept and note discovery

**LLM assistance** (optional, user-controlled):
- Extract concepts from TOC
- Suggest concept definitions
- Identify potential note links
- All suggestions require user confirmation

### Future Possibilities

Not committed, but potential directions:
- **Collaborative maps**: Share concept graphs with others
- **Spaced repetition**: Review notes and concepts over time
- **Citation graphs**: Import citation relationships between papers
- **Reading groups**: Coordinate reading across a team

---

## Data Model (Complete)

### Books

```sql
CREATE TABLE books (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  authors TEXT,                 -- JSON array
  year INTEGER,
  type TEXT DEFAULT 'book',     -- 'book', 'paper', 'article', 'chapter'

  -- External references
  zotero_key TEXT,
  identifiers TEXT,             -- JSON: {isbn, doi, arxiv, url}
  file_path TEXT,               -- Path to PDF/EPUB if available

  -- Reading state
  depth TEXT DEFAULT 'listed',  -- 'listed', 'mapped', 'reading', 'read', 'deep'

  -- User's high-level understanding
  about TEXT,                   -- "What is this book about?"

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_books_depth ON books(depth);
CREATE INDEX idx_books_zotero ON books(zotero_key);
```

### Chapters

```sql
CREATE TABLE chapters (
  id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,

  -- Structure
  number TEXT,                  -- "1", "2.3", "IV", "Part I"
  title TEXT NOT NULL,
  parent_id INTEGER REFERENCES chapters(id),
  position INTEGER NOT NULL,    -- Sort order within parent

  -- Location
  page_start INTEGER,
  page_end INTEGER,

  -- User annotations
  summary TEXT,
  relevance TEXT,

  UNIQUE(book_id, number)
);

CREATE INDEX idx_chapters_book ON chapters(book_id);
```

### Concepts

```sql
CREATE TABLE concepts (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE COLLATE NOCASE,

  -- Variants
  aliases TEXT,                 -- JSON array: ["CAP", "Brewer's theorem"]

  -- User's understanding
  definition TEXT,

  -- Organization (optional hierarchy)
  parent_id INTEGER REFERENCES concepts(id),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_concepts_parent ON concepts(parent_id);
```

### Book-Concept Links

```sql
CREATE TABLE book_concepts (
  id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,

  -- Location
  chapter_id INTEGER REFERENCES chapters(id),
  location TEXT,                -- Free text: "Ch. 9", "pp. 300-350"

  -- Classification
  treatment TEXT,               -- 'introduces', 'discusses', 'applies', 'critiques', 'mentions'
  importance TEXT,              -- 'central', 'significant', 'mentioned'

  -- Your notes on this treatment
  notes TEXT,

  UNIQUE(book_id, concept_id)
);

CREATE INDEX idx_book_concepts_book ON book_concepts(book_id);
CREATE INDEX idx_book_concepts_concept ON book_concepts(concept_id);
```

### Concept Links

```sql
CREATE TABLE concept_links (
  id INTEGER PRIMARY KEY,
  from_concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  to_concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,

  -- Relationship
  link_type TEXT NOT NULL,      -- 'related', 'prerequisite', 'contradicts', 'specializes', 'generalizes', 'implements'

  -- Direction matters for some types
  -- prerequisite: from requires to
  -- specializes: from is a specific case of to
  -- generalizes: from is a general case of to

  notes TEXT,

  UNIQUE(from_concept_id, to_concept_id, link_type),
  CHECK(from_concept_id != to_concept_id)
);

CREATE INDEX idx_concept_links_from ON concept_links(from_concept_id);
CREATE INDEX idx_concept_links_to ON concept_links(to_concept_id);
```

### Notes

```sql
CREATE TABLE notes (
  id INTEGER PRIMARY KEY,

  -- Content
  title TEXT,
  body TEXT NOT NULL,

  -- Connections (all optional, at least one recommended)
  concept_id INTEGER REFERENCES concepts(id) ON DELETE SET NULL,
  book_id INTEGER REFERENCES books(id) ON DELETE SET NULL,
  chapter_id INTEGER REFERENCES chapters(id) ON DELETE SET NULL,

  -- Source location (for literature notes)
  source_location TEXT,         -- "p.336", "Ch. 9, §3"
  is_quote BOOLEAN DEFAULT FALSE,

  -- Zettelkasten type
  note_type TEXT DEFAULT 'permanent',  -- 'fleeting', 'literature', 'permanent'

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notes_concept ON notes(concept_id);
CREATE INDEX idx_notes_book ON notes(book_id);
CREATE INDEX idx_notes_type ON notes(note_type);
```

### Note Links

```sql
CREATE TABLE note_links (
  id INTEGER PRIMARY KEY,
  from_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  to_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,

  UNIQUE(from_note_id, to_note_id),
  CHECK(from_note_id != to_note_id)
);

CREATE INDEX idx_note_links_from ON note_links(from_note_id);
CREATE INDEX idx_note_links_to ON note_links(to_note_id);
```

### Aliases

```sql
CREATE TABLE aliases (
  id INTEGER PRIMARY KEY,
  alias TEXT NOT NULL UNIQUE COLLATE NOCASE,
  book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE
);
```

---

## CLI Design

### Command Hierarchy

```
melvil
├── add <title>                 # Add a book
├── show <title>                # Show book details
├── books                       # List books
├── depth <title> <level>       # Set reading depth
├── about <title> <text>        # Set book description
├── alias <alias> <title>       # Create book alias
│
├── toc <title>                 # Show table of contents
│   ├── add                     # Add chapter
│   ├── import                  # Import from PDF
│   └── summarize               # Add chapter summary
│
├── concept <name>              # Create/show concept
│   ├── alias                   # Add concept alias
│   ├── link                    # Link concept to book
│   ├── relate                  # Link concept to concept
│   └── show                    # Show concept details
├── concepts                    # List concepts
│
├── note                        # Create a note
├── quote                       # Create a quote note
├── notes                       # List/search notes
│
├── map                         # Show concept map
│
├── export                      # Export data
│   ├── map                     # Export concept map
│   └── notes                   # Export notes
│
└── zotero
    └── sync                    # Sync from Zotero
```

### Design Principles

1. **Titles over IDs**: `melvil show "DDIA"` not `melvil show 42`
2. **Aliases for convenience**: Short names for frequently used books
3. **Progressive detail**: `melvil books` → `melvil show X` → `melvil concept show Y`
4. **Composable commands**: Each command does one thing well

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Database | SQLite | Single file, relational, FTS5 built-in |
| CLI | Click + Rich | Standard Python, beautiful output |
| PDF parsing | PyMuPDF | Extract TOC outlines, text (Phase 2) |
| Zotero | Direct SQLite + pyzotero | Fast local access, API fallback |
| Graph viz (Phase 2) | Textual (TUI) or D3.js (web) | TBD based on user preference |

### Why SQLite?

- **Single file**: Easy backup, sync, portability
- **Relational**: Graph queries via joins and CTEs
- **FTS5**: Full-text search built-in
- **JSON**: JSON columns for flexible arrays
- **Transactions**: ACID guarantees for data integrity

---

## Integration Points

### Zotero

- **Import**: Sync books and metadata from Zotero library
- **Link**: Preserve `zotero_key` for bidirectional reference
- **Non-destructive**: Melvil reads from Zotero; never writes back

### Export Targets (Phase 2-3)

| Target | Format | Use Case |
|--------|--------|----------|
| Obsidian | Markdown + `[[links]]` | Integrate with existing vault |
| Notion | Markdown | Share or collaborate |
| Anki | CSV/APKG | Spaced repetition review |
| Graphviz | DOT | Visualize elsewhere |
| JSON | Full export | Backup, migration |

### Import Sources (Phase 3)

| Source | What | How |
|--------|------|-----|
| Obsidian | Notes, links | Parse `[[wikilinks]]` |
| Roam | Notes, hierarchy | JSON export |
| Kindle | Highlights | My Clippings.txt |
| Readwise | Highlights | API or export |

---

## Evaluation Metrics

### Phase 1

| Metric | Target |
|--------|--------|
| Time to map a book | < 5 minutes for TOC + 5 concepts |
| Time to create a concept | < 10 seconds |
| Time to find books covering a concept | < 500ms |
| Map export completeness | 100% of data included |

### Phase 2

| Metric | Target |
|--------|--------|
| Graph rendering | < 2 seconds for 100 concepts |
| Passage capture | < 30 seconds per passage |
| FTS latency | < 500ms for 10k notes |

---

## Anti-Patterns to Avoid

1. **Premature structure** — Don't force hierarchy on concepts too early
2. **Capture without connection** — Notes should link to something
3. **All mapping, no reading** — The map serves reading, not the reverse
4. **Precision theater** — Page numbers are useful; file hashes usually aren't
5. **Tool over thinking** — Melvil assists thinking; it doesn't replace it

---

## Open Questions

See `QUESTIONS.md` for design questions requiring validation.

---

## Document Index

| Document | Purpose | Status |
|----------|---------|--------|
| `SPEC_MVP.md` | Phase 1 specification | Active |
| `SPEC_FULL.md` | Full system vision (this doc) | Active |
| `QUESTIONS.md` | Open design questions | Active |
| `semantic_archive_design_orientation_literature_guide.md` | Conceptual foundations | Reference |
| `AGENTS.md` | Developer guidelines | Active |
| `docs/archive/*` | Historical documents | Archived |
