# Melvil: Learning-Directed Knowledge Management System

## Design Document v2.0

**Date:** January 22, 2026
**Conceptual Foundation:** Adler & Van Doren's "How to Read a Book"

---

## 1. Vision

Melvil helps readers answer the fundamental question: **"What should I read next, and how should I read it?"**

In a world of infinite reading material and finite time, most books don't need cover-to-cover reading. Melvil applies the principles of inspectional, analytical, and syntopical reading at scale—helping users discover what's worth their attention, which parts matter most, and how materials connect to their learning goals.

### The End State

A fully-realized Melvil will:

- **Understand your knowledge**: Track what you know and what you're trying to learn
- **Map the terrain**: Build a knowledge graph connecting concepts, materials, and prerequisites
- **Guide your path**: Generate personalized learning paths across your entire library
- **Save your time**: Identify the 50 pages that matter from a 500-page book
- **Capture serendipity**: Hold interesting discoveries until they become relevant

### The Guiding Principle

> The system does not replace reading—it directs attention to what's worth reading.

---

## 2. Architecture Overview

Melvil is designed in layers, where each layer delivers value independently and enables the next.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              LAYER 4: CARTOGRAPHER                       │
│         Knowledge graphs, prerequisite paths, syntopical reading         │
│                         (Future: when scale demands)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                              LAYER 3: GUIDE                              │
│          Chapter-level analysis, reading plans, interest queue           │
│                           (Phase 2: with content)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                              LAYER 2: ADVISOR                            │
│             Learning goals, relevance scoring, recommendations           │
│                            (Phase 1b: with goals)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                              LAYER 1: LIBRARIAN                          │
│              Add books, generate summaries, search, organize             │
│                              (Phase 1a: MVP)                             │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key insight**: Each layer is useful on its own. You don't need prerequisite graphs to answer "what is this book about?" You don't need knowledge state tracking to find books on a topic.

---

## 3. Phase 1: The Librarian (MVP)

### 3.1 What It Does

The Librarian answers: **"What do I have, and what is it about?"**

| Feature | Description |
|---------|-------------|
| **Add materials** | Import books by ISBN, title, or file |
| **Zotero import** | Sync from your existing Zotero library |
| **Auto-summarize** | Generate multi-level summaries via LLM |
| **Extract concepts** | Identify key topics as tags |
| **Search & browse** | Find materials by title, concept, or full-text |
| **Organize** | Tag, categorize, and annotate your library |

### 3.2 Data Model (Simple)

```sql
-- Core tables only
CREATE TABLE materials (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'book', 'article', 'paper'
    title TEXT NOT NULL,
    authors TEXT,  -- JSON array
    isbn TEXT,
    publication_year INTEGER,
    page_count INTEGER,

    -- Summaries (the core value)
    summary_short TEXT,      -- 2-3 sentences
    summary_detailed TEXT,   -- 1-2 paragraphs
    main_thesis TEXT,        -- Author's central argument

    -- Concepts as simple tags
    concepts TEXT,  -- JSON array: ["distributed systems", "CAP theorem", ...]

    -- For semantic search
    embedding BLOB,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Full-text search
CREATE VIRTUAL TABLE materials_fts USING fts5(
    title,
    authors,
    summary_short,
    summary_detailed,
    concepts,
    content=materials,
    content_rowid=rowid
);

-- Table of contents (when available)
CREATE TABLE chapters (
    id TEXT PRIMARY KEY,
    material_id TEXT REFERENCES materials(id),
    chapter_number INTEGER,
    title TEXT,
    page_start INTEGER,
    page_end INTEGER,
    summary TEXT,
    concepts TEXT,  -- JSON array
    embedding BLOB
);

-- Simple organization
CREATE TABLE tags (
    material_id TEXT REFERENCES materials(id),
    tag TEXT,
    PRIMARY KEY (material_id, tag)
);

-- Reading status
CREATE TABLE reading_status (
    material_id TEXT PRIMARY KEY REFERENCES materials(id),
    status TEXT,  -- 'want_to_read', 'reading', 'finished', 'abandoned'
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    notes TEXT
);

-- Zotero sync tracking
CREATE TABLE zotero_sync (
    zotero_key TEXT PRIMARY KEY,      -- Zotero item key
    material_id TEXT REFERENCES materials(id),
    zotero_version INTEGER,           -- For incremental sync
    last_synced TIMESTAMP,
    attachment_path TEXT              -- Path to PDF if available
);
```

