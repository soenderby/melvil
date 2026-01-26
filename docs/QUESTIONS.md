# Melvil: Open Design Questions

Design questions to validate before committing to implementation decisions.

---

## Phase 1 Questions (Resolve Before Building)

### Q1: How granular should concepts be?

**Context**: Concepts can exist at different levels of granularity:
- Broad: "distributed systems"
- Medium: "consensus"
- Narrow: "Paxos Phase 1"

**Options**:
1. **User decides** — No guidance; concepts are whatever users create
2. **Encourage medium granularity** — UI/docs suggest concepts should be "learnable in one sitting"
3. **Support hierarchy** — Concepts can have parent/child relationships (already in schema)

**Questions to explore**:
- When you think about "concepts," what level of abstraction feels natural?
- Would you want "consensus" and "Paxos" as separate concepts, or Paxos as a sub-concept?
- How do you currently organize topics in your head or on paper?

**Decision needed**: Should we actively guide granularity, or let it emerge?

---

### Q2: What relationship types matter?

**Current design** includes these concept-to-concept link types:
- `related` — General connection
- `prerequisite` — Understanding A requires understanding B
- `contradicts` — A and B are in tension
- `specializes` — A is a specific case of B
- `generalizes` — A is a general case of B
- `implements` — A is a concrete realization of B

**Questions to explore**:
- When you connect two ideas, what kinds of relationships do you typically note?
- Are these types sufficient? Too many? Wrong categories?
- Do you distinguish "requires" from "builds on" from "is related to"?

**Decision needed**: Final set of link types for MVP.

---

### Q3: How should the map be displayed in CLI?

**Options**:
1. **Tree/hierarchy** — Nested indentation (current `melvil map` design)
2. **Table** — Flat list with columns for relationships
3. **Adjacency list** — Each concept with its neighbors
4. **Defer to Phase 2** — Just export to JSON/Markdown; visual display later

**Questions to explore**:
- Show mockups of each; which is most useful for navigation?
- Would you primarily use CLI map display, or export to another tool?
- What information is most important to see at a glance?

**Decision needed**: Map display format for MVP.

---

### Q4: How should notes connect to multiple things?

**Current design**: A note has optional links to one concept, one book, and one chapter.

**Problem**: What if a note relates to multiple concepts? Or compares two books?

**Options**:
1. **Single link each** — Keep it simple; create multiple notes if needed
2. **Multiple concepts allowed** — Note can link to many concepts (junction table)
3. **Full many-to-many** — Notes can link to multiple concepts AND multiple books

**Questions to explore**:
- Do your notes typically relate to one concept or many?
- If a note compares two ideas, would you create one note or two?
- Is simplicity more valuable than flexibility here?

**Decision needed**: Note linking cardinality.

---

### Q5: What metadata matters for book-concept links?

**Current design** includes:
- `treatment` — How the book handles the concept (introduces, discusses, applies, critiques, mentions)
- `importance` — How central the concept is to the book (central, significant, mentioned)
- `location` — Where in the book (chapter reference, page range)

**Questions to explore**:
- Is this the right set of attributes?
- Do you actually think in terms of "treatment" and "importance"?
- What would you want to record when noting "DDIA covers consensus"?

**Decision needed**: Finalize book-concept link attributes.

---

## Phase 2 Questions (Inform Future Design)

### Q6: How should synthesis work?

**Context**: Phase 2 adds structure notes for synthesis—organizing accumulated notes into coherent arguments.

**Options**:
1. **Note-centric** — Structure notes reference individual notes; you assemble note-by-note
2. **Concept-centric** — Structure notes reference concepts; all notes on that concept come in
3. **Hybrid** — Can add individual notes OR entire concepts
4. **Outline-first** — Create an outline structure, then fill in with notes

**Questions to explore**:
- When you synthesize, do you start with an outline or let structure emerge?
- Would you want to pull in "all notes on consensus" or select specific notes?
- How much commentary/connective tissue do you write between quoted notes?

**Decision needed**: Structure note assembly model.

---

### Q7: What helps you re-orient after time away?

**Context**: Phase 2 adds navigation aids (landmarks, path finding, recent activity, visualization) to help users re-orient after being away from their map.

**Options for "where was I?"**:
1. **Session tracking** — Automatically record what you were exploring; offer "resume"
2. **Manual bookmarks** — User explicitly marks "come back to this"
3. **Both** — Automatic tracking plus manual bookmarks

**Questions to explore**:
- When you return to a project after weeks/months, how do you currently re-orient?
- Would automatic "you were here" tracking be helpful or creepy?
- What information helps most: last concepts viewed? Last notes written? Last books touched?

**Decision needed**: Session tracking approach.

---

### Q8: How important is visualization?

**Context**: Phase 2 plans graph visualization. But building good visualization is significant work.

**Options**:
1. **Terminal (TUI)** — Interactive graph in terminal using Textual
2. **Web** — Local web server with D3.js or similar
3. **Export only** — Export to Obsidian/Graphviz; use their visualization
4. **Skip it** — Text-based navigation is sufficient

