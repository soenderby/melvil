# Melvil MVP Spec (Synthesis Workspace)

## Purpose
Deliver immediate value by helping users **assemble and synthesize** what they have read. The MVP focuses on building a synthesis workspace with explicit provenance, starting from user-selected sources and passages.

---

## MVP Goals

- Create a synthesis workspace around a topic or question.
- Capture passages or excerpts with stable references and provenance.
- Assemble excerpts into a structured outline or narrative.
- Export the workspace to a durable format (Markdown).
- Minimize capture friction with a guided flow and optional PDF prefill.

---

## Non-Goals (MVP)

- Automated recommendations or relevance scoring.
- Concept extraction, term definitions, or argument maps.
- Correction loops for summaries or concepts (Phase 2).
- Embedding-based discovery or cross-library semantic search.
- Full browsing experience beyond the workspace.

---

## Primary Workflow

1. **Create workspace** for a topic.
2. **Add sources** (Zotero items or manual entries).
3. **Capture passages** (guided capture with optional PDF prefill).
4. **Add reading prompts** (thesis, key terms, arguments, interpretations) as notes.
5. **Assemble** passages and notes into a working outline.
6. **Find within workspace** (fast scan across captured passages and notes).
7. **Export** the synthesis to Markdown.

---

## Minimal Data Model

```sql
materials (
  id, type, title, authors, year, identifiers_json,
  zotero_key, content_path, source_snapshot_id,
  created_at, updated_at
)

source_snapshots (
  id, material_id, captured_at, source_type, source_ref, hash
)

passages (
  id, material_id, source_snapshot_id, page_start, page_end,
  text, start_offset, end_offset, created_at
)

synthesis_projects (
  id, topic, guiding_questions_json,
  status, created_at, updated_at
)

synthesis_items (
  id, synthesis_id, item_type,  -- passage|note|thesis|term|argument|interpretation
  passage_id, note_text, position,
  created_at
)

synthesis_index (
  id, synthesis_id, kind,  -- passage|note
  text, created_at
)
```

Notes:
- `source_snapshot_id` is required for any passage.
- The MVP allows manual passage entry to reduce parsing risk.
- Page references should be tied to a specific snapshot/edition to avoid drift.
- `start_offset`/`end_offset` are optional when text extraction is available; if missing, keep `page_start`/`page_end` and `source_snapshot_id`.

---

## Ingestion (MVP)

- Import **metadata only** from Zotero when available.
- Capture a **source snapshot** (metadata + file hash).
- Optional: manual passage entry from PDFs or notes.
- Optional: PDF prefill for passages by page range when a local file is available.

---

## CLI Surface (MVP)

```bash
# Workspace
melvil synthesize "consistency models"
melvil synth show "consistency models"

# Sources
melvil synth add-source "DDIA"
melvil synth add-source --manual "Paxos Made Simple"

# Passages
melvil synth add-passage --source "DDIA" --page 323-325 --text "..."
melvil synth add-passage --source "DDIA" --page 323-325 --from-pdf
melvil synth capture "DDIA" --page 323-325 --type passage
melvil synth add-note --type thesis --text "Primary claim: consistency requires explicit tradeoffs."
melvil synth add-note --type term --text "Linearizability: appears as if a single copy exists."
melvil synth add-note --type argument --text "CAP implies partitions force latency or staleness."
melvil synth add-note --type interpretation --text "Author B treats CAP as an availability warning."

# Find (workspace-scoped)
melvil synth find "consistency" --in "consistency models"

# Export
melvil synth export "consistency models" --format markdown
```

Output requirements:
- Every passage shows its source and page reference.
- Capture flows show source snapshot hash and page range before save.
- Workspace export preserves ordering and provenance.

---

## Acceptance Criteria

- A user can create a workspace and assemble at least 5 sourced passages in under 10 minutes.
- Each passage includes a visible source reference in the workspace and export.
- The workspace includes at least one thesis note, one term note, and one interpretation note.
- Export produces a single Markdown file with sections for passages and notes.
- A user can capture a passage with `--from-pdf` and edit it before saving.
- `melvil synth find` returns results within the workspace in under 1 second for 1k passages/notes.

---

## Phase 2 Hooks (Not in MVP)

- Correction loop for summaries and concepts.
- Term definitions and concept normalization.
- Cross-library retrieval via FTS/embeddings.
