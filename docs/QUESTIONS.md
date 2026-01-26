# Melvil: Open Design Questions

This document lists unresolved design questions that should be answered through user research before committing to implementation decisions. Questions are organized by priority and topic.

---

## Critical Questions (Block Phase 2)

These questions affect core architecture. Answer before expanding beyond MVP.

### Q1: What is the actual entry point?

**Current assumption**: Users start with "create workspace for topic, then add sources."

**Alternative hypothesis**: Users start with "I'm reading this book, help me capture notes."

**Research method**: User interviews (5-8 target users)

**Questions to ask**:
1. "Walk me through your last deep reading session. What did you do first?"
2. "When do you decide to create a 'synthesis project' vs. just take notes?"
3. "Do you know your topic/question before you start reading, or does it emerge?"
4. "Show me how you currently organize notes across multiple books."

**Design impact**:

| If users... | Then Melvil should... |
|-------------|----------------------|
| Start with topics | Keep current workspace-first flow |
| Start with books | Add capture-first flow: `melvil capture "DDIA" --page 42` without requiring workspace |
| Mix both | Support both entry points equally |

**Decision needed**: Primary workflow order.

---

### Q2: Where does capture actually happen?

**Current assumption**: Users capture passages at their computer, in a terminal.

**Alternative**: Users read on tablets, phones, Kindle, or physical books.

**Research method**: User interviews + diary study (1 week)

**Questions to ask**:
1. "Where do you physically do most of your reading?"
2. "What device are you using when you want to save a passage?"
3. "How do you currently capture quotes or highlights?"
4. "Would you switch to a terminal to capture something? When?"

**Design impact**:

| If users... | Then Melvil should... |
|-------------|----------------------|
| Read at computer | CLI capture is fine |
| Read on Kindle/tablet | Prioritize import from Kindle/Readwise in Phase 2 |
| Read physical books | Support quick mobile capture (web/app) or photo-to-text |
| Mix contexts | Build import first, CLI capture second |

**Decision needed**: Phase 2 priority—semantic search vs. import from external sources.

---

### Q3: Is "synthesis workspace" the right unit?

**Current assumption**: Users work in discrete "synthesis projects" with clear topics and boundaries.

**Alternative**: Users have ongoing, overlapping areas of interest that evolve fluidly.

**Research method**: User interviews + show mockups

**Questions to ask**:
1. "Do your reading projects have clear boundaries, or do they blend together?"
2. "How long does a typical 'project' or 'topic' last for you?"
3. "Do you ever return to old projects, or are they one-time efforts?"
4. "If you captured a passage about 'consistency,' would it belong to one project or many?"

**Design impact**:

| If users... | Then Melvil should... |
|-------------|----------------------|
| Have discrete projects | Keep workspace model |
| Have fluid interests | Passages live in global library; workspaces become "views" or "collections" |
| Return to old work | Add workspace archiving and revival |

**Decision needed**: Data model—do passages belong to workspaces or to a global library?

---

### Q4: Is cross-library search essential for MVP?

**Current assumption**: MVP search is workspace-scoped. Cross-library search is Phase 2.

**Alternative**: Users need to search everything from day one.

**Research method**: User interviews + prototype testing

**Questions to ask**:
1. "If you could only search within one 'project' at a time, would that be useful?"
2. "Describe a time you needed to find something across multiple books."
3. "How often do you know which book a passage is in vs. needing to search everywhere?"

**Prototype test**: Show both:
- Version A: "Search finds passages in your current workspace only"
- Version B: "Search finds passages across everything you've captured"

Ask: "Which would you use? Would you use A at all?"

**Design impact**:

| If users... | Then Melvil should... |
|-------------|----------------------|
| Accept workspace-scoped search | Keep current Phase 1 scope |
| Require cross-library search | Move cross-library search to Phase 1 |

**Decision needed**: Phase 1 scope—add cross-library FTS or defer?

---

## Important Questions (Inform Phase 2)

