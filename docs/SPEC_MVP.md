# Melvil MVP Spec (Synthesis Workspace)

## Purpose
Deliver immediate value by helping users **assemble and synthesize** what they have read. The MVP focuses on building a synthesis workspace with explicit provenance, starting from user-selected sources and passages.

---

## MVP Goals

- Create a synthesis workspace around a topic or question.
- Capture passages or excerpts with stable references and provenance.
- Assemble excerpts into a structured outline or narrative.
- Export the workspace to a durable format (Markdown).

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
3. **Capture passages** (manual paste or simple extraction).
4. **Assemble** passages and notes into a working outline.
5. **Export** the synthesis to Markdown.

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
  id, material_id, page_start, page_end,
  text, created_at
)

synthesis_projects (
  id, topic, guiding_questions_json,
  status, created_at, updated_at
)

synthesis_items (
  id, synthesis_id, item_type,  -- passage|note
  passage_id, note_text, position,
  created_at
)
```

Notes:
- `source_snapshot_id` is required for any passage.
- The MVP allows manual passage entry to reduce parsing risk.

---

## Ingestion (MVP)

- Import **metadata only** from Zotero when available.
- Capture a **source snapshot** (metadata + file hash).
- Optional: manual passage entry from PDFs or notes.

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
melvil synth add-note --text "Key tradeoff: availability vs consistency"

# Export
melvil synth export "consistency models" --format markdown
```

Output requirements:
- Every passage shows its source and page reference.
- Workspace export preserves ordering and provenance.

---

## Acceptance Criteria

- A user can create a workspace and assemble at least 5 sourced passages in under 10 minutes.
- Each passage includes a visible source reference in the workspace and export.
- Export produces a single Markdown file with sections for passages and notes.

---

## Phase 2 Hooks (Not in MVP)

- Correction loop for summaries and concepts.
- Term definitions and concept normalization.
- Cross-library retrieval via FTS/embeddings.