### 3.3 Zotero Integration

Zotero is the primary source of materials for many researchers. Melvil integrates with Zotero at multiple levels:

#### Integration Options

| Method | Use Case | Requires |
|--------|----------|----------|
| **Local database** | Offline, immediate access | Zotero installed locally |
| **Web API** | Synced libraries, shared groups | Zotero account + API key |
| **Better BibTeX** | Users who already export | Better BibTeX plugin |

#### Local Database Integration (Recommended)

Zotero stores its data in a SQLite database at:
- **macOS**: `~/Zotero/zotero.sqlite`
- **Linux**: `~/Zotero/zotero.sqlite`
- **Windows**: `C:\Users\<user>\Zotero\zotero.sqlite`

```python
class ZoteroLocalImporter:
    """Import from local Zotero database."""

    def __init__(self, zotero_path: str = None):
        self.zotero_path = zotero_path or self._find_zotero_db()
        self.storage_path = Path(self.zotero_path).parent / "storage"

    def _find_zotero_db(self) -> str:
        """Auto-detect Zotero database location."""
        candidates = [
            Path.home() / "Zotero" / "zotero.sqlite",
            Path.home() / ".zotero" / "zotero" / "zotero.sqlite",
        ]
        for path in candidates:
            if path.exists():
                return str(path)
        raise FileNotFoundError("Zotero database not found")

    def get_items(self, item_type: str = None, collection: str = None) -> list[dict]:
        """
        Fetch items from Zotero.

        Args:
            item_type: Filter by type ('book', 'journalArticle', 'conferencePaper', etc.)
            collection: Filter by collection name
        """
        conn = sqlite3.connect(f"file:{self.zotero_path}?mode=ro", uri=True)

        query = """
            SELECT
                items.key,
                itemTypes.typeName,
                (SELECT value FROM itemData
                 JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
                 JOIN fields ON itemData.fieldID = fields.fieldID
                 WHERE itemData.itemID = items.itemID AND fields.fieldName = 'title'
                ) as title,
                (SELECT value FROM itemData
                 JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
                 JOIN fields ON itemData.fieldID = fields.fieldID
                 WHERE itemData.itemID = items.itemID AND fields.fieldName = 'abstractNote'
                ) as abstract,
                (SELECT value FROM itemData
                 JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
                 JOIN fields ON itemData.fieldID = fields.fieldID
                 WHERE itemData.itemID = items.itemID AND fields.fieldName = 'ISBN'
                ) as isbn,
                (SELECT value FROM itemData
                 JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
                 JOIN fields ON itemData.fieldID = fields.fieldID
                 WHERE itemData.itemID = items.itemID AND fields.fieldName = 'DOI'
                ) as doi,
                (SELECT GROUP_CONCAT(creators.firstName || ' ' || creators.lastName, '; ')
                 FROM itemCreators
                 JOIN creators ON itemCreators.creatorID = creators.creatorID
                 WHERE itemCreators.itemID = items.itemID
                ) as authors,
                items.itemID
            FROM items
            JOIN itemTypes ON items.itemTypeID = itemTypes.itemTypeID
            WHERE itemTypes.typeName != 'attachment'
              AND itemTypes.typeName != 'note'
              AND items.itemID NOT IN (SELECT itemID FROM deletedItems)
        """

        results = conn.execute(query).fetchall()
        conn.close()

        return [self._row_to_dict(row) for row in results]

    def get_attachment_path(self, zotero_key: str) -> Optional[Path]:
        """Get path to PDF attachment for an item."""
        storage_dir = self.storage_path / zotero_key
        if storage_dir.exists():
            pdfs = list(storage_dir.glob("*.pdf"))
            if pdfs:
                return pdfs[0]
        return None

    def sync_to_melvil(self, melvil_db: Database, item_type: str = None) -> SyncResult:
        """
        Sync Zotero items to Melvil.

        Returns counts of added, updated, and skipped items.
        """
        items = self.get_items(item_type=item_type)
        added, updated, skipped = 0, 0, 0

        for item in items:
            existing = melvil_db.get_by_zotero_key(item['key'])

            if existing:
                # Already synced - check if needs update
                skipped += 1
                continue

            # Create new material from Zotero data
            material = Material(
                type=self._map_item_type(item['type']),
                title=item['title'],
                authors=item['authors'].split('; ') if item['authors'] else [],
                isbn=item.get('isbn'),
                doi=item.get('doi'),
                # Abstract becomes initial summary (will be enhanced by LLM)
                summary_short=item.get('abstract', '')[:500] if item.get('abstract') else None,
            )

            # Check for PDF attachment
            pdf_path = self.get_attachment_path(item['key'])
            if pdf_path:
                material.has_content = True
                material.content_path = str(pdf_path)

            melvil_db.save(material)
            melvil_db.save_zotero_sync(item['key'], material.id)
            added += 1

        return SyncResult(added=added, updated=updated, skipped=skipped)
```