**Questions to explore**:
- How important is seeing the graph visually vs. navigating it textually?
- Would you use built-in visualization, or export to a tool you already use?
- What decisions would visualization help you make?

**Decision needed**: Visualization approach for Phase 2.

---

### Q9: What import sources matter most?

**Phase 3 plans imports from**:
- Obsidian vault
- Roam export
- Kindle highlights
- Readwise

**Questions to explore**:
- What tools do you currently use for notes and highlights?
- If you have existing notes, where are they?
- Would you migrate existing notes into Melvil, or start fresh?

**Decision needed**: Import priority order.

---

### Q10: Should Melvil suggest concepts from TOC?

**Context**: When importing a book's TOC, Melvil could suggest concepts based on chapter titles.

**Options**:
1. **No suggestions** — User creates all concepts manually
2. **Chapter titles as starting point** — Show "Chapter 9: Consistency and Consensus" and let user extract concepts
3. **LLM-assisted extraction** — Use AI to suggest concepts from chapter titles (requires API key, cost)

**Questions to explore**:
- Would automated concept suggestions be helpful or noisy?
- Do you trust AI-extracted concepts, or prefer to identify them yourself?
- Is the manual work of concept identification part of the learning value?

**Decision needed**: Concept suggestion approach.

---

### Q11: How should notes integrate with external tools?

**Context**: Many users have existing note systems (Obsidian, Notion, etc.).

**Options**:
1. **Melvil is primary** — Notes live in Melvil; export when needed
2. **Melvil is index** — Notes live elsewhere; Melvil tracks concepts and links
3. **Bidirectional sync** — Keep Melvil and external tool in sync (complex)

**Questions to explore**:
- Where do your permanent notes currently live?
- Would you move notes into Melvil, or want Melvil to point to external notes?
- How important is integration with your existing system?

**Decision needed**: Note storage philosophy.

---

## Validation Questions (User Research)

### Q12: Is this the right problem?

**Core assumption**: Readers building expertise need help externalizing and navigating their concept map.

**To validate**:
- Interview 5-8 target users
- Ask about their current reading and note-taking workflow
- Show Melvil concept and ask if it addresses a real pain point

**Questions to ask**:
1. "Describe how you currently track what you've read and learned."
2. "When you're deep in a topic, how do you keep track of how ideas connect?"
3. "What's frustrating about your current approach?"
4. "If you could externalize the map in your head, what would it look like?"

---

### Q13: Is CLI the right interface?

**Current assumption**: Target users are comfortable with command-line tools.

**To validate**:
- Show CLI mockups to potential users
- Ask about their tool preferences
- Observe comfort level with terminal-based workflows

**Questions to ask**:
1. "What's your comfort level with command-line tools?" (1-5)
2. "Would you use a CLI tool daily for note-taking?"
3. "What would make you prefer CLI over a graphical interface?"

---

### Q14: Does the Zettelkasten framing resonate?

**Current assumption**: Framing notes as "fleeting/literature/permanent" is helpful.

**To validate**:
- Ask users about their familiarity with Zettelkasten
- Test whether the note types make sense
- See if users want this structure or find it constraining

**Questions to ask**:
1. "Are you familiar with the Zettelkasten method?"
2. "Do you distinguish between different types of notes?"
3. "Would 'fleeting/literature/permanent' categories help or hinder you?"

---

## Research Tracking

| Question | Status | Method | Findings |
|----------|--------|--------|----------|
| Q1: Concept granularity | Not started | Interview | — |
| Q2: Relationship types | Not started | Interview | — |
| Q3: Map display | Not started | Mockup test | — |
| Q4: Note linking | Not started | Interview | — |
| Q5: Book-concept metadata | Not started | Interview | — |
| Q6: Synthesis workflow | Not started | Interview | — |
| Q7: Re-orientation aids | Not started | Interview | — |
| Q8: Visualization | Not started | Interview | — |
| Q9: Import sources | Not started | Survey | — |
| Q10: Concept suggestions | Not started | Prototype | — |
| Q11: External tools | Not started | Interview | — |
| Q12: Problem validation | Not started | Interview | — |
| Q13: CLI preference | Not started | Usability | — |
| Q14: Zettelkasten framing | Not started | Interview | — |

---

## Quick Decisions (Make During Implementation)

These can be decided during implementation without formal research:

- **Alias case sensitivity**: Case-insensitive (already in schema)
- **Default depth for new books**: `listed`
- **Default note type**: `permanent`
- **Chapter number format**: Free text (supports "1", "2.3", "IV", etc.)
- **Concept name uniqueness**: Required (UNIQUE constraint)
- **Note minimum length**: None (allow short notes)

---

## Decisions Made

Document decisions here as they're made:

| Question | Decision | Rationale | Date |
|----------|----------|-----------|------|
| — | — | — | — |
