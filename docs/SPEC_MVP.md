# Melvil MVP Spec (Concept Mapping)

## Purpose

Melvil helps readers **map concepts across books** to build understanding incrementally. It externalizes the mental map that forms when reading broadly, tracking which books cover which concepts and how ideas connect.

**The MVP focuses on low-friction capture and basic visualization.** You capture thoughts as you read, concepts emerge from your notes, and you can see the map you're building. Structure can be explicit or can emerge from usage—the system supports both.

The system supports the workflow of a reader who:
- Reads broadly across many books
- Cannot read everything end-to-end
- Maps books shallowly first (TOC, key concepts)
- Builds a concept graph that spans sources
- Dives deeper selectively based on the map
- Takes notes while reading, refines structure later

---

## MVP Goals

1. **Low-friction capture** — Quick notes with implicit concept creation via `[[wikilinks]]`.
2. **Track books** with metadata, TOC, and reading depth.
3. **Map concepts** as first-class entities that span multiple books.
4. **Link concepts** to each other and to the books that discuss them.
5. **Write notes** tied to concepts and/or specific sources.
6. **See the map** — Basic visualization so you can actually see what you're building.

---

## Non-Goals (MVP)

- Structure notes and synthesis workflows (Phase 2)
- Advanced graph visualization with clustering (Phase 2)
- Reading suggestions based on concept gaps (Phase 2)
- Full-text search within PDFs (Phase 2)
- Passage-level capture with page references (Phase 2)
- Import from existing Zettelkasten tools (Phase 2)
- Spaced repetition or review workflows (Future)

---

## Core Concepts

### The Map

The central data structure is a **concept map**:

```
                    ┌─────────────┐
                    │  Concepts   │
                    │ (nodes)     │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐      ┌──────────┐      ┌─────────┐
    │ Links   │      │  Notes   │      │ Books   │
    │(edges)  │      │ (atoms)  │      │(sources)│
    └─────────┘      └──────────┘      └─────────┘
```

- **Concepts** are ideas that span multiple books (e.g., "CAP theorem", "consensus", "linearizability")
- **Books** are sources that discuss concepts
- **Links** connect concepts to each other (related, contradicts, prerequisite, etc.)
- **Notes** are atomic thoughts tied to concepts and/or sources

### Two Input Paths, One Data Model

**Explicit**: `melvil concept "consensus"` then `melvil concept link "consensus" --book "DDIA"`

**Quick capture**: `melvil note --book "DDIA" "[[consensus]] is equivalent to total order broadcast"`

Both create the same data: a concept, a note, links between them. The `[[wikilink]]` syntax is just a convenient alias for `--concept` that uses the same link-creation path. There's no separate storage mechanism—wikilinks are an input method, not a data structure.

### Reading Depth

Books have a **depth level** indicating how thoroughly they've been engaged:

| Depth | Meaning |
|-------|---------|
| `listed` | In the system but not yet examined |
| `mapped` | TOC reviewed, key concepts identified |
| `reading` | Currently being read |
| `read` | Read through, concepts and notes captured |
| `deep` | Studied deeply, passages extracted |

### Notes

Notes capture your thinking. They can be:
- **Quick captures** — Jotted while reading, refined later
- **Developed thoughts** — Fully articulated ideas

Standard notes can link to zero or one concept. Notes can link to multiple concepts only when the note is explicitly about their relationship (comparison, contrast, equivalence). Use `--type relation` for these.

Classification (fleeting/literature/permanent) is optional. The system doesn't enforce Zettelkasten orthodoxy—use it if it helps, ignore it if it doesn't.

---

## Data Model

### Books