#### Web API Integration

For synced libraries or shared group libraries:

```python
from pyzotero import zotero

class ZoteroWebImporter:
    """Import from Zotero Web API."""

    def __init__(self, library_id: str, api_key: str, library_type: str = 'user'):
        self.zot = zotero.Zotero(library_id, library_type, api_key)

    def get_items(self, item_type: str = None, limit: int = 100) -> list[dict]:
        """Fetch items from Zotero Web API."""
        params = {'limit': limit}
        if item_type:
            params['itemType'] = item_type

        items = self.zot.items(**params)
        return [self._parse_item(item) for item in items]

    def get_collections(self) -> list[dict]:
        """List all collections."""
        return self.zot.collections()

    def get_items_in_collection(self, collection_key: str) -> list[dict]:
        """Get all items in a specific collection."""
        items = self.zot.collection_items(collection_key)
        return [self._parse_item(item) for item in items]
```

#### CLI Commands for Zotero

```bash
# === Zotero Sync ===
melvil zotero sync                           # Sync all items from local Zotero
melvil zotero sync --type book               # Only books
melvil zotero sync --collection "Research"   # Only specific collection

# === Zotero Status ===
melvil zotero status                         # Show sync status
melvil zotero collections                    # List Zotero collections

# === Initial Setup ===
melvil zotero setup                          # Auto-detect Zotero location
melvil zotero setup --path ~/Zotero          # Manual path
melvil zotero setup --api-key <key>          # Configure Web API

# === Selective Import ===
melvil zotero import "Author Name"           # Import by author
melvil zotero import --tag "to-read"         # Import by Zotero tag
melvil zotero import --since 2024-01-01      # Import recent additions
```

#### Sync Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      ZOTERO SYNC WORKFLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Zotero Library                        Melvil                   │
│  ┌─────────────┐                      ┌─────────────┐           │
│  │ 500 items   │  ──── sync ────────► │ materials   │           │
│  │ with PDFs   │                      │ table       │           │
│  └─────────────┘                      └─────────────┘           │
│        │                                     │                   │
│        │                                     ▼                   │
│        │                              ┌─────────────┐           │
│        │                              │ LLM enrich  │           │
│        │                              │ (summaries, │           │
│        │                              │  concepts)  │           │
│        │                              └─────────────┘           │
│        │                                     │                   │
│        ▼                                     ▼                   │
│  ┌─────────────┐                      ┌─────────────┐           │
│  │ PDF files   │  ──── Phase 3 ─────► │ Chapter     │           │
│  │ (storage/)  │      analysis        │ analysis    │           │
│  └─────────────┘                      └─────────────┘           │
│                                                                  │
│  Benefits:                                                       │
│  • Zotero remains source of truth for bibliography              │
│  • Melvil adds summaries, concepts, recommendations             │
│  • PDFs available for deep chapter analysis                      │
│  • Tags/collections sync both ways (future)                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Ingestion Pipeline (Simple)

