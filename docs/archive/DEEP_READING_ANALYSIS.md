# What Analytical and Syntopical Readers Actually Need

## The Reframe

The original Melvil design focused on **triage**: "What should I read?"

But the real target user is different:
- They've already read significant amounts
- They're motivated and committed to learning
- They want to go *deeper*, not just *wider*
- They struggle with the mechanical work of synthesis, not motivation

**The question isn't "what should I read?" but "how do I synthesize what I've read?"**

---

## Semantic Archive Alignment

This revised direction aligns with the semantic archive principles:
- **Capture first, structure progressively**: store passages and notes before formalizing arguments.
- **Pluralism of representations**: keep text, glossaries, argument maps, and annotations side by side.
- **Provenance and inspectability**: every extracted claim links back to the exact passage.
- **Retrieval as a process**: syntheses evolve through iterative questions, not one-shot queries.
- **Uncertainty and disagreement**: competing interpretations are preserved, not flattened.

---

## What Adler Actually Meant

### Analytical Reading (Single Work, Deep Understanding)

The goal: Truly understand what an author is saying and evaluate it critically.

**The steps:**
1. Classify the book (theoretical vs. practical, what field)
2. State the unity of the whole in a single sentence
3. Enumerate the major parts and their relationships
4. Define the problems the author is trying to solve
5. Find and understand the author's key terms
6. Locate the key propositions
7. Follow the author's arguments
8. Determine what the author solved vs. left unsolved
9. Criticize the book fairly

**The grunt work:**
- Extracting the argument structure (premises → conclusions)
- Building a glossary of how THIS author uses key terms
- Mapping the logical flow (chapter N depends on chapter M)
- Finding the author's actual thesis vs. what they claim it is
- Identifying unstated assumptions

### Syntopical Reading (Multiple Works, Constructing Understanding)

The goal: Address a question by bringing multiple authors into dialogue.

**The steps:**
1. Find relevant passages across many books
2. Bring authors to common terms (they use different words for same concepts)
3. Get clear on the questions being asked
4. Define the issues (where do authors disagree?)
5. Analyze the discussion (positions, arguments, evidence)
6. Form your own reasoned position

**The grunt work:**
- Finding WHERE each author addresses a question (passage location)
- Term translation ("consistency" means different things to different authors)
- Position mapping (Author A says X, Author B says Y, Author C says Z)
- Identifying genuine disagreements vs. terminological confusion
- Synthesizing a coherent view from partial perspectives

---

## What's Actually Hard (The Real Pain Points)

### Pain Point 1: "I read this book but can't articulate its argument"

You finished a book. You know it was good. But when someone asks "what's the main argument?" you fumble. The ideas haven't crystallized.

**What would help:**
- Prompted reflection: "In one sentence, what is the author's main claim?"
- Argument extraction: "Here are the 5 key propositions in chapter 3, how do they connect?"
- Thesis validation: "You said the thesis is X. Does the author's conclusion in chapter 12 support this?"

### Pain Point 2: "I can't find that passage I remember"

You remember reading something about consensus algorithms and the FLP impossibility theorem. But was it in DDIA? The Raft paper? That blog post? Which chapter?

**What would help:**
- Cross-library search: "Find all passages about FLP impossibility in my read materials"
- Passage retrieval with context: "Here's the passage, and here's how the author uses it in their argument"

### Pain Point 3: "These authors seem to disagree but I'm not sure about what"

Author A says eventual consistency is fine for most applications. Author B says strong consistency is essential. Are they actually disagreeing, or talking about different contexts?

**What would help:**
- Term comparison: "Here's how Author A defines 'eventual consistency' vs. Author B"
- Context extraction: "Author A is discussing social media feeds; Author B is discussing bank transfers"
- Disagreement mapping: "The actual disagreement is about X, not Y"

### Pain Point 4: "I've read 10 books on this topic but can't synthesize them"

You've read extensively on distributed systems. But your knowledge feels fragmented—isolated facts rather than a coherent mental model.

**What would help:**
- Concept inventory: "Across your 10 books, these are the 47 key concepts discussed"
- Coverage matrix: "Book A covers concepts 1-15, Book B covers concepts 8-25, ..."
- Gap identification: "Concept X is mentioned in 4 books but never deeply explained"
- Synthesis prompts: "How does Author A's view of CAP relate to Author B's view of PACELC?"

