# Melvil

**Your reading, directed.**

---

## The Problem

You have 847 papers in Zotero. Thirty-two books on your shelf you've been meaning to read. A growing list of "interesting" links saved from Twitter, podcasts, and conversations. When someone asks what you're reading, you feel a familiar guilt.

The problem isn't motivation. It's *triage*.

Every book is potentially relevant. Every paper might be the one that unlocks understanding. But you can't read everything, and you don't know what to skip. So you either read randomly (inefficient) or don't read at all (worse).

**Melvil fixes this.**

---

## The Core Insight

In 1940, Mortimer Adler observed that most books don't deserve cover-to-cover reading. He proposed *inspectional reading*: spending 15 minutes with a book to understand its structure, thesis, and whether it warrants deeper engagement.

This was brilliant advice for the library-goer. But we don't visit libraries anymore. We have Zotero databases, PDF folders, and endless recommendations. The problem isn't finding books—it's evaluating the hundreds we've already collected.

**Melvil automates inspectional reading at scale.**

For every book in your library, Melvil can tell you:
- What it's about (in 3 sentences)
- What the author is trying to convince you of
- What concepts it covers and how deeply
- Which chapters matter for your specific goal

This transforms a guilt-inducing backlog into a navigable resource.

---

## A Day With Melvil

**Morning.** You're preparing for a project on distributed systems. You ask:

```
$ melvil recommend --goal "distributed systems"

Based on your goal "Learn distributed systems (working level)":

1. Designing Data-Intensive Applications    [94% relevant]
   "The definitive guide to data systems. Covers replication,
   partitioning, and distributed transactions."
   → Focus on chapters 5-9 (skip 1-2 if you know databases)

2. Database Internals                        [76% relevant]
   "Deep dive into storage engines and distributed architecture."
   → Read Part II only for your goal

3. The Art of Scalability                    [71% relevant]
   "Organizational and technical scaling patterns."
   → Chapters 10-15 most relevant
```

You didn't have to evaluate these books. Melvil already knows what's in your library.

**Afternoon.** A colleague mentions a paper during a meeting. You capture it instantly:

```
$ melvil later "Raft consensus paper" --context "Alex mentioned, seems important"

Added to interest queue. Will evaluate against your goals.
```

Later, Melvil will tell you whether this paper matters for what you're learning.

**Evening.** You're curious what you know about consensus:

```
$ melvil search "consensus"

Found 12 materials covering "consensus":

Books:
  • Designing Data-Intensive Applications (ch. 9) - deep_dive
  • Database Internals (ch. 14) - explains

Papers:
  • Raft: In Search of an Understandable Consensus Algorithm - deep_dive
  • Paxos Made Simple - explains

You marked "Raft" as understood. 3 materials may be redundant.
```

Your library becomes a map you can navigate.

---

## What Makes Melvil Different

| Tool | What it does | What's missing |
|------|--------------|----------------|
| **Zotero** | Stores citations and PDFs | No understanding of content |
| **Goodreads** | Tracks books read | No learning goals, no relevance |
| **Readwise** | Surfaces highlights | Assumes you've already read |
| **ChatGPT** | Answers questions | No memory of your library or goals |

**Melvil knows both your library and your goals.** It's the layer between your reference manager (what you have) and your brain (what you want to learn).

---

## Design Orientation: Semantic Archive

Melvil is not just a recommender. It is a **semantic archive**: a system that preserves sources, captures meaning in multiple forms, and helps users recompute relevance as their questions change.

Guiding principles:
1. **Capture first, structure progressively.** Preserve raw sources; let structure evolve.
2. **Pluralism of representations.** Text, metadata, embeddings, graphs, and notes coexist.
3. **Provenance and inspectability.** Every derived artifact links back to sources and timestamps.
4. **Retrieval as a process.** Support iterative sensemaking, not one-shot answers.
5. **Uncertainty and disagreement.** Competing interpretations are preserved, not flattened.

---

