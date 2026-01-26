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
5. **Structure can be explicit or emergent** — Build deliberately or let it emerge from `[[wikilinks]]`
6. **The map grows and is pruned** — Understanding accumulates; noise is archived
7. **A map you can't see isn't useful** — Basic visualization is essential, not a luxury

## Two Paths to Structure

**Explicit structure**: Create concepts deliberately, define them, link them carefully.

**Emergent structure**: Write notes with `[[concept]]` mentions, concepts are created implicitly, refine later.

Both paths lead to the same map. The system supports quick capture when reading and deliberate structuring when reflecting. Most users will mix both approaches.

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

### Notes

Notes capture your thinking. The system uses a simple status model:

| Status | Meaning |
|--------|---------|
| **draft** | Quick capture, not yet refined |
| **active** | Normal note, part of the working map |
| **archived** | Hidden from default views, still queryable |

**Zettelkasten note types** (fleeting/literature/permanent) are valid mental models but aren't enforced by the system. If you want to track them, use tags or a naming convention. The system doesn't require classification overhead for every note.

**Structure notes** (Phase 2) organize other notes into synthesis documents. They don't contain new ideas—they arrange existing notes into coherent arguments.

---

## Phased Delivery

### Phase 1: Concept Mapping (MVP)

**Goal**: Low-friction capture, basic visualization, map maintenance.

**Capabilities**:
- Add books from Zotero or manually
- Capture table of contents
- Create concepts explicitly or implicitly via `[[wikilinks]]`
- Link concepts to books and to each other
- Write notes with `[[concept]]` mentions (auto-linking)
- **Basic TUI visualization** — see the graph you're building
- **Maintenance tools** — merge duplicates, archive stale concepts
- Export to Markdown, DOT, Obsidian format

**See**: `SPEC_MVP.md` for complete specification.

### Phase 2: Advanced Navigation, Synthesis & Deep Reading

**Goal**: Advanced navigation, synthesis workflows, and deep reading support.

Phase 1 provides basic visualization. Phase 2 adds **advanced navigation aids** for complex maps and **synthesis workflows** for turning accumulated notes into coherent output.

**Capabilities**:

*Advanced Navigation:*
- **Web-based visualization**: Richer interaction than TUI allows
- **Landmarks**: Mark key concepts as navigation anchors / entry points
- **Path finding**: Show how two concepts connect through the graph
- **Session tracking**: "Where was I?" context when returning to the map
- **Clustering**: Auto-detect and visualize concept communities

*Synthesis:*
- **Structure notes**: Organize notes into synthesis documents
- **Synthesis workflow**: Assemble notes on a topic into coherent arguments

*Deep Reading:*
- **Passage capture**: Extract quotes with page-level provenance
- **Full-text search**: Search within indexed PDFs
- **Gap analysis**: Identify concepts you've mapped but not understood deeply
- **Reading suggestions**: "To understand X, you might read Y"

**New data structures**:

```sql
-- Structure notes organize other notes into synthesis
-- (note_type = 'structure' in notes table)

-- Items within a structure note
structure_note_items (
  id INTEGER PRIMARY KEY,
  structure_note_id INTEGER NOT NULL REFERENCES notes(id),

  -- What this item references (one of these)
  referenced_note_id INTEGER REFERENCES notes(id),
  referenced_concept_id INTEGER REFERENCES concepts(id),

  -- Position in the structure
  position INTEGER NOT NULL,

  -- Commentary on this item within the synthesis
  commentary TEXT,

  UNIQUE(structure_note_id, position)
)

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

**Synthesis workflow**:

The synthesis capability bridges accumulation and output. After building up notes over time, users create **structure notes** that organize existing notes into coherent arguments.

```bash
# After months of accumulation...
melvil map --concept "consensus"
# "47 notes across 8 books. Time to synthesize."

# Create a structure note
melvil synthesize "Understanding Consensus"

# Add notes and concepts to the structure
melvil synth add-note 42
melvil synth add-note 57 --comment "Contradicts #42 on timing"
melvil synth add-concept "Paxos"           # All notes on Paxos
melvil synth add-concept "Raft" --notes 63,67  # Specific notes

# Arrange and review
melvil synth reorder "Understanding Consensus"
melvil synth show "Understanding Consensus"

# Export as document
melvil synth export "Understanding Consensus"
```

**Synthesis export format**:

```markdown
# Understanding Consensus