```python
class MaterialIngestion:
    """
    Simple ingestion: fetch metadata, generate summary, store.
    """

    async def ingest(self, identifier: str) -> Material:
        # Step 1: Fetch metadata from Open Library
        metadata = await self.fetch_metadata(identifier)

        # Step 2: Generate summary with Claude
        # Use long context - no need for map-reduce on most books
        summary = await self.generate_summary(
            title=metadata['title'],
            description=metadata.get('description', ''),
            toc=metadata.get('table_of_contents', [])
        )

        # Step 3: Extract concepts (simple tag extraction)
        concepts = await self.extract_concepts(summary)

        # Step 4: Generate embedding for semantic search
        embedding = await self.embed(f"{metadata['title']}. {summary['short']}")

        # Step 5: Store
        material = Material(
            title=metadata['title'],
            authors=metadata.get('authors', []),
            isbn=metadata.get('isbn'),
            summary_short=summary['short'],
            summary_detailed=summary['detailed'],
            main_thesis=summary['thesis'],
            concepts=concepts,
            embedding=embedding
        )

        await self.db.save(material)
        return material

    async def generate_summary(self, title: str, description: str, toc: list) -> dict:
        """Single Claude call for all summary levels."""

        prompt = f"""Analyze this book and provide:

1. SHORT_SUMMARY: 2-3 sentences. What is this book about? Who is it for?
2. DETAILED_SUMMARY: 1-2 paragraphs covering main topics and key insights.
3. MAIN_THESIS: 1-2 sentences. What is the author's central argument?
4. KEY_CONCEPTS: 5-10 main concepts/topics (comma-separated).

Title: {title}
Description: {description}
Table of Contents: {self._format_toc(toc)}

Respond in this exact format:
SHORT_SUMMARY: [summary]
DETAILED_SUMMARY: [summary]
MAIN_THESIS: [thesis]
KEY_CONCEPTS: [concept1, concept2, ...]"""

        response = await self.claude.message(prompt)
        return self._parse_response(response)
```

### 3.4 CLI Interface

```bash
# === Adding Materials ===
melvil add "978-1449373320"                    # By ISBN
melvil add "Designing Data-Intensive Apps"     # By title search
melvil add ./book.pdf                          # From file (future)

# === Zotero Integration ===
melvil zotero sync                             # Sync from local Zotero
melvil zotero sync --collection "Research"     # Sync specific collection
melvil zotero sync --type book                 # Only books
melvil zotero status                           # Show sync status
melvil zotero enrich                           # Generate summaries for synced items

# === Viewing Materials ===
melvil show "DDIA"                             # Show summary, concepts, TOC
melvil list                                    # List all materials
melvil list --tag "distributed-systems"        # Filter by tag

# === Searching ===
melvil search "consensus algorithms"           # Full-text + semantic search
melvil concepts                                # List all concepts
melvil concepts "CAP theorem"                  # Find materials covering concept

# === Organizing ===
melvil tag "DDIA" distributed-systems backend  # Add tags
melvil status "DDIA" reading                   # Update reading status
melvil note "DDIA" "Chapter 5 is gold"         # Add notes

# === Quick Info ===
melvil summary "DDIA"                          # Just the short summary
melvil toc "DDIA"                              # Table of contents
melvil thesis "DDIA"                           # Author's main argument
```

### 3.5 Technology Stack (Minimal)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Database | SQLite | Zero config, portable, surprisingly capable |
| Full-text search | SQLite FTS5 | Built-in, good enough for thousands of books |
| Vector search | sqlite-vec or in-memory | Simple, no infrastructure |
| LLM | Claude API | Long context, excellent summarization |
| Embeddings | OpenAI ada-002 or local | Simple API, good quality |
| Zotero | pyzotero + direct SQLite | Web API and local database access |
| Interface | CLI (Click + Rich) | Fast iteration, forces good UX |

### 3.6 Success Criteria for Phase 1

- [ ] Can sync entire Zotero library in <2 minutes
- [ ] Can add a book by ISBN and get summary in <30 seconds
- [ ] Can search across 100+ books instantly
- [ ] Can answer "what is this book about?" with useful summary
- [ ] Can find "all books about X" with reasonable accuracy
- [ ] Daily CLI usage feels natural

