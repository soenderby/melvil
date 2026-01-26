# Melvil Revised Spec (TOC + Concepts Overview)

**Purpose**: Build a structured overview of your to-read library by collecting tables of contents, clarifying vague chapter titles, and surfacing core concepts per book and chapter.

---

## 1. Core Value Proposition

Melvil helps you quickly scan *what you want to read* and decide where to focus by providing:
- **TOC-first outlines** for each book.
- **Clarifying blurbs** for vague chapter titles.
- **Core concepts** per book and chapter.
- **Cross-library browsing** by concept and chapter topic.

This is not a recommendation engine. It is a structured map of your backlog.

---

## 2. Target User

A motivated reader who:
- Collects books/papers to read later.
- Wants a high-level map of what each item contains.
- Prefers quick scanning over deep synthesis.

---

## 3. Product Capabilities (MVP)

### 3.1 TOC Indexing
- Import TOC from Zotero metadata when available.
- If metadata lacks TOC, extract from PDF text if present.
- Normalize chapters into a consistent structure (number, title, optional subheadings).

**Example**:
```
$ melvil toc "DDIA"
1. Reliable, Scalable, and Maintainable Applications
2. Data Models and Query Languages
3. Storage and Retrieval
...
```

### 3.2 Clarifying Blurms for Vague Titles
- Detect vague titles (e.g., "Foundations", "Overview", "Discussion").
- Generate 1-2 sentence summaries using nearby TOC context or extracted chapter text.
- Mark provenance (metadata-derived vs. text-derived vs. user-edited).

**Example**:
```
$ melvil toc "DDIA" --explain
2. Data Models and Query Languages
   Clarifies relational, document, and graph models, and how they affect query design.
```

### 3.3 Core Concepts Extraction
- Extract 5-10 concepts per book, and 2-5 per chapter.
- Deduplicate and normalize concepts across the library.
- Allow user edits and confirmations.

**Example**:
```
$ melvil concepts "DDIA"
Book concepts: replication, partitioning, transactions, consistency models, stream processing

$ melvil concepts "DDIA" --chapter 6
Chapter concepts: partitioning, sharding, rebalancing
```

### 3.4 Cross-Library Browsing
- Show all chapters that mention a concept.
- Allow filtering by material type and status (to-read vs. reading vs. read).

**Example**:
```
$ melvil browse "consistency"
DDIA ch. 9
Database Internals ch. 11
Paxos Made Simple (section 2)
```

---

## 4. Non-Goals (MVP)

- Relevance scoring and recommendations.
- Deep passage retrieval or argument extraction.
- Chapter guidance without available text/metadata.
- Web UI or browser extension.

---

## 5. Data Model (SQLite)

### 5.1 Core Tables
```sql
materials (id, type, title, authors, year, zotero_key, source_path)
materials_status (material_id, status, updated_at) -- status: to_read|reading|read

chapters (id, material_id, number, title, level, parent_id)
chapter_blurbs (id, chapter_id, blurb, provenance, user_confirmed)

concepts (id, name, normalized)
chapter_concepts (chapter_id, concept_id, confidence, user_confirmed)
material_concepts (material_id, concept_id, confidence, user_confirmed)
```

### 5.2 Provenance
- `provenance` values: `metadata`, `pdf_text`, `llm`, `user`.
- Every blurb and concept includes provenance and optional `user_confirmed`.

---

## 6. Ingestion Pipeline

1. **Sync metadata** from Zotero.
2. **Capture TOC** from metadata if present.
3. **Fallback extraction** from PDF text if TOC missing.
4. **Normalize chapters** into a consistent tree.
5. **Generate blurbs** for vague titles when text is available.
6. **Extract concepts** per chapter and per book.

---

## 7. CLI Commands (MVP)

```bash
# Sync and ingest
melvil zotero sync
melvil ingest --toc
melvil ingest --title "DDIA"

# TOC and blurbs
melvil toc <title>
melvil toc <title> --explain

# Concepts
melvil concepts <title>
melvil concepts <title> --chapter <n>

# Cross-library browsing
melvil browse <concept>
```

Design rules:
- Titles are primary identifiers, but results always show stable IDs.
- Output is scannable and optimized for quick review.

---

## 8. UX Principles

- **TOC-first**: outlines are the primary surface.
- **Sparse by default**: show blurbs only when they add clarity.
- **Editable**: users can correct blurbs and concepts.
- **Provenance visible**: always show data source.

---

## 9. Evaluation Metrics

- TOC coverage rate across the library.
- User confirmations of blurbs/concepts.
- Time to find a relevant chapter on a topic.
- Return usage (do users revisit the overview?).

---

## 10. Future Phases (Post-MVP)

- Passage retrieval for deep lookup.
- Reading progress tracking tied to chapters.
- Goal-based recommendations after TOC coverage is high.