## The System in One Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│    YOUR SOURCES                 MELVIL                   YOUR GOALS    │
│                                                                         │
│    ┌──────────┐              ┌──────────┐              ┌──────────┐    │
│    │  Zotero  │─────────────▶│          │              │ "Learn   │    │
│    │  847 refs│    sync      │ Enriched │◀─────────────│  dist.   │    │
│    └──────────┘              │ Library  │   relevance  │ systems" │    │
│                              │          │              └──────────┘    │
│    ┌──────────┐              │ • summaries             ┌──────────┐    │
│    │  Manual  │─────────────▶│ • concepts │◀───────────│ "Prep    │    │
│    │  ISBN/DOI│    add       │ • chapters │  relevance │  for ML  │    │
│    └──────────┘              │ • thesis   │            │  role"   │    │
│                              └──────────┘              └──────────┘    │
│                                   │                                     │
│                                   ▼                                     │
│                          ┌───────────────┐                             │
│                          │ "Read ch 5-9  │                             │
│                          │  of DDIA for  │                             │
│                          │  your goal"   │                             │
│                          └───────────────┘                             │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## The Four Capabilities

Melvil grows in capability across four layers. Each layer works independently.

### Layer 1: The Librarian
*"What do I have, and what is it about?"*

```
$ melvil zotero sync
Synced 847 items from Zotero.

$ melvil enrich --limit 20
Generating summaries... ████████████████████ 20/20

$ melvil show "DDIA"

Designing Data-Intensive Applications
Martin Kleppmann, 2017

SUMMARY: A comprehensive guide to building reliable, scalable, and
maintainable data systems. Covers the fundamental ideas behind databases,
distributed systems, and data processing pipelines.

THESIS: The core challenge of modern applications is managing data at
scale, and understanding the trade-offs between consistency, availability,
and partition tolerance is essential for making good design decisions.

CONCEPTS: distributed systems, replication, partitioning, transactions,
consistency models, stream processing, batch processing

CHAPTERS:
  1. Reliable, Scalable, and Maintainable Applications
  2. Data Models and Query Languages
  ...
```

**You now have an intelligent index of everything you own.**

### Layer 2: The Advisor
*"What should I read for my goal?"*

```
$ melvil goal add "distributed systems" --depth working
Goal created: distributed systems (working level)

$ melvil recommend
Top 5 materials for "distributed systems":
  1. Designing Data-Intensive Applications [94%]
  2. Database Internals [76%]
  ...

$ melvil relevant? "Clean Code"
Relevance to "distributed systems": 12%
This book is about code quality, not distributed systems.
→ Skip for this goal.
```

**You stop guessing what's worth reading.**

### Layer 3: The Guide
*"Which parts of this book matter?"*

```
$ melvil analyze "DDIA"
Analyzing PDF... extracting chapters... generating summaries...
Done. 12 chapters analyzed.

$ melvil what-to-read "DDIA" --goal "distributed systems"

For your goal "distributed systems (working level)":

READ CAREFULLY:
  Ch 5. Replication (pp. 151-196)      ████████████ essential
  Ch 6. Partitioning (pp. 197-226)     ████████████ essential
  Ch 7. Transactions (pp. 227-276)     ██████████░░ important
  Ch 8. Distributed Problems (pp. 277-322) ████████████ essential
  Ch 9. Consistency & Consensus (pp. 323-378) ████████████ essential

SKIM OR SKIP:
  Ch 1-2. Foundations                   You likely know this already
  Ch 3-4. Storage & Encoding            Reference as needed
  Ch 10-12. Batch & Stream              Beyond "working level"

Estimated focused reading: 8 hours (vs 20+ for full book)
```

**You read 40% of the book and get 90% of what you need.**

### Layer 4: The Cartographer
*"How does everything connect?"*

```
$ melvil path --to "consensus algorithms"

Learning path to "consensus algorithms":

1. ○ Distributed systems basics
     └─ DDIA ch. 5-8 [not started]

2. ○ Failure models
     └─ DDIA ch. 8 [not started]

3. ○ Consensus algorithms
     └─ Raft paper [not started]
     └─ DDIA ch. 9 [not started]

You're missing prerequisites. Start with (1).
```

**You see the terrain before you walk it.**

---

## The CLI

Melvil is a command-line tool. This is deliberate.

A CLI forces good design. Every command must be discoverable, memorable, and fast. If typing `melvil recommend` isn't faster than opening a web app, the design is wrong.

### Command Taxonomy

```bash
# === Library ===
melvil add <isbn|doi|title>        # Add a single item
melvil zotero sync                 # Sync from Zotero
melvil enrich [--limit N]          # Generate summaries
melvil list [--type book|paper]    # List library
melvil show <title>                # Show details
melvil search <query>              # Search everything

# === Goals ===
melvil goal add <description>      # Create goal
melvil goal list                   # Show goals
melvil recommend [--goal X]        # Get recommendations
melvil relevant? <title>           # Check relevance

# === Reading ===
melvil what-to-read <title>        # Chapter recommendations
melvil read <title> [--ch N-M]     # Mark as read
melvil progress                    # Show reading progress

# === Discovery ===
melvil later <title> [--context]   # Add to interest queue
melvil queue                       # Show queue
melvil know <concept>              # Mark concept as known

# === Exploration ===
melvil concepts [<query>]          # Browse concepts
melvil path --to <concept>         # Show learning path
```