---

## 4. Phase 2: The Advisor

### 4.1 What It Adds

The Advisor answers: **"What should I read for my goal?"**

| Feature | Description |
|---------|-------------|
| **Learning goals** | Define what you want to learn and how deeply |
| **Relevance scoring** | Score materials against your goals |
| **Recommendations** | Suggest what to read next |
| **Knowledge tracking** | Simple self-reported concept familiarity |

### 4.2 Additional Data Model

```sql
-- Learning goals
CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    depth TEXT,  -- 'survey', 'working', 'expert'
    status TEXT DEFAULT 'active',  -- 'active', 'paused', 'completed'
    target_concepts TEXT,  -- JSON array (can be empty initially)
    embedding BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User's self-reported concept familiarity
CREATE TABLE knowledge (
    concept TEXT PRIMARY KEY,
    level TEXT,  -- 'unknown', 'heard_of', 'understand', 'can_explain', 'mastered'
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interest queue: books to evaluate later
CREATE TABLE interest_queue (
    id TEXT PRIMARY KEY,
    identifier TEXT,  -- ISBN, title, or URL
    context TEXT,     -- "Mentioned in podcast X", "Friend recommended"
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);
```

### 4.3 Relevance Scoring (Simple)

```python
class RelevanceScorer:
    """
    Simple relevance: semantic similarity + concept overlap.
    No elaborate formulas—let users judge with good information.
    """

    async def score(self, material: Material, goal: Goal) -> RelevanceResult:
        # Primary signal: semantic similarity
        similarity = cosine_similarity(material.embedding, goal.embedding)

        # Secondary signal: concept overlap
        goal_concepts = set(goal.target_concepts) if goal.target_concepts else set()
        material_concepts = set(material.concepts)

        if goal_concepts:
            overlap = len(goal_concepts & material_concepts) / len(goal_concepts)
        else:
            overlap = None  # Goal doesn't have explicit concepts

        return RelevanceResult(
            score=similarity,
            concept_overlap=overlap,
            matching_concepts=list(goal_concepts & material_concepts),
            material_summary=material.summary_short,
            # Let the user decide with this information
        )

    async def recommend(self, goal: Goal, limit: int = 10) -> list[RelevanceResult]:
        """Find most relevant materials for a goal."""

        materials = await self.db.get_all_materials()
        scored = [await self.score(m, goal) for m in materials]
        scored.sort(key=lambda r: r.score, reverse=True)

        return scored[:limit]
```

### 4.4 CLI Additions

```bash
# === Goals ===
melvil goal add "Learn distributed systems" --depth working
melvil goal list
melvil goal "dist-sys"                         # Show goal details

# === Relevance ===
melvil relevant? "DDIA" --goal "dist-sys"      # Score one material
melvil recommend --goal "dist-sys"             # Top recommendations
melvil recommend --goal "dist-sys" --hours 10  # Filter by reading time

# === Knowledge ===
melvil know "CAP theorem"                      # I understand this
melvil know "Paxos" --level "heard_of"         # Basic awareness
melvil knowledge                               # Show what I've marked

# === Interest Queue ===
melvil later "Some Book Title" --context "Podcast recommendation"
melvil queue                                   # Show interest queue
melvil process-queue                           # Ingest and evaluate queued items
```

### 4.5 Success Criteria for Phase 2

- [ ] Can define a goal and get relevant recommendations
- [ ] Semantic search meaningfully ranks by relevance
- [ ] Interest queue captures and surfaces discoveries
- [ ] Knowledge tracking feels lightweight, not burdensome

---

## 5. Phase 3: The Guide

### 5.1 What It Adds

The Guide answers: **"Which parts of this book should I read?"**

| Feature | Description |
|---------|-------------|
| **Chapter-level analysis** | Summaries and concepts per chapter |
| **Targeted recommendations** | "Read chapters 5-9" not "read this book" |
| **Reading plans** | Multi-book sequences for a goal |
| **Progress tracking** | What you've read, what's next |

### 5.2 Requirements

This phase requires **access to book content** (PDF, EPUB, or full text) for meaningful chapter analysis. Without content, chapter recommendations are limited to TOC-based heuristics.