*Synthesized from 23 notes across 5 books*

## The Core Problem

> [Note #42] Consensus is fundamentally about agreement...

> [Note #57] FLP impossibility shows we can't have it all...

*Commentary: These establish the theoretical foundation.*

## Practical Solutions

### Paxos
> [Note #63] Paxos solves consensus but is notoriously difficult...

### Raft
> [Note #67] Raft was designed for understandability...

*Commentary: Raft is essentially Paxos made teachable.*

---
Sources: DDIA, Paxos Made Simple, Raft Paper, Database Internals
```

**Navigation data structures**:

```sql
-- Landmarks: key concepts that serve as navigation anchors
-- (stored as a flag on concepts table or separate table)
landmarks (
  id INTEGER PRIMARY KEY,
  concept_id INTEGER NOT NULL UNIQUE REFERENCES concepts(id),
  notes TEXT,                   -- Why this is a landmark
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Session tracking: where was the user last exploring
sessions (
  id INTEGER PRIMARY KEY,
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  last_concept_id INTEGER REFERENCES concepts(id),
  last_book_id INTEGER REFERENCES books(id),
  breadcrumbs TEXT              -- JSON array of recent concept IDs
)
```

**Navigation commands**:

```bash
# Mark a concept as a landmark (navigation anchor)
melvil landmark "distributed systems"
melvil landmark "consensus" --note "Core concept for understanding coordination"

# View landmarks
melvil landmarks

# Find path between two concepts
melvil path "CAP theorem" "Raft"
# Output: CAP theorem → consistency → linearizability → consensus → Raft

# See recent activity
melvil recent
# Output: Last session 3 days ago. Exploring: consensus → Raft → leader election

# Resume where you left off
melvil resume

# View concept clusters (auto-detected communities)
melvil clusters
```

**Visualization approaches** (to be validated):
- Terminal: Tree view with Rich, interactive graph with Textual
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

  -- Lifecycle
  archived BOOLEAN DEFAULT FALSE,           -- Hidden from default views
  merged_into_id INTEGER REFERENCES concepts(id),  -- If merged into another

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_concepts_parent ON concepts(parent_id);
CREATE INDEX idx_concepts_archived ON concepts(archived) WHERE NOT archived;
```

### Book-Concept Links

```sql
CREATE TABLE book_concepts (
  id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
  concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,

  -- Location (optional)
  chapter_id INTEGER REFERENCES chapters(id),
  location TEXT,                -- Free text: "Ch. 9", "pp. 300-350"

  -- Your notes on how this book treats the concept (free text)
  notes TEXT,

  UNIQUE(book_id, concept_id)
);

CREATE INDEX idx_book_concepts_book ON book_concepts(book_id);
CREATE INDEX idx_book_concepts_concept ON book_concepts(concept_id);
```

Note: Earlier designs included `treatment` (introduces/discusses/etc.) and `importance` (central/significant/mentioned) enum fields. These were removed to reduce friction—users rarely filled them consistently, and free-text notes serve the same purpose without requiring micro-decisions on every link.

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

  -- Content (body supports [[wikilinks]] for concept mentions)
  title TEXT,
  body TEXT NOT NULL,

  -- Primary connections (optional — concepts can also link via [[wikilinks]] in body)
  concept_id INTEGER REFERENCES concepts(id) ON DELETE SET NULL,  -- Primary concept
  book_id INTEGER REFERENCES books(id) ON DELETE SET NULL,
  chapter_id INTEGER REFERENCES chapters(id) ON DELETE SET NULL,

  -- Source location (for quotes)
  source_location TEXT,         -- "p.336", "Ch. 9, §3"
  is_quote BOOLEAN DEFAULT FALSE,

  -- Status
  status TEXT DEFAULT 'active',  -- 'draft', 'active', 'archived'

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notes_concept ON notes(concept_id);
CREATE INDEX idx_notes_book ON notes(book_id);
CREATE INDEX idx_notes_status ON notes(status);
```

### Note-Concept Links

```sql
-- Links from [[wikilinks]] in note body, plus explicit links
CREATE TABLE note_concepts (
  id INTEGER PRIMARY KEY,
  note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,

  -- How link was created
  source TEXT DEFAULT 'wikilink',  -- 'wikilink' (parsed from body), 'explicit'

  UNIQUE(note_id, concept_id)
);

CREATE INDEX idx_note_concepts_note ON note_concepts(note_id);
CREATE INDEX idx_note_concepts_concept ON note_concepts(concept_id);
```

When a note body contains `[[consensus]]`, the system:
1. Finds or creates a concept named "consensus"
2. Creates a row in `note_concepts` with `source='wikilink'`
3. Re-parses on note edit to keep links current

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
├── note <text>                 # Quick capture with [[wikilinks]] (most common)
├── quote                       # Create a quote note
├── notes                       # List/search notes
│
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
│   ├── merge                   # Merge two concepts
│   ├── archive                 # Archive a concept
│   ├── restore                 # Restore archived concept
│   └── show                    # Show concept details
├── concepts                    # List concepts (--orphan, --stale, --archived)
│
├── map                         # Show concept map (text)
├── viz                         # Interactive graph visualization (TUI)
│
├── cleanup                     # Maintenance: find/archive orphans
│
├── landmark <concept>          # Mark as navigation anchor (Phase 2)
├── landmarks                   # List landmarks (Phase 2)
├── path <from> <to>            # Find connection path (Phase 2)
├── recent                      # Show recent activity (Phase 2)
├── resume                      # Resume last session (Phase 2)
├── clusters                    # Show concept clusters (Phase 2)
│
├── synthesize <title>          # Create structure note (Phase 2)
├── synth                       # Synthesis commands (Phase 2)
│   ├── show / list / add-note / add-concept / reorder / export
│
├── export                      # Export data
│   ├── --format markdown       # Markdown export
│   ├── --format dot            # Graphviz DOT
│   ├── --format obsidian       # Obsidian vault with [[wikilinks]]
│   └── --format json           # Full data export
│
└── zotero
    └── sync                    # Sync from Zotero
```

### Design Principles

1. **Quick capture first**: `melvil note` is the most common command
2. **Titles over IDs**: `melvil show "DDIA"` not `melvil show 42`
3. **Implicit concept creation**: `[[wikilinks]]` create concepts automatically
4. **Progressive detail**: `melvil books` → `melvil show X` → `melvil concept show Y`
5. **Maintenance is normal**: Merge, archive, and cleanup are first-class operations

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
| Time to capture a thought | < 15 seconds (quick note with [[wikilinks]]) |
| Time to map a book | < 5 minutes for TOC + 5 concepts |
| Time to find books covering a concept | < 500ms |
| Graph rendering (TUI) | < 2 seconds for 200 concepts |
| Merge two concepts | < 5 seconds |
| Map export completeness | 100% of data included |

### Phase 2

| Metric | Target |
|--------|--------|
| Time to re-orient after 6 months | < 2 minutes using landmarks + recent |
| Path finding | < 500ms for 500-concept graph |
| Web graph rendering | < 2 seconds for 500 concepts |
| Cluster detection | < 5 seconds for 500 concepts |
| Structure note creation | < 1 minute to create and add 10 notes |
| Synthesis export | < 2 seconds for 50-note structure |
| Passage capture | < 30 seconds per passage |
| FTS latency | < 500ms for 10k notes |

---

## Anti-Patterns to Avoid

1. **Premature structure** — Don't force hierarchy on concepts too early; let structure emerge
2. **Capture without connection** — Notes should link to something (but `[[wikilinks]]` make this easy)
3. **All mapping, no reading** — The map serves reading, not the reverse
4. **Precision theater** — Page numbers are useful; enum classifications usually aren't
5. **Tool over thinking** — Melvil assists thinking; it doesn't replace it
6. **Infinite accumulation** — Without maintenance, the map becomes a junk drawer
7. **Ceremony over capture** — If adding a thought takes more than 15 seconds, something is wrong

---

## Reading Integration

Melvil is a **capture and mapping tool**, not a reading tool. Reading happens elsewhere:
- Physical books
- Kindle / e-readers
- PDF readers (Preview, Acrobat, Zotero)
- Web browsers

The workflow is: read → capture thought → return to reading.

**Design implications**:
- Quick capture (`melvil note`) must be fast enough to not break reading flow
- `[[wikilinks]]` reduce the overhead of linking
- Draft status lets you capture rough thoughts now, refine later
- Mobile/web capture is a future consideration (not MVP)

**Future possibilities** (not committed):
- Browser extension for capture while reading online
- Readwise integration for highlight import
- Kindle clippings import

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
