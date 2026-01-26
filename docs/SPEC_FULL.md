# Melvil Full System Spec (Semantic Archive)

## Purpose
Melvil is a **semantic archive** for learning-directed reading. It preserves sources, captures meaning in multiple forms, and helps users recompute relevance as their questions change. This spec consolidates prior designs and orients the system around the semantic archive principles.

This document is the full-system product and technical reference. The MVP spec lives in `docs/SPEC_MVP.md`. Other documents are archived for context.

---

## Core Problem Statement
The challenge is not storing information, but **preserving and reactivating meaning**.

Key constraints:
- Relevance is contextual and question-dependent.
- Meaning is social, embodied, time-dependent, and contested.
- No single representational scheme is sufficient.

Therefore, Melvil must support:
- Multiple representations of the same material
- Question-driven, iterative retrieval
- Transparency, provenance, and temporal awareness

---

## Guiding Design Principles

1. **Capture first, structure progressively**
2. **Pluralism of representations** (text, metadata, embeddings, graphs, narratives)
3. **Provenance and inspectability** for every derived artifact
4. **Retrieval as a process**, not a single query
5. **Uncertainty and disagreement are preserved**

Summaries and derived outputs **orient**; sources decide.

---

## Primary User Purposes

1. **Orientation and sensemaking** in a domain or project
2. **Recall and verification** of exact passages and sources
3. **Decision support** with evidence and tradeoffs
4. **Discovery and insight** via connections and analogies
5. **Memory externalization** with retrievability over time

---

## Interaction Modes

Melvil supports multiple cognitive modes and smooth transitions between them:
- **Browsing**: timelines, facets, clusters, TOCs
- **Inspecting**: close reading of original sources
- **Assembling**: synthesizing excerpts into narratives
- **Contributing**: annotation, curation, refinement

---

## Conceptual Architecture

### Layered Semantic Stack

- **Layer 0: Immutable sources**
  - PDFs, notes, metadata snapshots, versioned attachments
- **Layer 1: Metadata and facets**
  - authors, dates, domains, projects, permissions
- **Layer 2: Information retrieval index**
  - FTS for precise, auditable retrieval
- **Layer 3: Semantic embeddings**
  - fuzzy recall, similarity, discovery
- **Layer 4: Structured meaning**
  - term definitions, claims, arguments, relations

Meaning emerges from **interaction between layers**, not any single layer.

---

## Data Model (Canonical)

This model is additive and provenance-first. All derived artifacts include source links, timestamps, and model/version identifiers.

```sql
materials (
  id, type, title, authors, year, identifiers_json,
  zotero_key, content_path, source_snapshot_id,
  created_at, updated_at
)

source_snapshots (
  id, material_id, captured_at, source_type, source_ref, hash
)

chapters (
  id, material_id, number, title, parent_id,
  page_start, page_end
)

passages (
  id, material_id, chapter_id, start_offset, end_offset,
  text, page_start, page_end
)

summaries (
  id, material_id, chapter_id, scope, text,
  provenance_json, confidence, created_at
)

concepts (
  id, name, normalized
)

concept_links (
  id, material_id, chapter_id, passage_id, concept_id,
  confidence, provenance_json, created_at, user_confirmed
)

term_definitions (
  id, term, term_as_written, material_id, passage_id,
  definition, provenance_json, confidence, created_at
)

interpretations (
  id, topic, material_id, stance, evidence_passages_json,
  created_at, superseded_by
)

annotations (
  id, material_id, passage_id, annotation_type, note,
  provenance_json, confidence, created_at
)

synthesis_projects (
  id, topic, guiding_questions_json, materials_json,
  current_thesis, key_insights_json, remaining_questions_json,
  status, created_at, updated_at
)

workspace_index (
  id, synthesis_id, kind, text, created_at
)
```

Notes:
- `provenance_json` includes source snapshot id, model/version, and extraction method.
- `confidence` is optional but visible when present.
- Prior versions are preserved; new generations append, not overwrite.

---

## Ingestion Pipeline

1. **Sync metadata** from Zotero or other sources
2. **Capture source snapshot** (metadata + file hash)
3. **Import TOC** from metadata where available
4. **Extract text** from PDFs (or EPUB) if available
5. **Segment passages** with stable offsets and page references
6. **Generate summaries** with provenance and confidence
7. **Extract concepts and term definitions** with provenance
8. **Index** into FTS and vector layers

---

## Retrieval as a Process

A retrieval session is iterative and transparent:
1. Start from a question
2. Surface candidates from FTS and semantic layers
3. Show **why** results appear (signals, sources, confidence)
4. Inspect original passages
5. Refine the question or assemble a synthesis

---

## Product Scope (Full System)

The full system supports:
- Source snapshots and provenance across all derived artifacts
- TOC capture, text extraction, and passage indexing
- FTS and semantic embeddings for recall and discovery
- Inspectable summaries, concepts, and term definitions
- Synthesis workspaces, interpretations, and argument tracking
- Iterative retrieval with provenance-first inspection paths

This spec intentionally avoids promise of black-box recommendations.

---

## MVP Reference

The MVP is defined in `docs/SPEC_MVP.md`. It **starts with the synthesis workspace** and a minimal ingest path, with correction workflows deferred to Phase 2.

---

## CLI and UX Surface

The CLI is a primary interface but must support multiple modes:

```bash
# Ingest
melvil zotero sync
melvil ingest --toc
melvil ingest --title "DDIA"

# Browse / Inspect
melvil toc "DDIA"
melvil toc "DDIA" --explain
melvil find "CAP theorem"        # passage retrieval
melvil show "DDIA" --sources     # provenance view

# Concepts / Terms
melvil concepts "DDIA"
melvil terms "consistency"

# Synthesis
melvil synthesize "consistency models"
melvil assemble "consistency models" --add "DDIA" --passages 12,13,14
melvil synth capture "DDIA" --page 323-325 --type passage
melvil synth find "consistency" --in "consistency models"
```

CLI output must:
- show provenance and confidence where relevant
- preserve access to original passages
- allow iterative refinement
- surface source snapshot hash and page range in capture/edit flows

---

## Anti-Patterns to Avoid

- **Premature ontology freezing**
- **Overconfident summarization**
- **Single-mode interaction**
- **Relevance as a black box**
- **Forgetting time**

---

## Evaluation Metrics

- Coverage: % of library with TOC and passages indexed
- Provenance completeness: % of derived artifacts with snapshot + model metadata
- Retrieval quality: time to find a relevant passage
- User trust signals: corrections, confirmations, and revisits

---

## Phased Delivery (Aligned with Semantic Archive)

### Phase 1: Synthesis Workspace (MVP)
- Minimal ingest (metadata + optional text import)
- Passage capture with stable references
- Guided capture flow with optional PDF prefill
- Workspace creation and assembly of excerpts
- Provenance display for every excerpt
- Workspace-scoped find across captured passages and notes

### Phase 2: Clarify + Correct
- Correction loop for summaries and concepts
- Term definitions with source links
- Concept normalization and browsing

### Phase 3: Retrieval Expansion
- FTS + embeddings across passages
- Cross-source comparisons and interpretations
- Export to external notes

---

## Status of Prior Docs

Legacy design documents are archived in `docs/archive/` for historical context. This spec supersedes them.
