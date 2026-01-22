# Melvil  
**Design Specification Document**

**Version:** 0.1.1  
**Date:** 2026-01-22

---

## 1. Introduction

### 1.1 Purpose of This Document
This document defines the **architecture, components, data models, interfaces, and functional requirements** for **Melvil** — the *Knowledge-Assisted Reading & Learning System* designed to support directed reading from a large body of material. It serves as a blueprint for engineers, product teams, and stakeholders.

### 1.2 Scope
Melvil will:

- Ingest structured and unstructured reading materials.
- Extract hierarchical structure and semantic information.
- Build a **knowledge graph** of concepts and content.
- Provide goal-driven reading recommendations.
- Adapt recommendations based on user knowledge state and preferences.

Melvil guides *what* to read and *why* — not *do the learning for the user*.

---

## 2. Problem Statement

In the modern information landscape, individuals are exposed to a **vast and continuously expanding volume of content** from books, articles, reports, web pages, and other sources. 

Information overload makes it challenging for readers to even identify what is worth reading. Melvil confronts this enduring challenge with modern tools, helping users prioritize reading efforts and make informed decisions about *what sources are most releveant* and *what parts of a text matter most* for their specific goals.

Classic reading pedagogy — such as that articulated in *How to Read a Book* — emphasizes that effective reading is **purposeful and goal-oriented**, advocating for different modes of reading depending on the task (e.g., inspectional, analytical, syntopical). Melvil aims to provide technological support to operationalize such strategies over large and heterogeneous reading lists.

Thus, the core problem Melvil aims to address is:

> **Readers have access to more potential material than they can realistically read, and lack tools to systematically assess, prioritize, and navigate content based on their individual learning goals, existing knowledge, and time constraints.**

Melvil’s goal is to mitigate the effects of information overload by providing structured support for reading prioritization, context-aware recommendations, and directed learning planning.

---

## 3. System Overview

### 3.1 High-Level Architecture
Melvil consists of three primary subsystems:

1. **Ingestion & Semantic Enrichment**
   - Document parsing, structure extraction, chunking.
   - Embedding and concept extraction.

2. **Knowledge Representation**
   - Knowledge graph of concepts, documents, and relationships.

3. **Reading Router & Recommendation**
   - Hybrid semantic + graph retrieval.
   - Ranking and planning tailored reading routes.

---

## 4. Requirements

### 4.1 Functional Requirements
- **F1: Source Import & Normalization** — Support EPUB, PDF, text, and web articles.
- **F2: Semantic Processing** — Extract concepts and generate semantic representations.
- **F3: Knowledge Graph Construction** — Map entities and relationships across sources.
- **F4: User Model** — Track goals, preferences, known concepts, and history.
- **F5: Recommendation Engine** — Produce actionable reading plans.
- **F6: Explainability** — Justify all recommendations with transparent metrics.

---

## 5. Data Model

### 5.1 Core Entities

#### a. Document Structure
| Entity           | Description |
|------------------|-------------|
| **Work**         | Abstract representation of a book/article. |
| **Edition**      | File/format (EPUB, PDF, etc.). |
| **TocNode**      | Section/chapter hierarchy within a work. |
| **ContentChunk** | Text chunk tied to a section with summary + concepts. |

#### b. Knowledge Graph Ontology
| Entity           | Description |
|------------------|-------------|
| **Concept**      | Canonical idea or term extracted from text. |
| **Relation**     | Semantic or structural linkage between entities. |
| **UserProfile**  | User’s known/unknown concepts + goals. |

---

## 6. Architectural Components

### 6.1 Ingestion Layer
Responsible for parsing files, extracting table of contents (TOC), and chunking content into manageable units.

### 6.2 Semantic Enrichment Pipeline
- Extract entities and concepts using NLP.
- Normalize concept names.
- Create vector embeddings for semantic search.

### 6.3 Knowledge Graph Module
Stores relationships between entities (concepts, content chunks, works, etc.) and supports expanded retrieval. Knowledge graphs provide **semantic context and relationships** that enrich recommendations beyond flat semantic search.

### 6.4 Retrieval + Recommendation Engine
Combines:

- **Hybrid retrieval** (semantic + keyword + graph traversal)
- **Ranking** based on relevance to user goals, novelty, and effort
- **Plan generation** tailored to the user’s learning mode

---

## 7. Interfaces & APIs

### 7.1 Input Interfaces
- File upload endpoints (multiple formats)
- APIs for importing external sources (e.g., Zotero, Calibre)
- UI for specifying learning goals and preferences

### 7.2 Search & Recommendation API
Typical endpoints:

- `/recommend` — returns a ranked reading plan
- `/concepts` — exposes the user’s concept map
- `/progress` — updates the user’s learning state

### 7.3 Feedback Loop
Users provide feedback on:

- Sections read or skipped
- Concepts learned
- Relevance judgments

Feedback updates the user profile and influences future recommendations.

---

## 8. Recommendation Strategy

### 8.1 Reading Modes
Melvil supports three primary reading modes:

1. **Inspectional** — high-level skims using TOC and summaries
2. **Analytical** — deeper engagement with prerequisite awareness
3. **Syntopical** — context across sources via graph clusters

### 8.2 Scoring Metrics
- **Semantic Fit** — alignment of content with user goals
- **Effort** — estimated reading time and cognitive effort
- **Novelty** — difference from what the user has already seen
- **Centrality** — importance of concepts via graph measures

---

## 9. Build Plan & Milestones

| Milestone | Deliverable |
|-----------|-------------|
| M0 | Project plan & specs |
| M1 | Ingestion + TOC extraction |
| M2 | Semantic pipeline & embedding |
| M3 | Graph storage & retrieval |
| M4 | Reading recommendation engine |
| M5 | UI + feedback integration |

---

## 10. Testing & Evaluation

### 10.1 Unit Tests
- Validate parsers, semantic extraction, and data structures

### 10.2 Integration Tests
- End-to-end tests: file upload → ingestion → recommendation

### 10.3 User Validation
- Validate that Melvil’s recommendations help users achieve learning goals more efficiently

---

## 11. Non-Functional Requirements

| Category        | Requirement |
|-----------------|-------------|
| Performance     | Must handle large corpora with acceptable latency |
| Maintainability | Modular and extensible components |
| Security        | Protect user data and profiles |
| Explainability  | All recommendations are transparent and justifiable |

---

## 12. Glossary
- **Knowledge Graph** — structured network of entities and relationships  
- **ContentChunk** — a text unit used for retrieval and recommendation  
- **Hybrid Retrieval** — a blend of semantic embedding, keyword search, and graph traversal

---

## References
- Research on information overload, its causes and effects. :contentReference[oaicite:3]{index=3}  
- Studies on coping strategies and information management. :contentReference[oaicite:4]{index=4}  
- Reading methodology guided by Adler and Van Doren’s *How to Read a Book*. :contentReference[oaicite:5]{index=5}