### 5.3 Chapter Analysis

```python
class ChapterAnalyzer:
    """Analyze chapters when full content is available."""

    async def analyze_book(self, material_id: str, content: str) -> list[Chapter]:
        # Split content by chapters (detect chapter boundaries)
        chapter_texts = self.split_into_chapters(content)

        chapters = []
        for i, (title, text) in enumerate(chapter_texts):
            summary = await self.summarize_chapter(title, text)
            concepts = await self.extract_concepts(text)
            embedding = await self.embed(f"{title}. {summary}")

            chapters.append(Chapter(
                material_id=material_id,
                chapter_number=i + 1,
                title=title,
                summary=summary,
                concepts=concepts,
                embedding=embedding
            ))

        return chapters

    async def recommend_chapters(
        self,
        material: Material,
        goal: Goal
    ) -> list[tuple[Chapter, float]]:
        """Find most relevant chapters for a goal."""

        chapters = await self.db.get_chapters(material.id)
        scored = []

        for chapter in chapters:
            similarity = cosine_similarity(chapter.embedding, goal.embedding)
            scored.append((chapter, similarity))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Return chapters above threshold
        return [(ch, score) for ch, score in scored if score > 0.5]
```

### 5.4 CLI Additions

```bash
# === Chapter Analysis ===
melvil analyze "DDIA" --file ./ddia.pdf        # Full chapter analysis
melvil chapters "DDIA"                         # List chapters with summaries

# === Targeted Reading ===
melvil what-to-read "DDIA" --goal "dist-sys"   # Recommended chapters
# Output: "Focus on chapters 5-9 (Replication, Partitioning, Transactions)
#          Skip chapters 1-2 if you know databases basics"

# === Reading Plans ===
melvil plan --goal "dist-sys"                  # Multi-book reading plan
melvil next                                    # What should I read next?

# === Progress ===
melvil read "DDIA" --chapters 5-7              # Mark chapters as read
melvil progress                                # Show reading progress
```

### 5.5 Success Criteria for Phase 3

- [ ] Can get chapter-level recommendations for analyzed books
- [ ] "Read chapters 5-9" recommendations are accurate
- [ ] Reading plans span multiple books coherently
- [ ] Progress tracking motivates continued reading

---

## 6. Phase 4: The Cartographer (Future Vision)

### 6.1 What It Adds

The Cartographer answers: **"How does everything connect?"**

| Feature | Description |
|---------|-------------|
| **Knowledge graph** | Concepts, prerequisites, and relationships |
| **Prerequisite paths** | "Learn X before Y" |
| **Gap analysis** | What you're missing for a goal |
| **Syntopical reading** | Cross-book concept synthesis |

### 6.2 When to Build This

Build the Cartographer **only when**:

- You have 200+ materials and need graph-level queries
- Users explicitly request prerequisite guidance
- The simpler phases prove insufficient
- You have evidence prerequisite mapping adds value

### 6.3 Graph Model (Eventual)

```cypher
// Concepts with relationships
(:Concept {name, description, domain, abstraction_level})
(:Concept)-[:PREREQUISITE_OF {strength}]->(:Concept)
(:Concept)-[:RELATED_TO {type, strength}]->(:Concept)
(:Concept)-[:PART_OF]->(:Concept)  // Hierarchical

// Materials covering concepts
(:Material)-[:COVERS {depth, quality}]->(:Concept)
(:Material)-[:REQUIRES_KNOWLEDGE_OF]->(:Concept)

// User knowledge state
(:User)-[:FAMILIAR_WITH {level, confidence, source}]->(:Concept)
(:User)-[:HAS_GOAL]->(:LearningGoal)
(:LearningGoal)-[:TARGETS]->(:Concept)
```

### 6.4 Prerequisite Inference

