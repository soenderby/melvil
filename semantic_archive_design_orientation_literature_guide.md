# Semantic Archive: Design Orientation & Literature Guide

## Purpose of this Document
This document summarizes the conceptual foundations, design goals, user needs, and key literature relevant to building an **ideal semantic archive**. It is intended to:
- Inform high-level and detailed design decisions
- Provide shared conceptual grounding for team members
- Serve as an orientation guide to the relevant bodies of literature

The focus is **semantic information**: meaning-rich material whose relevance depends on context, perspective, time, and purpose.

---

## Core Problem Statement

The challenge is not storing information, but **preserving and reactivating meaning**.

Key constraints:
- Relevance cannot be stored directly; it only emerges in relation to a question.
- Meaning is contextual, social, embodied, and time-dependent.
- No single representational scheme is sufficient.

Therefore, a semantic archive must support:
- Multiple representations of the same material
- Question-driven retrieval
- Transparency, provenance, and temporal awareness

---

## Guiding Design Principles

1. **Capture first, structure progressively**  
   Avoid premature formalization. Preserve raw sources and allow structure to evolve.

2. **Pluralism of representations**  
   Combine text, metadata, embeddings, graphs, and narratives. No layer is authoritative alone.

3. **Provenance and inspectability**  
   All derived meaning must trace back to sources, authorship, time, and confidence.

4. **Retrieval as a process, not a query**  
   Favor iterative sensemaking over one-shot answers.

5. **Support uncertainty and disagreement**  
   Preserve competing interpretations rather than forcing convergence.

---

## Conceptual Architecture (Summary)

### Layered Semantic Stack

- **Layer 0: Immutable Sources**  
  Original documents, notes, media, code; versioned and preserved.

- **Layer 1: Metadata & Facets**  
  Human-legible descriptors (author, date, domain, project, permissions).

- **Layer 2: Information Retrieval Index**  
  Full-text and fielded search for precision and auditability.

- **Layer 3: Semantic Embeddings**  
  Vector representations enabling fuzzy recall, analogy, and discovery.

- **Layer 4: Structured Meaning**  
  Knowledge graphs (entities + relations) and optional claim/argument structures.

Meaning emerges through **interaction between layers**, not within any single one.

---

## Primary User Purposes

Users engage with semantic archives to reduce cognitive friction under uncertainty. Core purposes include:

1. **Orientation & Sensemaking**  
   Understanding a domain, project, or situation.

2. **Recall & Verification**  
   Finding authoritative sources and exact wording.

3. **Decision Support**  
   Accessing precedents, arguments, evidence, and tradeoffs.

4. **Discovery & Insight**  
   Revealing patterns, connections, and reframings.

5. **Memory Externalization**  
   Offloading cognitive load while preserving future retrievability.

---

## Modes of Interaction

An effective system supports multiple cognitive modes:

- **Asking**: natural language questions and follow-ups
- **Browsing**: maps, timelines, clusters, and facets
- **Inspecting**: close reading of original sources
- **Assembling**: synthesizing excerpts into arguments or narratives
- **Contributing**: curation, annotation, and refinement by users

No single mode is sufficient; value arises from smooth transitions between them.

---

## Value Users Seek

Often implicitly, users seek:

- **Cognitive leverage**: better reasoning with less effort
- **Trust and confidence**: grounded answers with clear provenance
- **Speed without recklessness**: fast orientation with paths to depth
- **Sense of control**: understanding why information appears
- **Learning over time**: improved mental models and judgment

Systems fail when they optimize for confidence or speed at the expense of transparency.

---

## Best Practices for Use

- Treat the system as a **thinking partner**, not an oracle
- Start broad, then progressively narrow
- Always return to sources for high-stakes decisions
- Use the archive to externalize uncertainty and open questions
- Leverage time: compare past and present interpretations

The system should help users ask **better questions**, not just retrieve answers.

---

## Literature Orientation (Conceptual Map)

### 1. Philosophical & Cognitive Foundations (Highest Priority)
Focus: what meaning is, how it arises, and why it shifts
- Theories of meaning and use
- Embodied and prototype-based cognition
- Inferential and social accounts of semantics
- Paradigm shifts and conceptual change

Key figures: Wittgenstein, Lakoff, Brandom, Sellars, Kuhn, Dreyfus, Rosch

---

### 2. Knowledge Management & Organizational Memory
Focus: how meaning survives (or fails to) in institutions
- Tacit vs explicit knowledge
- Knowledge lifecycle and governance
- Organizational forgetting and drift

Key figures: Davenport, Prusak, Nonaka, Ackerman, Wiig

---

### 3. Information Retrieval & Relevance Theory
Focus: operationalizing relevance under uncertainty
- Inverted indexes and ranking
- Probabilistic relevance
- User-centered relevance models

Key figures: Manning, Robertson, Spärck Jones, Saracevic, Belkin

---

### 4. Semantic Search & Vector Representations
Focus: similarity-based retrieval and discovery
- Distributional semantics
- Neural retrieval models
- Vector databases and similarity search

Key areas: word embeddings, dense passage retrieval, neural IR benchmarks

---

## Key Design Insight

> The primary value of a semantic archive is not answers, but **improved sensemaking**.

A successful system:
- Sharpens user intent
- Makes assumptions and disagreements visible
- Preserves context across time
- Enables meaning to be recomputed as questions change

---

## Intended Use of This Document

This document should be used to:
- Align design discussions around shared principles
- Justify architectural tradeoffs
- Onboard new contributors to the conceptual landscape
- Anchor technical decisions in epistemic and human considerations

It is a **living orientation**, not a final specification.