### Pain Point 5: "I want to understand concept X deeply"

You want to truly understand consensus algorithms. Not just "know about" them—understand them well enough to explain, critique, and apply.

**What would help:**
- Multi-source compilation: "Here's everything your library says about consensus"
- Progressive depth: "Start with DDIA ch.9 (overview), then Raft paper (mechanism), then Paxos (foundations)"
- Understanding verification: "Based on what you've read, answer these questions to check comprehension"

---

## The Real Product: A Reading Companion for Serious Learners

### Core Value Proposition

**Melvil helps you extract, connect, and synthesize ideas from what you've already read.**

It's not about choosing what to read. It's about getting more value from your reading.

### The Three Modes

#### Mode 1: Analytical Companion (Single Work)

When reading a book deeply:

```
$ melvil analyze "DDIA"

I'll help you read this analytically. As you read each chapter:
- I'll prompt you to articulate key arguments
- I'll help you build a glossary of the author's terms
- I'll ask you to connect chapters to the overall thesis

Start with: What kind of book is this? (theoretical/practical/mixed)
```

**Features:**
- Argument structure templates for each chapter
- Prompted reflection questions
- Key term extraction with your definitions
- Thesis development tracking (how does your understanding evolve?)

#### Mode 2: Passage Finder (Cross-Library Search)

When you need to find something:

```
$ melvil find "CAP theorem limitations"

Found 7 relevant passages across 4 materials:

1. DDIA, Ch. 9, p. 336-338
   "The CAP theorem is sometimes presented as Consistency, Availability,
   Partition tolerance: pick 2 out of 3. Unfortunately, this is misleading..."

2. Database Internals, Ch. 11, p. 284
   "CAP is often misunderstood. It doesn't say you must choose..."

3. Brewer's original paper, p. 4
   "The theorem states that..."

[View all passages] [Compare treatments] [Show in context]
```

**Features:**
- Semantic search across all your read materials
- Exact passage extraction with page numbers
- Cross-reference to see how different authors treat the same topic

#### Mode 3: Synthesis Helper (Syntopical Reading)

When constructing understanding across sources:

```
$ melvil synthesize "consistency models"

Building synthesis workspace for "consistency models"...

Authors in your library who discuss this:
- Kleppmann (DDIA) - extensive treatment
- Petrov (Database Internals) - technical deep-dive
- Helland (various papers) - practical perspective

Key terms and how each author uses them:
┌─────────────────┬─────────────────────────────────────────────────┐
│ Term            │ Definitions                                      │
├─────────────────┼─────────────────────────────────────────────────┤
│ Linearizability │ Kleppmann: "appears as if there is only one     │
│                 │ copy of the data" (p.324)                        │
│                 │ Petrov: "strongest single-object consistency"    │
│                 │ (p.291)                                          │
├─────────────────┼─────────────────────────────────────────────────┤
│ Serializability │ Kleppmann: "transactions behave as if executed  │
│                 │ serially" (p.329)                                │
│                 │ Petrov: distinguishes from linearizability       │
│                 │ (p.295)                                          │
└─────────────────┴─────────────────────────────────────────────────┘

Questions to explore:
1. When is linearizability necessary vs. overkill?
2. How do these authors view the consistency/availability tradeoff?
3. What practical advice do they give for choosing a model?

[Deep dive on question 1] [Map positions] [Export notes]
```

**Features:**
- Automatic term glossary across authors
- Position mapping on key questions
- Guided synthesis with prompts
- Export to Obsidian/Notion for permanent notes

---

## Revised Data Model

The original model tracked materials and concepts. The new model needs:

### Reading Annotations
```sql
-- Your engagement with specific passages
CREATE TABLE annotations (
    id TEXT PRIMARY KEY,
    material_id TEXT REFERENCES materials(id),
    passage_start INTEGER,  -- character offset or page
    passage_end INTEGER,
    passage_text TEXT,

    -- Your analytical work
    annotation_type TEXT,  -- 'key_term', 'argument', 'question', 'connection'
    your_note TEXT,

    provenance JSON,  -- source snapshot, model/version if auto-extracted
    confidence REAL,
    created_at TIMESTAMP
);
```

