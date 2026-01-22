# Learning-Directed Knowledge Management System
## Executive Summary & Quick Start Guide

### The Core Idea

You have more books to read than time allows. This system helps you **decide what to read and what to skip**—inspired by Adler & Van Doren's "How to Read a Book" principle that not every book requires cover-to-cover reading.

---

## What This System Does

| Problem | System Solution |
|---------|-----------------|
| "Is this book worth my time?" | **Automated inspectional reading**: summaries, concept extraction, relevance scoring |
| "I want to learn X, where do I start?" | **Learning path generation**: prerequisite mapping, material recommendations |
| "I found an interesting book but don't have time now" | **Interest queue**: stores context, surfaces when relevant |
| "Should I read the whole book or specific chapters?" | **Chapter-level relevance**: identifies which sections matter for your goal |
| "What do I already know vs. need to learn?" | **Knowledge state tracking**: maps your expertise against target concepts |

---

## Key Architectural Decisions

### 1. Graph Database (Neo4j)
**Why**: Your data is fundamentally relational—concepts have prerequisites, materials cover concepts, users have goals targeting concepts. A graph database makes these queries natural and fast.

```cypher
// Example: Find all materials covering a concept and its prerequisites
MATCH path = (prereq:Concept)-[:PREREQUISITE_OF*0..]->(target:Concept {name: "Machine Learning"})
MATCH (m:Material)-[:COVERS]->(prereq)
RETURN m, prereq
```

### 2. LLM-Powered Summarization
**Why**: Generating multi-level summaries (quick summary, detailed summary, main thesis) enables different use cases—quick triage vs. deep evaluation.

**Strategy**: Hierarchical map-reduce for long documents (split → summarize chunks → combine summaries).

### 3. Concept-Centric Rather Than Book-Centric
**Why**: You're not trying to "read more books"—you're trying to learn concepts. Materials are just vehicles. This reframe enables:
- Cross-book concept mapping
- Prerequisite identification
- Depth-aware recommendations

### 4. Three Types of Knowledge State
- **Self-reported**: User says "I understand calculus"
- **Inferred from reading**: Completed 80% of a calculus book → probably knows calculus
- **Propagated**: Knows ML → probably knows its prerequisites

---

## Minimum Viable System (Phase 1)

Start here to get value quickly:

```
┌─────────────────────────────────────────┐
│          Phase 1: Add & Query           │
├─────────────────────────────────────────┤
│                                         │
│  1. Add Book (ISBN or title)            │
│     → Fetch metadata (Open Library)     │
│     → Generate summary (Claude)         │
│     → Extract concepts                  │
│     → Store in Neo4j                    │
│                                         │
│  2. Query Relevance                     │
│     "Is book X relevant to topic Y?"    │
│     → Score concept overlap             │
│     → Show matching chapters            │
│                                         │
└─────────────────────────────────────────┘
```

### Minimal Code to Get Started

```python
# 1. Set up Neo4j (docker-compose.yml)
# services:
#   neo4j:
#     image: neo4j:5
#     ports: ["7474:7474", "7687:7687"]
#     environment:
#       NEO4J_AUTH: neo4j/password

# 2. Core dependencies
# pip install neo4j anthropic httpx

# 3. Simplest possible ingestion
import httpx
from anthropic import Anthropic
from neo4j import GraphDatabase

async def add_book(isbn: str):
    # Fetch from Open Library
    resp = await httpx.AsyncClient().get(
        f"https://openlibrary.org/api/books",
        params={"bibkeys": f"ISBN:{isbn}", "jscmd": "details", "format": "json"}
    )
    data = resp.json()[f"ISBN:{isbn}"]["details"]
    
    # Summarize with Claude
    client = Anthropic()
    summary = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": f"Summarize in 2-3 sentences: {data['title']} - {data.get('description', '')}"}]
    ).content[0].text
    
    # Store in Neo4j
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    with driver.session() as session:
        session.run("""
            CREATE (m:Material {
                title: $title,
                isbn: $isbn,
                summary: $summary
            })
        """, title=data['title'], isbn=isbn, summary=summary)
    
    print(f"Added: {data['title']}")
```

---

## Data Sources

| Source | What It Provides | Quality |
|--------|------------------|---------|
| **Open Library** | Title, authors, TOC, page count | ⭐⭐⭐ (TOC is gold) |
| **Google Books** | Description, categories | ⭐⭐⭐ |
| **ISBNdb** | Publication details | ⭐⭐ |
| **Wikidata** | Concept relationships | ⭐⭐⭐ (for enrichment) |

**Key insight**: Open Library often has table of contents data—this is extremely valuable for chapter-level analysis.

---

## Critical Concepts

### The Adler Framework (Your Compass)

| Level | System Equivalent |
|-------|-------------------|
| **Inspectional Reading** | Summaries + TOC analysis + concept extraction |
| **Analytical Reading** | Deep material processing (when needed) |
| **Syntopical Reading** | Cross-material concept graph queries |

### The Learning Path

```
[User Goal] → [Target Concepts] → [Prerequisite Graph] → [Recommended Materials]
     ↑                                                            │
     └─────────────── [Knowledge State Updates] ←─────────────────┘
```

### Relevance Scoring Formula

```
Relevance = 
    0.35 × (concepts covered ∩ concepts needed) / concepts needed
  + 0.25 × depth match (survey vs. deep dive)
  + 0.20 × prerequisites satisfied
  + 0.20 × semantic similarity of summary to goal
```

---

## What NOT to Build

1. **Reading the books for you** — The system directs attention, not replaces learning
2. **Complete metadata for every book** — Start with what APIs provide, enhance lazily
3. **Perfect prerequisite graphs** — Good enough beats perfect; iterate based on usage
4. **Complex UI initially** — CLI is fine for v1; proves the concept

---

## Next Steps

1. **Read the full design doc** for detailed architecture
2. **Set up Neo4j locally** (Docker recommended)
3. **Implement basic ingestion** (Open Library + Claude summary)
4. **Add 10-20 books** in a domain you care about
5. **Query for relevance** and iterate on scoring

---

## Questions This System Answers

✓ "I want to learn distributed systems—what should I read first?"  
✓ "Is 'Designing Data-Intensive Applications' relevant to my ML goal?"  
✓ "Which chapters of this 500-page book actually matter for my purpose?"  
✓ "I heard about this book on a podcast—should I add it to my list?"  
✓ "What prerequisites am I missing for this advanced material?"  
✓ "Show me everything I've collected about topic X"  

---

*See the full design document for complete architecture, code samples, and implementation phases.*