```python
class PrerequisiteMapper:
    """Build prerequisite relationships from content analysis."""

    async def infer_prerequisites(self, concept: str) -> list[str]:
        """Use LLM to infer what you need to know before learning a concept."""

        prompt = f"""What concepts should someone understand BEFORE learning about "{concept}"?

List only direct prerequisites (not prerequisites of prerequisites).
Return as a comma-separated list, or "none" if no prerequisites.

Prerequisites:"""

        response = await self.claude.message(prompt)

        if response.strip().lower() == "none":
            return []

        return [p.strip() for p in response.split(",")]

    async def build_learning_path(
        self,
        target_concepts: list[str],
        known_concepts: list[str]
    ) -> list[str]:
        """Generate ordered list of concepts to learn."""

        # Get all prerequisites recursively
        to_learn = set(target_concepts) - set(known_concepts)
        all_prereqs = set()

        for concept in to_learn:
            prereqs = await self.get_all_prerequisites(concept)
            all_prereqs.update(prereqs)

        # Remove already known
        to_learn = (to_learn | all_prereqs) - set(known_concepts)

        # Topological sort based on prerequisites
        return self.topological_sort(to_learn)
```

### 6.5 Technology Upgrade Path

| Phase 1-3 | Phase 4 |
|-----------|---------|
| SQLite | Neo4j (when graph queries needed) |
| sqlite-vec | Pinecone/Wikidata (when scale demands) |
| In-memory graphs | Persistent graph database |
| Simple CLI | API + optional web UI |

---

## 7. Design Principles

### 7.1 Simplicity First

- Each feature should be useful on its own
- Don't build infrastructure for hypothetical needs
- SQLite until you prove you need more
- CLI until you prove you need UI

### 7.2 User Agency

- Show information, let users decide
- Self-reported knowledge over inference
- Recommendations are suggestions, not prescriptions
- Always explain why something is recommended

### 7.3 Incremental Value

- Phase 1 is useful without Phase 2
- Phase 2 is useful without Phase 3
- Each phase delivers value, not just enables future phases

### 7.4 Content is Optional

- System works with metadata only (titles, descriptions, TOC)
- Full content enables deeper analysis but isn't required
- Graceful degradation when content unavailable

---

## 8. Adler's Framework in the System

| Reading Level | System Support | Phase |
|---------------|----------------|-------|
| **Elementary** | Not addressed (assumed) | - |
| **Inspectional** | Summaries, TOC, concept tags | 1 |
| **Analytical** | Chapter analysis, reading guides | 3 |
| **Syntopical** | Cross-book graphs, concept synthesis | 4 |

The system progresses through Adler's levels as it matures—starting with inspectional reading support (what every user needs) and building toward syntopical reading support (for power users with large libraries).

---

## 9. Success Metrics

### Immediate (Phase 1)
- Time to understand what a book is about: <30 seconds
- Accuracy of concept extraction: >80% relevant
- Daily active use by creator

### Medium-term (Phase 2-3)
- Quality of recommendations: users read what's suggested
- Chapter recommendations save time vs. full book reads
- Interest queue captures >90% of discoveries

### Long-term (Phase 4)
- Users report feeling "in control" of reading choices
- Prerequisite paths prevent frustration
- Syntopical queries produce novel insights

---

## 10. What This System Does NOT Do

1. **Read books for you** — It directs attention, not replaces learning
2. **Require perfect data** — Works with incomplete metadata
3. **Force a reading order** — Recommendations, not prescriptions
4. **Need all infrastructure upfront** — Layers add incrementally
5. **Replace your judgment** — Shows information, you decide

---

## 11. Getting Started

### Minimal Setup

```bash
# 1. Clone and install
git clone <repo>
cd melvil
pip install -e .

# 2. Configure API keys
export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key  # For embeddings

# 3. Initialize database
melvil init

# 4. Connect to Zotero (if you use it)
melvil zotero setup                    # Auto-detects local Zotero
melvil zotero sync                     # Import your library

# 5. Or add books manually
melvil add "978-1449373320"

# 6. Generate summaries for imported items
melvil enrich --pending                # Process items without summaries

# 7. See what you have
melvil list
melvil show "Designing Data-Intensive Applications"
```

### Quick Start with Zotero

If you already have a Zotero library, this is the fastest path:

```bash
melvil init
melvil zotero sync                     # Imports all items
melvil enrich --limit 10               # Summarize first 10 items
melvil search "your topic"             # Start exploring
```

### First Week Goals