### Term Glossary
```sql
-- How different authors define terms
CREATE TABLE term_definitions (
    id TEXT PRIMARY KEY,
    term TEXT NOT NULL,  -- normalized term
    term_as_written TEXT,  -- how the author wrote it
    material_id TEXT REFERENCES materials(id),
    definition TEXT,
    passage_location TEXT,  -- where they define it
    your_understanding TEXT,  -- your synthesis
    provenance JSON,
    confidence REAL
);
```

### Competing Interpretations
```sql
-- Preserve disagreement and evolution of meaning over time
CREATE TABLE interpretations (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,  -- e.g., "CAP theorem implications"
    material_id TEXT REFERENCES materials(id),
    stance TEXT,  -- author's position or your summary
    evidence_passages JSON,  -- passage ids or locations
    created_at TIMESTAMP,
    superseded_by TEXT  -- optional link to newer interpretation
);
```

### Synthesis Workspaces
```sql
-- Active syntopical reading projects
CREATE TABLE synthesis_projects (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    guiding_questions JSON,  -- questions you're exploring
    materials JSON,  -- which materials are part of this synthesis
    status TEXT,  -- 'active', 'paused', 'completed'

    -- Your developing synthesis
    current_thesis TEXT,
    key_insights JSON,
    remaining_questions JSON,

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Argument Maps
```sql
-- Extracted argument structures
CREATE TABLE arguments (
    id TEXT PRIMARY KEY,
    material_id TEXT REFERENCES materials(id),
    chapter TEXT,

    claim TEXT,  -- what the author is arguing
    premises JSON,  -- supporting points
    evidence JSON,  -- evidence cited
    conclusion TEXT,

    your_evaluation TEXT,  -- do you find this convincing?
    connections JSON  -- links to other arguments
);
```

---

## The New CLI

```bash
# === Active Reading ===
melvil read "DDIA"                     # Start analytical reading session
melvil read "DDIA" --chapter 5         # Focus on specific chapter
melvil reflect                          # Prompted reflection on current reading
melvil term "linearizability"          # Add/view term definition

# === Passage Finding ===
melvil find "CAP theorem"              # Search across library
melvil find "consensus" --in "DDIA"    # Search within one book
melvil passages "FLP impossibility"    # Get exact passages with locations

# === Synthesis ===
melvil synthesize "consistency models" # Start synthesis workspace
melvil compare "Kleppmann" "Petrov" --on "consistency"
melvil positions "eventual consistency"  # Map author positions
melvil terms "consistency"             # Compare term definitions

# === Knowledge Mapping ===
melvil map                             # Visualize what you know
melvil map "distributed systems"       # Map a specific area
melvil gaps                            # What's missing in your understanding?
melvil connections "CAP" "PACELC"      # How do concepts relate?

# === Export ===
melvil export "consistency models" --to obsidian
melvil export-terms --format markdown
```

---

## What This Actually Looks Like

### Scenario: Mastering Consistency Models

**Week 1: Analytical reading of DDIA chapters 7-9**

```
$ melvil read "DDIA" --chapter 7

Starting analytical reading of Chapter 7: Transactions

As you read, I'll prompt you to:
□ Identify the main problem this chapter addresses
□ Note how Kleppmann defines key terms
□ Trace the argument structure
□ Mark passages you want to revisit

Ready? Let's start with: What problem is this chapter trying to solve?

> Transactions provide guarantees that make it easier to reason about
> concurrent operations and failures

Good. Kleppmann would say it more specifically. As you read the intro,
refine this. What specific guarantees does he focus on?
```

**Week 2: Adding a second source**

```
$ melvil synthesize "transactions"

You've read about transactions in:
- DDIA Ch. 7 (your notes: 12 annotations, 8 terms defined)

Adding "Database Internals" to synthesis...

Petrov covers transactions in Ch. 5 and 12. Comparing with Kleppmann:

Terminology alignment:
- Both use "ACID" but Petrov emphasizes implementation details
- Kleppmann's "serializable isolation" = Petrov's "serializable SI" (verify?)

