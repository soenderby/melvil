# Melvil  
**Design Specification Document**

**Version:** 0.1.0  
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

## 2. System Overview

### 2.1 High-Level Architecture
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

## 3. Requirements

### 3.1 Functional Requirements
- **F1: Source Import & Normalization** — Support EPUB, PDF, text, and web articles.
- **F2: Semantic Processing** — Extract concepts and generate semantic representations.
- **F3: Knowledge Graph Construction** — Map entities and relationships across sources.
- **F4: User Model** — Track goals, preferences, known concepts, and history.
- **F5: Recommendation Engine** — Produce actionable reading plans.
- **F6: Explainability** — Justify all recommendations with transparent metrics.

---

## 4. Data Model

### 4.1 Core Entities

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

## 5. Architectural Components

### 5.1 Ingestion Layer
Responsible for parsing files, extracting table of contents (TOC), and chunking content into manageable units.

### 5.2 Semantic Enrichment Pipeline
- Extract entities and concepts using NLP.
- Normalize concept names.
- Create vector embeddings for semantic search.

### 5.3 Knowledge Graph Module
Stores relationships between entities (concepts, content chunks, works, etc.) and supports expanded retrieval. Knowledge graphs provide **semantic context and relationships** that enrich recommendations beyond flat semantic search.

### 5.4 Retrieval + Recommendation Engine
Combines:

- **Hybrid retrieval** (semantic + keyword + graph traversal)
- **Ranking** based on relevance to user goals, novelty, and effort
- **Plan generation** tailored to the user’s learning mode

---

## 6. Interfaces & APIs

### 6.1 Input Interfaces
- File upload endpoints (multiple formats)
- APIs for importing external sources (e.g., Zotero, Calibre)
- UI for specifying learning goals and preferences

### 6.2 Search & Recommendation API
Typical endpoints:

- `/recommend` — returns a ranked reading plan
- `/concepts` — exposes the user’s concept map
- `/progress` — updates the user’s learning state

### 6.3 Feedback Loop
Users provide feedback on:

- Sections read or skipped
- Concepts learned
- Relevance judgments

Feedback updates the user profile and influences future recommendations.

---

## 7. Recommendation Strategy

### 7.1 Reading Modes
Melvil supports three primary reading modes:

1. **Inspectional** — high-level skims using TOC and summaries
2. **Analytical** — deeper engagement with prerequisite awareness
3. **Syntopical** — context across sources via graph clusters

### 7.2 Scoring Metrics
- **Semantic Fit** — alignment of content with user goals
- **Effort** — estimated reading time and cognitive effort
- **Novelty** — difference from what the user has already seen
- **Centrality** — importance of concepts via graph measures

---

## 8. Build Plan & Milestones

| Milestone | Deliverable |
|-----------|-------------|
| M0 | Project plan & specs |
| M1 | Ingestion + TOC extraction |
| M2 | Semantic pipeline & embedding |
| M3 | Graph storage & retrieval |
| M4 | Reading recommendation engine |
| M5 | UI + feedback integration |

---

## 9. Testing & Evaluation

### 9.1 Unit Tests
- Validate parsers, semantic extraction, and data structures

### 9.2 Integration Tests
- End-to-end tests: file upload → ingestion → recommendation

### 9.3 User Validation
- Validate that Melvil’s recommendations help users achieve learning goals more efficiently

---

## 10. Non-Functional Requirements

| Category        | Requirement |
|-----------------|-------------|
| Performance     | Must handle large corpora with acceptable latency |
| Maintainability | Modular and extensible components |
| Security        | Protect user data and profiles |
| Explainability  | All recommendations are transparent and justifiable |

---

## 11. Glossary
- **Knowledge Graph** — structured network of entities and relationships  
- **ContentChunk** — a text unit used for retrieval and recommendation  
- **Hybrid Retrieval** — a blend of semantic embedding, keyword search, and graph traversal

---

## References
- Best practices for technical design documents
- Knowledge graph + retrieval integration literature