These questions shape Phase 2 features but don't block MVP.

### Q5: What makes a passage worth capturing?

**Current assumption**: Users capture passages to support a synthesis (evidence for arguments).

**Alternatives**:
- "I want to remember this quote" (personal resonance)
- "This is wrong and I want to note why" (disagreement)
- "This reminds me of something else" (connection)
- "I might need this later" (hoarding)

**Research method**: Diary study + artifact review

**Questions to ask**:
1. "Show me 3-5 things you highlighted recently. Why those?"
2. "What would make you stop reading to capture something?"
3. "What do you do with passages after capturing them?"
4. "How often do you return to old highlights?"

**Design impact**:

| If users... | Then Melvil should... |
|-------------|----------------------|
| Capture for synthesis | Current note types (thesis, argument, term) work |
| Capture for many reasons | Add flexible tagging; make structured types optional |
| Rarely return to captures | Focus on export/integration, not in-app browsing |

**Decision needed**: Note taxonomy—keep structured types or move to free-form tags?

---

### Q6: How important is edition-level provenance?

**Current assumption**: Users need to trace passages to source + page + specific edition.

**Alternative**: Users just need "which book" and "roughly where."

**Research method**: A/B mockup comparison

**Show users**:

**Version A (detailed)**:
```
"The CAP theorem is sometimes presented as..."
— DDIA, p. 336 (2017 O'Reilly edition, PDF hash: abc123)
```

**Version B (simple)**:
```
"The CAP theorem is sometimes presented as..."
— DDIA, Chapter 9
```

**Questions to ask**:
1. "Which version do you prefer? Why?"
2. "When would you actually need the detailed source information?"
3. "Have you ever needed to verify which edition a quote came from?"
4. "Would you notice if the page number was slightly wrong?"

**Design impact**:

| If users... | Then Melvil should... |
|-------------|----------------------|
| Need edition-level precision | Keep full source_snapshot model |
| Just need book + chapter | Simplify to material_id + chapter; drop file hashes |
| Value page numbers but not editions | Keep pages, make edition_info optional |

**Decision needed**: Source snapshot complexity level.

---

### Q7: What existing tools do users have?

**Current assumption**: Users have Zotero and want CLI-based tooling.

**Reality**: Users have diverse toolchains (Obsidian, Notion, Readwise, Kindle, etc.)

**Research method**: Survey (larger sample, 20-50 users)

**Survey questions**:
1. "What tools do you currently use for managing reading/bibliography?" (multi-select)
2. "What tools do you use for taking notes on what you read?" (multi-select)
3. "Where do your highlights/annotations currently live?"
4. "What's the most annoying part of your current reading workflow?"
5. "If you could connect two tools that don't talk to each other, which would they be?"

**Design impact**:

| If users... | Then Melvil should... |
|-------------|----------------------|
| Mostly use Zotero | Current integration is sufficient |
| Use Readwise heavily | Prioritize Readwise import |
| Use Obsidian for notes | Prioritize Obsidian export format |
| Don't use bibliography tools | Support standalone mode without Zotero |

**Decision needed**: Integration priorities for Phase 2.

---

### Q8: Is CLI the right interface?

**Current assumption**: "A CLI forces good design" and is preferred by target users.

**Alternative**: CLI is a barrier; users prefer visual interfaces for synthesis work.

**Research method**: Usability testing

**Test protocol**:
1. Show CLI mockup of capture/synthesize flow
2. Show TUI (terminal UI) mockup with same features
3. Show simple web interface mockup
4. Ask users to complete a task with each

**Questions to ask**:
1. "Which would you be more likely to use regularly?"
2. "What's your comfort level with command-line tools?" (1-5 scale)
3. "Would you use this on a computer where you can't install software?"
4. "For which tasks would you prefer CLI vs. visual interface?"

**Design impact**:

| If users... | Then Melvil should... |
|-------------|----------------------|
| Prefer CLI | Keep CLI-first approach |
| Prefer visual but accept CLI | Build TUI with Rich/Textual |
| Strongly prefer visual | Plan web interface for Phase 2 |
| Need no-install option | Consider web-based version |

**Decision needed**: Interface investment—CLI only, TUI, or web?

---

## Lower Priority Questions (Phase 3+)

These inform long-term direction but don't affect near-term work.

### Q9: Do users want LLM-assisted features?

**Question**: Are concept extraction, term definitions, and summaries valuable enough to justify cost and complexity?

**Research method**: Prototype testing with real LLM outputs

**Test**: Run LLM extraction on 10 passages from a user's actual reading. Show results. Ask:
1. "Are these concepts accurate? Would you edit them?"
2. "Would you use this to find related passages?"
3. "Is this worth $0.01 per passage to you?"

---

### Q10: Is "position mapping" actually possible?

**Question**: Can Melvil meaningfully show "Author A's position on topic X"?

**Research method**: Expert evaluation

**Test**: Extract "positions" from 3 books on same topic using LLM. Have domain expert evaluate:
1. "Is this an accurate summary of the author's view?"
2. "What nuance is missing?"
3. "Would this mislead a novice reader?"

---

### Q11: Would users pay for this?

**Question**: Is there a viable business model, or is this a personal tool?

**Research method**: Willingness-to-pay survey

**Questions**:
1. "Would you pay for a tool like this? How much per month?"
2. "Would you prefer one-time purchase, subscription, or free with paid features?"
3. "What feature would make you pay that you wouldn't use for free?"

---

## Research Tracking

| Question | Status | Method | Target N | Findings |
|----------|--------|--------|----------|----------|
| Q1: Entry point | Not started | Interview | 5-8 | — |
| Q2: Capture context | Not started | Interview + diary | 5-8 | — |
| Q3: Workspace model | Not started | Interview + mockup | 5-8 | — |
| Q4: Search scope | Not started | Interview + prototype | 5-8 | — |
| Q5: Capture triggers | Not started | Diary + artifacts | 5-8 | — |
| Q6: Provenance detail | Not started | A/B mockup | 5-8 | — |
| Q7: Existing tools | Not started | Survey | 20-50 | — |
| Q8: Interface preference | Not started | Usability test | 5-8 | — |
| Q9: LLM features | Not started | Prototype test | 5-8 | — |
| Q10: Position mapping | Not started | Expert review | 3-5 | — |
| Q11: Willingness to pay | Not started | Survey | 20-50 | — |

---

## Interview Script (Template)

For Q1-Q4, use this general structure:

### Introduction (2 min)
"I'm exploring tools for serious readers who want to synthesize across multiple books. I'd like to understand your current reading and note-taking workflow. There are no right answers—I'm trying to learn how you actually work."

### Current Workflow (10 min)
1. "Tell me about something you're currently reading or recently finished."
2. "Walk me through how you decided to read it."
3. "What do you do when you find a passage you want to remember?"
4. "Where do those notes/highlights end up?"
5. "Have you ever tried to synthesize ideas across multiple books? How did that go?"

### Pain Points (5 min)
1. "What's the most frustrating part of your reading/notes workflow?"
2. "Is there something you wish you could do but can't with current tools?"
3. "Have you tried other tools for this? What happened?"

### Concept Testing (10 min)
[Show mockups or describe Melvil concept]
1. "Does this match a problem you have?"
2. "Would you use this? When?"
3. "What would make this not work for you?"

### Wrap-up (3 min)
1. "Anything else about your reading workflow I should know?"
2. "Would you be willing to try a prototype and give feedback?"

---

## Next Steps

1. **Recruit 5-8 target users** for interviews (serious readers with 50+ books in Zotero or equivalent)
2. **Conduct Q1-Q4 interviews** before expanding MVP scope
3. **Create mockups** for A/B testing (Q6, Q8)
4. **Prepare survey** for Q7 (can run in parallel with interviews)
5. **Document findings** in this file as research completes