1. Sync your Zotero library (or add 10-20 books manually)
2. Run `melvil enrich` on items you're curious about
3. Define 2-3 learning goals
4. Use `melvil recommend` daily
5. Note what's missing or frustrating

---

## Appendix A: LLM Prompts

### Book Summary Prompt

```text
Analyze this book and provide:

1. SHORT_SUMMARY: 2-3 sentences. What is this book about? Who is it for?
2. DETAILED_SUMMARY: 1-2 paragraphs covering main topics and key insights.
3. MAIN_THESIS: 1-2 sentences. What is the author's central argument?
4. KEY_CONCEPTS: 5-10 main concepts/topics (comma-separated).

Title: {title}
Description: {description}
Table of Contents: {toc}

Respond in this exact format:
SHORT_SUMMARY: [summary]
DETAILED_SUMMARY: [summary]
MAIN_THESIS: [thesis]
KEY_CONCEPTS: [concept1, concept2, ...]
```

### Chapter Summary Prompt

```text
Summarize this chapter in 2-3 sentences:
- What is the main point?
- What will readers learn?

Chapter title: {title}
Chapter content: {content}

Summary:
```

### Prerequisite Inference Prompt

```text
What concepts should someone understand BEFORE learning about "{concept}"?

List only direct prerequisites (not prerequisites of prerequisites).
Be specific and practical.
Return as a comma-separated list, or "none" if truly foundational.

Prerequisites:
```

---

## Appendix B: Supported Inputs

### Phase 1: Metadata-Based
| Input | Method |
|-------|--------|
| **Zotero library** | Local database sync (recommended) |
| **Zotero Web API** | For synced/shared libraries |
| **ISBN** | Fetches from Open Library |
| **Book title** | Searches Open Library |
| **DOI** | Fetches from CrossRef/Semantic Scholar |
| **Goodreads URL** | Extracts ISBN |

### Phase 3+: Content-Based
| Input | Method |
|-------|--------|
| **PDF files** | Direct upload or via Zotero attachments |
| **EPUB files** | Direct upload |
| **Plain text** | Direct upload |
| **Web articles** | URL fetch and extract |

### Zotero Item Type Mapping

| Zotero Type | Melvil Type |
|-------------|-------------|
| `book` | `book` |
| `bookSection` | `book` (chapter reference) |
| `journalArticle` | `article` |
| `conferencePaper` | `paper` |
| `report` | `paper` |
| `thesis` | `paper` |
| `webpage` | `article` |
| `preprint` | `paper` |

---

## Appendix C: Python Dependencies

```toml
[project]
name = "melvil"
version = "0.1.0"
requires-python = ">=3.10"

dependencies = [
    # Core
    "click>=8.0.0",
    "rich>=13.0.0",

    # Database
    "sqlite-vec>=0.1.0",       # Vector search in SQLite

    # AI/ML
    "anthropic>=0.25.0",       # Claude API
    "openai>=1.0.0",           # Embeddings

    # Zotero Integration
    "pyzotero>=1.5.0",         # Zotero Web API

    # HTTP
    "httpx>=0.24.0",           # Async HTTP client

    # Utilities
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
```

---

## Appendix D: Migration Path

### SQLite → Neo4j (if needed)

When graph queries become essential:

1. Export SQLite data to JSON
2. Import nodes (Materials, Concepts) to Neo4j
3. Create relationships from concept co-occurrence
4. Add prerequisite edges (LLM-inferred or manual)
5. Keep SQLite for simple queries, Neo4j for graph queries

### CLI → API (if needed)

When other interfaces are needed:

1. Extract core logic into service classes
2. Add FastAPI routes wrapping services
3. Keep CLI as primary development interface
4. Add web UI only if users request

### Zotero → Melvil (one-way sync)

The current design treats Zotero as the source of truth for bibliography:

1. Zotero manages citations, PDFs, and basic metadata
2. Melvil enriches with summaries, concepts, and recommendations
3. Sync is pull-only (Zotero → Melvil)

Future consideration: push Melvil tags back to Zotero for interop.

---

*This document defines both where we start (simple) and where we're going (ambitious). Build Phase 1 first. Prove value. Then expand.*