New concepts Petrov introduces:
- ARIES recovery algorithm (not in DDIA)
- Lock-free data structures (mentioned briefly in DDIA)

Suggested reading order:
1. Petrov Ch. 5 (overlaps with DDIA - skim for new perspectives)
2. Petrov Ch. 12 (new material on recovery)

Start comparison? [y/n]
```

**Week 3: Synthesis**

```
$ melvil positions "isolation levels"

Mapping positions on "isolation levels":

                    Kleppmann        Petrov           Your synthesis
                    ──────────       ──────           ──────────────
Read Committed      "default in      "good enough
                    many DBs"        for most"        ?

Snapshot Isolation  "prevents        "watch for
                    many anomalies"  write skew"      ?

Serializable        "gold standard   "expensive,
                    but costly"      rarely needed"   ?

Both authors agree: Start with Read Committed, upgrade when needed.
Both warn about: Write skew in Snapshot Isolation.
Key difference: Petrov more skeptical of serializable's practical value.

Your turn: Based on your reading, what's your position?

> _
```

---

## Why This Is Different

### Original Melvil
- **Problem**: Too many books, what to read?
- **Solution**: Triage and recommendations
- **Mode**: Passive (system tells you what to do)
- **Value**: Time saved on evaluation

### Revised Melvil
- **Problem**: I've read books but can't synthesize them
- **Solution**: Active reading support and synthesis tools
- **Mode**: Active (you're doing the learning, system assists)
- **Value**: Deeper understanding, lasting knowledge

### The Key Insight

**You can't automate understanding. But you can automate the clerical work around it.**

- Finding passages: tedious but mechanical → automate
- Comparing definitions: tedious but mechanical → automate
- Mapping positions: tedious but mechanical → automate
- Building glossaries: tedious but mechanical → automate

**What stays human:**
- Deciding what questions matter
- Evaluating arguments
- Forming your own synthesis
- Developing genuine understanding

Melvil does the grunt work so you can do the thinking.

---

## Minimum Viable Product (Revised)

### Phase 1: Passage Finder
Just this:

```
$ melvil index "DDIA"
Indexing DDIA... chunking... embedding... done.

$ melvil find "consistency vs availability tradeoff"

Found 8 passages:

1. Ch. 9, p. 336: "The CAP theorem is sometimes presented as..."
2. Ch. 9, p. 338: "In practice, partition tolerance is not negotiable..."
3. Ch. 5, p. 183: "The trade-off between consistency and latency..."
...
```

**Value**: You can search your actual books semantically. No more "I know I read this somewhere."

### Phase 2: Term Glossary
Add:
```
$ melvil define "linearizability" --from "DDIA"
Extracting definition from DDIA...

Kleppmann defines linearizability (p. 324):
"[A system] appears as if there is only one copy of the data,
and all operations on it are atomic."

Also called: "atomic consistency", "strong consistency"
Related terms: serializability (different!), sequential consistency

Add your own understanding? [y/n]
```

**Value**: Build a glossary of how terms are used, with sources.

### Phase 3: Synthesis Workspace
Add:
```
$ melvil synthesize "consensus algorithms"
```

**Value**: Structured support for syntopical reading across multiple sources.

---

## Technical Requirements

### Must Have (Different from Original)

1. **Full-text indexing of PDFs** - Can't find passages without content
2. **Passage-level embeddings** - Semantic search at paragraph level, not book level
3. **Citation/page tracking** - Must link back to exact locations
4. **Incremental annotation** - Add notes as you read, not just after
5. **Provenance + temporal snapshots** - Preserve source context and evolution

### Nice to Have

1. **OCR for scanned PDFs** - Many academic books are scans
2. **EPUB support** - Better structure than PDF
3. **Highlighting import** - From Kindle, Apple Books, etc.
4. **Obsidian/Notion export** - Where permanent notes live

---

## The Honest Value Proposition

**For serious readers who want to master topics, not just read about them:**

Melvil helps you:
1. **Find** what you've read (passage-level search across your library)
2. **Clarify** how authors use terms (cross-source glossary)
3. **Compare** what authors say (position mapping)
4. **Synthesize** your own understanding (structured workspace)

It doesn't read for you. It makes your reading count for more.