```sql
books (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  authors TEXT,                 -- JSON array
  year INTEGER,
  type TEXT DEFAULT 'book',     -- 'book', 'paper', 'article'

  -- External references
  zotero_key TEXT,
  identifiers TEXT,             -- JSON: {isbn, doi, arxiv}

  -- Reading state
  depth TEXT DEFAULT 'listed',  -- 'listed', 'mapped', 'reading', 'read', 'deep'

  -- User's high-level notes on this book
  about TEXT,                   -- "What is this book about?" (your words)

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Chapters (TOC)

```sql
chapters (
  id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL REFERENCES books(id),

  -- Structure
  number TEXT,                  -- "1", "2.3", "IV", etc.
  title TEXT NOT NULL,
  parent_id INTEGER REFERENCES chapters(id),
  position INTEGER,             -- For ordering

  -- Optional metadata
  page_start INTEGER,
  page_end INTEGER,

  -- User annotation
  summary TEXT,                 -- Your summary of this chapter
  relevance TEXT                -- Why this chapter matters to you
)
```

### Concepts

```sql
concepts (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,

  -- Optional normalization
  aliases TEXT,                 -- JSON array: ["CAP", "Brewer's theorem"]

  -- User's understanding
  definition TEXT,              -- Your working definition

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Concept-Book Links

```sql
book_concepts (
  id INTEGER PRIMARY KEY,
  book_id INTEGER NOT NULL REFERENCES books(id),
  concept_id INTEGER NOT NULL REFERENCES concepts(id),

  -- Where in the book (all optional)
  chapter_id INTEGER REFERENCES chapters(id),
  location TEXT,                -- "Chapter 9", "pp. 300-350", etc.

  -- Your notes on this treatment (free text, optional)
  notes TEXT,                   -- How the book treats this concept, why it matters
)
```

Multiple mentions of the same concept in a book are allowed (e.g., different chapters or locations). Earlier designs included `treatment` (introduces/discusses/applies) and `importance` (central/significant/mentioned) fields. These were removed to reduce friction. If you want to note that DDIA "introduces" consensus, put it in the `notes` field. Structure that doesn't get used is worse than no structure.

### Concept Links (Graph Edges)

```sql
concept_links (
  id INTEGER PRIMARY KEY,
  from_concept_id INTEGER NOT NULL REFERENCES concepts(id),
  to_concept_id INTEGER NOT NULL REFERENCES concepts(id),

  -- Relationship type
  link_type TEXT NOT NULL,      -- 'related', 'prerequisite', 'contradicts', 'specializes', 'generalizes'

  -- Explanation
  notes TEXT,

  UNIQUE(from_concept_id, to_concept_id, link_type)
)
```

### Notes

```sql
notes (
  id INTEGER PRIMARY KEY,

  -- Content
  title TEXT,                   -- Optional short title
  body TEXT NOT NULL,           -- The note content (Markdown)

  -- Connections (all optional)
  book_id INTEGER REFERENCES books(id),
  chapter_id INTEGER REFERENCES chapters(id),

  -- Type
  note_type TEXT DEFAULT 'standard',  -- 'standard', 'relation'

  -- For quotes/passages
  source_location TEXT,         -- "DDIA p.336", "Ch. 9", etc.
  is_quote BOOLEAN DEFAULT FALSE,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Note-Concept Links

```sql
note_concepts (
  id INTEGER PRIMARY KEY,
  note_id INTEGER NOT NULL REFERENCES notes(id),
  concept_id INTEGER NOT NULL REFERENCES concepts(id),

  -- How link was created
  source TEXT DEFAULT 'explicit', -- 'explicit' or 'wikilink'

  UNIQUE(note_id, concept_id)
)
```

### Note Links

```sql
note_links (
  id INTEGER PRIMARY KEY,
  from_note_id INTEGER NOT NULL REFERENCES notes(id),
  to_note_id INTEGER NOT NULL REFERENCES notes(id),

  UNIQUE(from_note_id, to_note_id)
)
```


### Title Aliases

```sql
aliases (
  id INTEGER PRIMARY KEY,
  alias TEXT NOT NULL UNIQUE,
  book_id INTEGER NOT NULL REFERENCES books(id)
)
```

---

## CLI Surface

### Quick Capture (Low Friction Path)

```bash
# Capture a thought while reading
# [[wikilinks]] create concepts if needed and create concept links
melvil note "[[CAP theorem]] framing as 'pick 2 of 3' is misleading" --book "DDIA"

# Or specify explicitly:
melvil note "[[linearizability]] vs serializability" --concept "linearizability"

# Quick capture opens $EDITOR if no text provided
melvil note --book "DDIA"
```

The `[[wikilink]]` syntax is shorthand for `--concept`. It creates the concept if it doesn't exist and links the note to it. This is the same data as explicit commands—just faster to type.

### Book Management

```bash
# Add a book
melvil add "Designing Data-Intensive Applications" --author "Kleppmann" --year 2017
melvil add "DDIA" --from-zotero

# Set an alias for quick reference
melvil alias "DDIA" "Designing Data-Intensive Applications"

# View book details
melvil show "DDIA"

# Update reading depth
melvil depth "DDIA" mapped
melvil depth "DDIA" reading

# Add your summary of what the book is about
melvil about "DDIA" "Comprehensive guide to distributed systems from a data perspective."

# List books
melvil books                    # All books
melvil books --depth mapped     # Only mapped books
melvil books --concept "consensus"  # Books covering a concept
```

### TOC Management

```bash
# View table of contents (if captured)
melvil toc "DDIA"

# Add chapters manually
melvil toc add "DDIA" --number 9 --title "Consistency and Consensus" --pages 321-374

# Import TOC from PDF (extracts outline if available)
melvil toc import "DDIA" --from-pdf

# Add your summary to a chapter
melvil toc summarize "DDIA" --chapter 9 "Covers linearizability, consensus algorithms, and the relationship between them."
```

### Concept Management

```bash
# Create a concept explicitly (or let it be created implicitly via [[wikilinks]])
melvil concept "CAP theorem"
melvil concept "linearizability" --definition "Operations appear atomic and ordered"

# Add aliases
melvil concept alias "CAP theorem" "Brewer's theorem" "CAP"

# Link a concept to a book
melvil concept link "CAP theorem" --book "DDIA" --chapter 9
melvil concept link "CAP theorem" --book "DDIA" --note "Central to Ch. 9, good intro"

# Link concepts to each other
melvil concept relate "linearizability" "serializability" --note "Often confused but different"
melvil concept relate "consensus" "linearizability" --type prerequisite

# View a concept
melvil concept show "CAP theorem"

# List all concepts
melvil concepts
melvil concepts --book "DDIA"   # Concepts from a specific book (deduped)
melvil concepts --orphan        # Concepts with no links (cleanup candidates)

# Show per-mention rows for a book
melvil concept mentions --book "DDIA"
```

### Note Management

```bash
# Quick note with [[wikilinks]] (concepts created/linked automatically)
melvil note "[[CAP theorem]] 'pick 2 of 3' is misleading—partitions aren't optional"

# Note on a book (opens editor if no text)
melvil note --book "DDIA" "Kleppmann's [[consensus]] treatment bridges theory and practice well"

# Relation note with multiple concepts
melvil note --type relation --concept "consensus" --concept "linearizability" "How these interact in DDIA"

# Note with source location
melvil note --book "DDIA" --location "p.336" "Kleppmann calls [[CAP theorem]] 'unfortunate' terminology"

# Add a quote
melvil quote --book "DDIA" --location "p.324" "Linearizability is a recency guarantee..."

# Link notes to each other
melvil note link 42 57          # Link note #42 to note #57

# View and search notes
melvil notes                    # Recent notes
melvil notes --concept "CAP theorem"
melvil notes --book "DDIA"
melvil notes --draft            # Unrefined captures
melvil notes search "consensus"
melvil notes --type relation    # Relation notes only

# `--concept` results dedupe by note (a note linked to multiple concepts appears once)

# Refine a draft note
melvil note edit 42             # Opens in $EDITOR
```

### Exploring the Map

```bash
# See what books cover a concept
melvil map --concept "consensus"

# See what concepts a book covers
melvil map --book "DDIA"                 # Deduped by concept

# See concepts related to a concept
melvil map --related "linearizability"

# See the full concept graph (text representation)
melvil map

# Export the map
melvil export map --format markdown
melvil export map --format json
```

### Visualization (MVP)

```bash
# Open interactive graph view (TUI)
melvil viz

# Visualize a neighborhood (concept and its connections)
melvil viz --focus "consensus"

# Export for external tools
melvil export --format dot | dot -Tpng > map.png
melvil export --format obsidian    # Creates vault with [[wikilinks]]
```

The MVP includes basic visualization because a map you can't see isn't useful. The TUI shows concepts as nodes, links as edges, with keyboard navigation. It's not fancy, but it lets you see the structure.

---

## Workflows

### Workflow 1: Quick Capture While Reading (Low Friction)

```bash
# You're reading DDIA. Capture thoughts as you go:
$ melvil note --book "DDIA" "[[Linearizability]] is about recency, not transactions"
$ melvil note --book "DDIA" "[[CAP theorem]] framing is misleading—see p.336"
$ melvil note --book "DDIA" "[[consensus]] is equivalent to total order broadcast!"

# Later, see what emerged:
$ melvil concepts --book "DDIA"
  linearizability (3 notes)
  CAP theorem (1 note)
  consensus (2 notes)
  total order broadcast (1 note)  [NEW - created from wikilink]

# Add definitions to the concepts you care about:
$ melvil concept "linearizability" --definition "Recency guarantee for single-object ops"

# See the map you're building:
$ melvil viz --book "DDIA"
```

### Workflow 2: Structured Mapping (Deliberate)

```bash
# 1. Add the book
$ melvil add "DDIA" --from-zotero
Added: Designing Data-Intensive Applications (Kleppmann, 2017)

# 2. Import or add TOC
$ melvil toc import "DDIA" --from-pdf
Imported 12 chapters from PDF outline.

# 3. Note what the book is about
$ melvil about "DDIA" "Comprehensive treatment of distributed data systems..."

# 4. Identify key concepts and link them
$ melvil concept link "replication" --book "DDIA" --chapter 5
$ melvil concept link "partitioning" --book "DDIA" --chapter 6
$ melvil concept link "consensus" --book "DDIA" --chapter 9 --note "Central chapter, very clear"

# 5. Mark as mapped
$ melvil depth "DDIA" mapped
```

### Workflow 3: Build Concept Understanding

```bash
# 1. Create concept with working definition
$ melvil concept "linearizability" --definition "Operations appear atomic at a single point in time"

# 2. Link to books that discuss it
$ melvil concept link "linearizability" --book "DDIA" --chapter 9
$ melvil concept link "linearizability" --book "Database Internals" --chapter 11

# 3. Relate to other concepts
$ melvil concept relate "linearizability" "serializability" --note "Often confused, but different"
$ melvil concept relate "linearizability" "consensus" --type prerequisite

# 4. See the full picture
$ melvil concept show "linearizability"
$ melvil viz --focus "linearizability"
```

## Output Examples

### `melvil show "DDIA"`

```
Designing Data-Intensive Applications
═════════════════════════════════════
Author: Martin Kleppmann
Year: 2017
Depth: mapped

About:
Comprehensive guide to distributed systems from a data perspective.
Covers storage, replication, partitioning, transactions, and stream processing.

Concepts (8):
  • replication (Ch. 5) - central
  • partitioning (Ch. 6) - central
  • transactions (Ch. 7) - central
  • consensus (Ch. 9) - central
  • linearizability (Ch. 9) - significant
  • serializability (Ch. 7) - significant
  • CAP theorem (Ch. 9) - discussed
  • eventual consistency (Ch. 5) - discussed

Notes: 12
```

### `melvil concept show "consensus"`

```
consensus
═════════
Definition: Agreement among distributed nodes on a single value

Aliases: distributed consensus, consensus protocol

Related concepts:
  → linearizability (related)
  → Paxos (specializes)
  → Raft (specializes)
  → total order broadcast (related)
  ← fault tolerance (prerequisite)

Books (4):
  • DDIA, Ch. 9 [mapped] — "Central chapter, very clear"
  • Database Internals, Ch. 14 [listed]
  • Paxos Made Simple [listed]
  • Raft paper [reading]

Notes (3):
  #42: "Consensus and total order broadcast are equivalent..."
  #57: "FLP impossibility: no deterministic consensus in async system..."
  #63: "Practical systems use timeouts to circumvent FLP..."

[View graph: melvil viz --focus "consensus"]
```

### `melvil map`

```
Concept Map (47 concepts, 12 books)
═══════════════════════════════════

distributed systems
├── consensus
│   ├── Paxos
│   ├── Raft
│   └── atomic broadcast
├── replication
│   ├── leader-follower
│   ├── multi-leader
│   └── leaderless
├── consistency models
│   ├── linearizability
│   ├── serializability
│   ├── eventual consistency
│   └── causal consistency
└── fault tolerance
    ├── Byzantine faults
    └── crash faults

[47 concepts across 12 books, 156 notes]
```

---

## Export Format

### Markdown Export (`melvil export map`)

```markdown
# Concept Map

*Exported from Melvil on 2024-01-15*

## Books (12)

### Designing Data-Intensive Applications
- **Author**: Martin Kleppmann (2017)
- **Depth**: mapped
- **About**: Comprehensive guide to distributed systems...
- **Concepts**: replication, partitioning, transactions, consensus, linearizability...

### Database Internals
...

## Concepts (47)

### consensus
- **Definition**: Agreement among distributed nodes on a single value
- **Related**: linearizability, Paxos, Raft, atomic broadcast
- **Books**: DDIA (Ch. 9), Database Internals (Ch. 14), Paxos Made Simple, Raft paper

#### Notes
1. Consensus and total order broadcast are equivalent...
2. FLP impossibility: no deterministic consensus in async system...

### linearizability
...

## Notes (156)

### #42: Consensus equivalence
- **Concept**: consensus
- **Source**: DDIA p.349
- **Type**: permanent

Consensus and total order broadcast are equivalent problems...

### #43: ...
```

---

## Acceptance Criteria

### Quick Capture
- [ ] `melvil note "text with [[concept]]"` creates note and concept in one command
- [ ] Concepts mentioned via `[[wikilinks]]` are created if they don't exist
- [ ] Notes can be created without explicit concept/book flags

### Books
- [ ] User can add a book manually or from Zotero
- [ ] User can set and view reading depth
- [ ] User can add "about" summary to a book
- [ ] User can import TOC from PDF or add manually

### Concepts
- [ ] User can create concepts with definitions
- [ ] User can link concepts to books with optional notes
- [ ] User can relate concepts to each other with typed links
- [ ] `melvil concept show` displays full concept context

### Notes
- [ ] User can create notes linked to concepts, books, or both
- [ ] User can link notes to each other
- [ ] Notes are searchable by content
- [ ] `[[wikilinks]]` in note body are parsed and linked
- [ ] `--type relation` allows multiple concept links
- [ ] `melvil notes --type relation` filters by note type

### Visualization
- [ ] `melvil viz` opens interactive TUI graph view
- [ ] `melvil viz --focus X` shows concept X and its neighborhood
- [ ] Graph is navigable via keyboard
- [ ] Export to DOT format works

### Map
- [ ] `melvil map` shows concept overview
- [ ] `melvil map --concept X` shows books covering X (deduped)
- [ ] `melvil map --book X` shows concepts in X (deduped)
- [ ] `melvil concept mentions --book X` shows per-mention rows
- [ ] Export produces valid Markdown

### Performance
- [ ] All commands respond in < 500ms for 100 books, 500 concepts, 1000 notes
- [ ] Visualization renders in < 2s for 200 concepts

---

## Phase 2 Preview

Phase 1 (MVP) includes basic visualization. Phase 2 adds:

- **Advanced visualization**: Clustering, landmarks, web-based view
- **Structure notes**: Organize notes into synthesis documents
- **Passage capture**: Deep reading with page-level provenance
- **Full-text search**: Search within indexed PDFs
- **Gap analysis**: "You've mapped X but not read about Y which is prerequisite"
- **Session tracking**: "Where was I?" when returning after time away
- **Import**: Obsidian vault, Roam, existing Zettelkasten
- **Export**: Notion, Anki

---

## Technical Notes

### SQLite
- All data in single SQLite file
- FTS5 for note search
- JSON columns for arrays (authors, aliases, identifiers)

### Wikilink Parsing
- Parse `[[concept name]]` from note body on save
- Case-insensitive matching against existing concepts
- Create concept if no match found (name = wikilink text, no definition)
- Use the same concept-linking behavior as `--concept` (writes to `note_concepts`)
- Re-parse on note edit to update `source='wikilink'` links only; explicit links are preserved
- If a link exists as both wikilink and explicit, store a single `source='explicit'` row
- Alias resolution: match against concept names and aliases (case-insensitive); create only if no match
- Alias collision: if multiple concepts match, error and require explicit `--concept`
- For `note_type='standard'`, multiple concept links are rejected; use `--type relation` instead

### Link Lifecycle (Source of Truth)
- `note_concepts` is canonical for note-to-concept links
- `source='explicit'` links are created via `--concept` and never modified by wikilink re-parse
- `source='wikilink'` links are derived from note body and are replaced on each re-parse

### Visualization (TUI)
- Use Textual for terminal-based graph view
- Force-directed layout (simple spring model)
- Keyboard navigation: arrow keys to move focus, enter to expand
- Color coding: concepts by connection count, books by depth

### PDF TOC Extraction
- Use PyMuPDF to extract PDF outline
- Fall back to manual entry if no outline

### Zotero Integration
- Read from local Zotero SQLite database
- Map Zotero items to books table
- Preserve zotero_key for sync

### Title Resolution
Same as before: alias → exact → prefix → fuzzy matching. Alias collisions require explicit disambiguation.