Melvil supports multiple modes: **asking**, **browsing**, **inspecting**, **assembling**, and **contributing**. The CLI should make it easy to move between them without losing provenance or context.

### Design Principles

1. **Nouns are titles, not IDs.** `melvil show "DDIA"` not `melvil show abc123`
2. **Defaults are sensible.** `melvil recommend` uses your active goal
3. **Output is scannable.** Relevance percentages, chapter ranges, clear verdicts
4. **Speed matters.** Common queries return in <500ms

---

## Data Architecture

### Layered Semantic Stack

- **Layer 0: Immutable sources** (PDFs, notes, metadata snapshots)
- **Layer 1: Metadata and facets** (authors, dates, domains, projects)
- **Layer 2: IR index** (FTS for precise, auditable retrieval)
- **Layer 3: Embeddings** (semantic recall and discovery)
- **Layer 4: Structured meaning** (claims, arguments, term definitions)

Meaning emerges from **interaction between layers**, not any single representation.

### The Simple Version (Phase 1-3)

```
~/.melvil/
├── melvil.db              # SQLite: everything lives here
├── config.yaml            # API keys, preferences
└── cache/                 # Embeddings, API responses
```

One database. One file to back up. Zero infrastructure.

### What's In The Database

```sql
-- The core: what you have
materials (id, type, title, authors, isbn, doi,
           summary_short, summary_detailed, thesis,
           concepts[], embedding, zotero_key)

-- Structure: what's in each book
chapters (id, material_id, number, title, pages,
          summary, concepts[], embedding)

-- Goals: what you're learning
goals (id, title, depth, status, concepts[], embedding)

-- State: what you know
knowledge (concept, level, updated_at)

-- Queue: what you've saved for later
interest_queue (id, identifier, context, added_at)
```

### Zotero Integration

Zotero is the source of truth for bibliography. Melvil enriches, doesn't replace.

```
Zotero                          Melvil
┌─────────────────┐            ┌─────────────────┐
│ • 847 items     │   sync     │ • Same 847 items│
│ • PDFs attached │ ─────────▶ │ • + summaries   │
│ • Basic metadata│            │ • + concepts    │
│ • Collections   │            │ • + relevance   │
└─────────────────┘            └─────────────────┘
```

Sync is:
- **One-way**: Zotero → Melvil (for now)
- **Non-destructive**: Melvil never modifies Zotero
- **Incremental**: Only new/changed items

```bash
$ melvil zotero sync
Found 847 items in Zotero.
  → 12 new since last sync
  → 3 updated
Syncing... done.

$ melvil zotero sync --collection "ML Papers"
Syncing collection "ML Papers" (143 items)...
```

---

## How Enrichment Works

When you add a book, Melvil:

1. **Fetches metadata** from Open Library, CrossRef, or Zotero
2. **Generates summaries** via Claude (3-sentence, detailed, thesis)
3. **Extracts concepts** as tags
4. **Creates embeddings** for semantic search
5. **Stores everything** in SQLite with provenance, timestamps, and model version

```python
# What happens inside
async def enrich(material):
    response = await claude.message(f"""
    Analyze this book:
    Title: {material.title}
    Description: {material.description}
    TOC: {material.toc}

    Provide:
    1. SHORT_SUMMARY (2-3 sentences)
    2. DETAILED_SUMMARY (1-2 paragraphs)
    3. MAIN_THESIS (1-2 sentences)
    4. KEY_CONCEPTS (5-10 topics)
    """)

    material.summary_short = parse(response, 'SHORT_SUMMARY')
    material.concepts = parse(response, 'KEY_CONCEPTS')
    material.embedding = embed(material.summary_short)
    material.provenance = {
        "summary_short": "llm:claude",
        "concepts": "llm:claude",
        "embedding": "openai:text-embedding-3-small",
    }

    save(material)
```

**Cost**: ~$0.01-0.03 per book (metadata-only enrichment).

**Rule**: Summaries orient; sources decide. All outputs are inspectable and reversible.

---

## The Goal System

A goal is a statement of what you want to learn and how deeply.

```bash
$ melvil goal add "distributed systems" --depth working

# Depth levels:
#   survey   = "I want an overview"
#   working  = "I want to build things with this"
#   expert   = "I want to understand the edge cases"
```

Goals enable:
- **Relevance scoring**: Is this book useful for this goal?
- **Chapter filtering**: Which chapters matter for this goal?
- **Recommendations**: What should I read next?

You can have multiple goals. Recommendations consider all active goals.

```bash
$ melvil goal list
Active goals:
  1. distributed systems (working) - 3 books read
  2. ML fundamentals (survey) - 0 books read

$ melvil recommend
Showing recommendations across all active goals...
```

---

## Technology Choices

| Component | Choice | Why |
|-----------|--------|-----|
| Database | SQLite | Zero config, single file, surprisingly capable |
| Vector search | sqlite-vec | Keeps everything in one database |
| LLM | Claude | Long context, excellent summarization |
| Embeddings | OpenAI text-embedding-3-small | Simple API, good quality |
| Zotero | Direct SQLite + pyzotero | Local DB is faster, API for sync |
| CLI | Click + Rich | Standard Python, beautiful output |

**Total infrastructure: one SQLite file.**

### Future Upgrades (Only If Needed)

| When | Do |
|------|-----|
| Library > 2000 items | Consider dedicated vector DB |
| Need graph queries | Add Neo4j alongside SQLite |
| Multiple users | Add FastAPI server |
| Web interface | Add simple frontend |

Don't build these until you need them.

---

## What Melvil Doesn't Do

1. **Read books for you.** It tells you what to read, not what books say.

2. **Require full text.** Works with metadata alone. Full PDFs enable chapter analysis but aren't required.

3. **Replace Zotero.** Zotero manages your bibliography. Melvil makes it navigable.

4. **Prescribe reading order.** It suggests; you decide.

5. **Track detailed notes.** That's what Zotero, Obsidian, and similar tools are for.

6. **Hide why results appear.** Relevance and summaries always link back to sources and provenance.

---

## Success Looks Like

After one month:
- Your Zotero library is synced and enriched
- You can answer "is X relevant?" in seconds
- You've defined 2-3 learning goals
- You know which chapters to read

After three months:
- The guilt of the unread backlog is gone
- When someone mentions a paper, you add it to the queue without anxiety
- You read less but learn more

After a year:
- Your library is a map of your knowledge
- Learning paths through your materials are visible
- Syntopical reading across books is natural

---

## Getting Started

```bash
# Install
pip install melvil

# Configure
export ANTHROPIC_API_KEY=your_key
export OPENAI_API_KEY=your_key

# Initialize
melvil init

# Connect Zotero (if you have one)
melvil zotero sync

# Or add books manually
melvil add "978-1449373320"

# Enrich with summaries
melvil enrich

# Explore what you have
melvil list
melvil show "Designing Data-Intensive Applications"
melvil search "distributed"
```

---

## Implementation Phases

### Phase 1: The Librarian (Week 1-2)
- [ ] SQLite schema and core data models
- [ ] Zotero local database sync
- [ ] Source snapshots + provenance tracking
- [ ] Open Library metadata fetching
- [ ] Claude summarization (basic)
- [ ] CLI: add, sync, list, show, search

### Phase 2: The Advisor (Week 3-4)
- [ ] Goal creation and storage
- [ ] Embedding generation
- [ ] Relevance scoring
- [ ] CLI: goal, recommend, relevant?

### Phase 3: The Guide (Week 5-8)
- [ ] PDF parsing and chapter extraction
- [ ] Chapter-level summaries
- [ ] Chapter recommendations per goal
- [ ] CLI: analyze, what-to-read, read, progress

### Phase 4: The Cartographer (Future)
- [ ] Prerequisite inference
- [ ] Learning path generation
- [ ] Knowledge gap analysis
- [ ] (Maybe) Neo4j for graph queries

---

## Appendix A: Database Schema

```sql
CREATE TABLE materials (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- book, article, paper
    title TEXT NOT NULL,
    authors JSON,
    isbn TEXT,
    doi TEXT,
    publication_year INTEGER,
    page_count INTEGER,

    summary_short TEXT,
    summary_detailed TEXT,
    thesis TEXT,
    concepts JSON,
    embedding BLOB,
    provenance JSON,  -- per-field sources + model versions
    confidence JSON,  -- optional confidence scores

    zotero_key TEXT UNIQUE,
    content_path TEXT,  -- path to PDF if available
    source_snapshot_id TEXT,  -- immutable snapshot reference

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enriched_at TIMESTAMP
);

CREATE TABLE chapters (
    id TEXT PRIMARY KEY,
    material_id TEXT REFERENCES materials(id),
    number INTEGER,
    title TEXT,
    page_start INTEGER,
    page_end INTEGER,
    summary TEXT,
    concepts JSON,
    embedding BLOB,
    provenance JSON,
    confidence JSON
);

CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    depth TEXT DEFAULT 'working',  -- survey, working, expert
    status TEXT DEFAULT 'active',
    concepts JSON,
    embedding BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE knowledge (
    concept TEXT PRIMARY KEY,
    level TEXT,  -- unknown, heard_of, understand, can_explain, mastered
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reading_status (
    material_id TEXT PRIMARY KEY REFERENCES materials(id),
    status TEXT,  -- want_to_read, reading, finished, abandoned
    chapters_read JSON,  -- [1, 2, 5, 6]
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE TABLE interest_queue (
    id TEXT PRIMARY KEY,
    identifier TEXT,
    context TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Full-text search
CREATE VIRTUAL TABLE materials_fts USING fts5(
    title, authors, summary_short, summary_detailed, concepts
);

-- Vector search (with sqlite-vec)
CREATE VIRTUAL TABLE materials_vec USING vec0(
    embedding float[1536]
);
```

---

## Appendix B: LLM Prompts

### Book Summary

```
Analyze this book:

Title: {title}
Authors: {authors}
Description: {description}
Table of Contents:
{toc}

Provide exactly:

SHORT_SUMMARY: 2-3 sentences. What is this book about? Who should read it?

DETAILED_SUMMARY: 1-2 paragraphs covering the main topics, structure, and key insights.

THESIS: 1-2 sentences. What is the author's central argument or message?

CONCEPTS: 5-10 key concepts/topics this book covers (comma-separated).
```

### Chapter Summary

```
Summarize this chapter in 2-3 sentences:
- What is the main point?
- What will the reader learn?

Title: {title}
Content: {content}
```

### Relevance Check

```
How relevant is this book to the learning goal?

Book: {title}
Book summary: {summary}
Book concepts: {concepts}

Learning goal: {goal}
Goal depth: {depth}  // survey, working, or expert

Provide:
RELEVANCE: 0-100 (how well does this book serve this goal?)
REASONING: 1-2 sentences explaining the score
CHAPTERS: If only some chapters are relevant, which ones?
```

---

## Appendix C: Zotero Integration Details

### Local Database Access

Zotero stores data in SQLite at:
- macOS/Linux: `~/Zotero/zotero.sqlite`
- Windows: `%USERPROFILE%\Zotero\zotero.sqlite`

PDFs are stored in `~/Zotero/storage/<key>/`.

### Query for Items

```sql
SELECT
    items.key,
    itemTypes.typeName as type,
    MAX(CASE WHEN fields.fieldName = 'title' THEN itemDataValues.value END) as title,
    MAX(CASE WHEN fields.fieldName = 'abstractNote' THEN itemDataValues.value END) as abstract,
    MAX(CASE WHEN fields.fieldName = 'ISBN' THEN itemDataValues.value END) as isbn,
    MAX(CASE WHEN fields.fieldName = 'DOI' THEN itemDataValues.value END) as doi
FROM items
JOIN itemTypes ON items.itemTypeID = itemTypes.itemTypeID
LEFT JOIN itemData ON items.itemID = itemData.itemID
LEFT JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
LEFT JOIN fields ON itemData.fieldID = fields.fieldID
WHERE itemTypes.typeName NOT IN ('attachment', 'note')
  AND items.itemID NOT IN (SELECT itemID FROM deletedItems)
GROUP BY items.itemID;
```

### Type Mapping

| Zotero | Melvil |
|--------|--------|
| book, bookSection | book |
| journalArticle | article |
| conferencePaper, report, thesis, preprint | paper |
| webpage, blogPost | article |

---

## Appendix D: Dependencies

```toml
[project]
name = "melvil"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "click>=8.1",
    "rich>=13.0",
    "anthropic>=0.40",
    "openai>=1.50",
    "pyzotero>=1.5",
    "httpx>=0.27",
    "pydantic>=2.0",
    "sqlite-vec>=0.1",
]
```

---

*Named for Melvil Dewey, who believed in organizing knowledge to make it accessible. Melvil does for your personal library what Dewey did for public ones.*
