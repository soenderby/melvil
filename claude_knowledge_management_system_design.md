# Learning-Directed Knowledge Management System

## Design Document

**Version:** 1.0  
**Date:** January 22, 2026  
**Conceptual Foundation:** Adler & Van Doren's "How to Read a Book"

---

## 1. Executive Summary

This document outlines the architecture for a **Learning-Directed Knowledge Management System** designed to help readers determine *which parts* of a large body of material they should read, based on their learning goals and current knowledge state.

The system is inspired by Mortimer Adler and Charles Van Doren's framework of reading levels—particularly **inspectional reading** (determining what a book is about and whether it deserves deeper engagement) and **syntopical reading** (researching a topic across multiple sources). Rather than doing the work of learning, this system directs the user's efforts most effectively.

### Core Problems Addressed

1. **The Discovery Problem**: Finding the *right* materials among an overwhelming sea of options
2. **The Relevance Problem**: Determining if a book (or part of it) is relevant to current learning goals
3. **The Depth Problem**: Knowing when to go broad vs. deep on a subject
4. **The Time Problem**: Materials that seem interesting but for which there's no immediate time
5. **The Knowledge State Problem**: Tracking what users know vs. what they're trying to learn

---

## 2. System Philosophy

### 2.1 Adler's Four Levels of Reading (Mapped to System Features)

| Level | Description | System Support |
|-------|-------------|----------------|
| **Elementary** | Basic literacy | Not addressed (assumed) |
| **Inspectional** | Systematic skimming to understand structure and purpose | **Automated summaries, TOC analysis, concept extraction** |
| **Analytical** | Deep reading for understanding | **Learning path generation, prerequisite mapping** |
| **Syntopical** | Reading multiple books on one subject | **Cross-book concept graphs, topic synthesis** |

### 2.2 Design Principles

1. **The system does not replace reading**—it directs attention to what's worth reading
2. **Books have specific purposes**—not all require cover-to-cover reading
3. **Learning is personal**—the system adapts to individual knowledge states and goals
4. **Relevance is contextual**—the same book may be essential or skippable depending on the goal
5. **Time is finite**—the system optimizes for impact, not completeness

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Learning   │  │  Material   │  │   Reading   │  │   Knowledge     │ │
│  │   Goals     │  │   Browser   │  │    Queue    │  │    Explorer     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────┴────────────────────────────────────┐
│                          APPLICATION SERVICES                            │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐  │
│  │  Relevance Engine   │  │  Path Generator     │  │  Summarization  │  │
│  │  (Goal ↔ Material)  │  │  (Learning Paths)   │  │     Service     │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘  │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐  │
│  │   User Knowledge    │  │   Material Ingestion │  │  Recommendation │  │
│  │   State Tracker     │  │      Pipeline       │  │      Engine     │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────┘  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────┴────────────────────────────────────┐
│                          KNOWLEDGE LAYER                                 │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     KNOWLEDGE GRAPH (Neo4j)                        │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐        │  │
│  │  │  Concepts   │◄──►│  Materials  │◄──►│  User Learning  │        │  │
│  │  │   (Topics)  │    │   (Books)   │    │     State       │        │  │
│  │  └─────────────┘    └─────────────┘    └─────────────────┘        │  │
│  │         │                  │                    │                  │  │
│  │    PREREQUISITE       COVERS            MASTERY/GOALS              │  │
│  │    RELATED_TO         AUTHORED_BY       INTERESTED_IN              │  │
│  │    PART_OF            HAS_CHAPTER       FAMILIAR_WITH              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─────────────────────────┐  ┌────────────────────────────────────┐    │
│  │  Vector Store (Pinecone │  │     External APIs                  │    │
│  │  or Chroma)             │  │  - Open Library (metadata, TOC)    │    │
│  │  - Concept embeddings   │  │  - Google Books (descriptions)     │    │
│  │  - Summary embeddings   │  │  - ISBNDB (additional metadata)    │    │
│  │  - Chapter embeddings   │  │  - DBpedia/Wikidata (concept KG)   │    │
│  └─────────────────────────┘  └────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Models

### 4.1 Knowledge Graph Schema (Neo4j)

```cypher
// === CORE NODE TYPES ===

// Concepts: Topics and ideas that can be learned
(:Concept {
    id: string,
    name: string,
    description: string,
    embedding: [float],           // For semantic similarity
    abstraction_level: int,       // 1 = fundamental, 5 = specialized
    domain: string                // e.g., "computer_science", "philosophy"
})

// Materials: Books, articles, papers
(:Material {
    id: string,
    type: "book" | "article" | "paper" | "course",
    title: string,
    authors: [string],
    isbn: string,
    publication_year: int,
    description: string,
    page_count: int,
    difficulty_level: int,        // 1-5 scale
    estimated_read_hours: float,
    summary_short: string,        // 2-3 sentences
    summary_detailed: string,     // 1-2 paragraphs
    main_thesis: string,          // Author's central argument
    embedding: [float]
})

// Chapters/Sections: Structural divisions of materials
(:Chapter {
    id: string,
    title: string,
    chapter_number: int,
    page_start: int,
    page_end: int,
    summary: string,
    key_concepts: [string],
    embedding: [float]
})

// User: The learner
(:User {
    id: string,
    created_at: datetime
})

// LearningGoal: What the user wants to learn
(:LearningGoal {
    id: string,
    title: string,
    description: string,
    depth: "survey" | "working" | "expert",  // How deep to go
    priority: int,
    status: "active" | "paused" | "completed",
    created_at: datetime,
    target_date: datetime,
    embedding: [float]
})

// === RELATIONSHIP TYPES ===

// Concept relationships
(:Concept)-[:PREREQUISITE_OF {strength: float}]->(:Concept)
(:Concept)-[:RELATED_TO {strength: float, type: string}]->(:Concept)
(:Concept)-[:PART_OF]->(:Concept)  // Hierarchical

// Material-Concept relationships  
(:Material)-[:COVERS {
    depth: "introduces" | "explains" | "deep_dive",
    quality: float,                // How well it covers
    chapter_refs: [string]         // Which chapters cover this
}]->(:Concept)

(:Material)-[:REQUIRES_KNOWLEDGE_OF {strength: float}]->(:Concept)

// Material structure
(:Material)-[:HAS_CHAPTER {order: int}]->(:Chapter)
(:Chapter)-[:COVERS {depth: string}]->(:Concept)

// User relationships
(:User)-[:HAS_GOAL]->(:LearningGoal)
(:LearningGoal)-[:TARGETS]->(:Concept)

(:User)-[:FAMILIAR_WITH {
    level: float,                  // 0.0 = unknown, 1.0 = mastered
    confidence: float,             // Certainty of assessment
    last_assessed: datetime,
    source: "self_reported" | "inferred" | "tested"
}]->(:Concept)

(:User)-[:HAS_READ {
    completion: float,             // 0.0 to 1.0
    rating: int,
    date_started: datetime,
    date_finished: datetime
}]->(:Material)

(:User)-[:READING_QUEUE {
    priority: int,
    added_at: datetime,
    reason: string                 // Why added to queue
}]->(:Material)

(:User)-[:INTERESTED_IN {
    added_at: datetime,
    context: string                // What sparked interest
}]->(:Material)
```

### 4.2 Python Data Classes

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid

class DepthLevel(Enum):
    SURVEY = "survey"           # Broad overview, many topics
    WORKING = "working"         # Practical understanding
    EXPERT = "expert"           # Deep mastery

class MaterialType(Enum):
    BOOK = "book"
    ARTICLE = "article"
    PAPER = "paper"
    COURSE = "course"

class CoverageDepth(Enum):
    INTRODUCES = "introduces"   # Brief mention
    EXPLAINS = "explains"       # Full explanation
    DEEP_DIVE = "deep_dive"     # Comprehensive treatment

@dataclass
class Concept:
    """A learnable topic or idea."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    abstraction_level: int = 1  # 1=fundamental, 5=specialized
    domain: str = ""
    embedding: Optional[List[float]] = None
    
    # Populated from graph queries
    prerequisites: List['Concept'] = field(default_factory=list)
    related_concepts: List['Concept'] = field(default_factory=list)

@dataclass
class Chapter:
    """A structural division of a material."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    chapter_number: int = 0
    page_start: int = 0
    page_end: int = 0
    summary: str = ""
    key_concepts: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

@dataclass
class Material:
    """A book, article, or other learning resource."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    material_type: MaterialType = MaterialType.BOOK
    title: str = ""
    authors: List[str] = field(default_factory=list)
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    description: str = ""
    page_count: Optional[int] = None
    difficulty_level: int = 3
    estimated_read_hours: Optional[float] = None
    
    # Summaries at different levels
    summary_short: str = ""        # 2-3 sentences
    summary_detailed: str = ""     # 1-2 paragraphs
    main_thesis: str = ""          # Central argument
    
    # Structure
    chapters: List[Chapter] = field(default_factory=list)
    table_of_contents_raw: Optional[str] = None
    
    # Concept coverage
    concepts_covered: List[dict] = field(default_factory=list)
    prerequisites: List[Concept] = field(default_factory=list)
    
    embedding: Optional[List[float]] = None

@dataclass
class LearningGoal:
    """What the user wants to learn."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    depth: DepthLevel = DepthLevel.WORKING
    priority: int = 1
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    target_date: Optional[datetime] = None
    
    # Target concepts
    target_concepts: List[Concept] = field(default_factory=list)
    embedding: Optional[List[float]] = None

@dataclass
class UserKnowledgeState:
    """Tracks what a user knows about concepts."""
    user_id: str
    concept_id: str
    level: float = 0.0           # 0.0 = unknown, 1.0 = mastered
    confidence: float = 0.5      # How sure we are of this assessment
    last_assessed: datetime = field(default_factory=datetime.now)
    source: str = "self_reported"  # How we determined this

@dataclass
class ReadingRecommendation:
    """A recommendation for what to read."""
    material: Material
    relevance_score: float       # How relevant to current goals
    urgency_score: float         # How soon to read
    suggested_chapters: List[Chapter] = field(default_factory=list)
    reason: str = ""             # Why this is recommended
    estimated_time: float = 0    # Hours to read suggested portions
    prerequisites_met: bool = True
    missing_prerequisites: List[Concept] = field(default_factory=list)
```

---

## 5. Core Services

### 5.1 Material Ingestion Pipeline

This pipeline processes new materials and extracts structured information.

```python
from abc import ABC, abstractmethod
from typing import Optional
import httpx

class MaterialIngestionPipeline:
    """
    Processes new materials to extract:
    1. Metadata (from APIs)
    2. Table of Contents structure
    3. Concept coverage
    4. Multi-level summaries
    5. Embeddings
    """
    
    def __init__(
        self,
        metadata_fetchers: list['MetadataFetcher'],
        summarizer: 'SummarizationService',
        concept_extractor: 'ConceptExtractor',
        embedding_service: 'EmbeddingService',
        graph_store: 'Neo4jStore'
    ):
        self.metadata_fetchers = metadata_fetchers
        self.summarizer = summarizer
        self.concept_extractor = concept_extractor
        self.embedding_service = embedding_service
        self.graph_store = graph_store
    
    async def ingest_material(
        self, 
        identifier: str,  # ISBN, URL, or title
        material_type: MaterialType = MaterialType.BOOK,
        full_text: Optional[str] = None  # If available
    ) -> Material:
        """Full ingestion pipeline for a new material."""
        
        # Step 1: Fetch metadata from multiple sources
        material = Material(material_type=material_type)
        for fetcher in self.metadata_fetchers:
            metadata = await fetcher.fetch(identifier)
            if metadata:
                material = self._merge_metadata(material, metadata)
        
        # Step 2: Parse and structure table of contents
        if material.table_of_contents_raw:
            material.chapters = self._parse_toc(material.table_of_contents_raw)
        
        # Step 3: Generate summaries
        if full_text:
            summaries = await self.summarizer.generate_hierarchical_summary(
                full_text,
                material.title
            )
            material.summary_short = summaries['short']
            material.summary_detailed = summaries['detailed']
            material.main_thesis = summaries['thesis']
            
            # Summarize each chapter if we have chapter boundaries
            for chapter in material.chapters:
                chapter_text = self._extract_chapter_text(full_text, chapter)
                if chapter_text:
                    chapter.summary = await self.summarizer.summarize_section(
                        chapter_text, 
                        chapter.title
                    )
        else:
            # Generate summary from description/metadata only
            material.summary_short = await self.summarizer.summarize_from_metadata(
                material.title,
                material.description,
                material.authors
            )
        
        # Step 4: Extract concepts
        concepts = await self.concept_extractor.extract_concepts(
            material.summary_detailed or material.description,
            material.chapters
        )
        material.concepts_covered = concepts
        
        # Step 5: Generate embeddings
        material.embedding = await self.embedding_service.embed(
            f"{material.title}. {material.summary_short}"
        )
        for chapter in material.chapters:
            chapter.embedding = await self.embedding_service.embed(
                f"{chapter.title}. {chapter.summary}"
            )
        
        # Step 6: Store in graph
        await self.graph_store.save_material(material)
        
        return material


class MetadataFetcher(ABC):
    """Abstract base for metadata sources."""
    
    @abstractmethod
    async def fetch(self, identifier: str) -> Optional[dict]:
        pass


class OpenLibraryFetcher(MetadataFetcher):
    """Fetch from Open Library API - great for TOC."""
    
    BASE_URL = "https://openlibrary.org"
    
    async def fetch(self, identifier: str) -> Optional[dict]:
        # Determine identifier type
        if identifier.replace("-", "").isdigit():
            bibkey = f"ISBN:{identifier.replace('-', '')}"
        else:
            # Search by title
            return await self._search_by_title(identifier)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/api/books",
                params={
                    "bibkeys": bibkey,
                    "jscmd": "details",
                    "format": "json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if bibkey in data:
                    return self._parse_response(data[bibkey])
        
        return None
    
    def _parse_response(self, data: dict) -> dict:
        details = data.get('details', {})
        return {
            'title': details.get('title'),
            'authors': [a.get('name') for a in details.get('authors', [])],
            'isbn': details.get('isbn_13', [None])[0] or details.get('isbn_10', [None])[0],
            'page_count': details.get('number_of_pages'),
            'table_of_contents_raw': self._format_toc(details.get('table_of_contents', [])),
            'description': details.get('description', {}).get('value', '') 
                          if isinstance(details.get('description'), dict)
                          else details.get('description', '')
        }
    
    def _format_toc(self, toc_items: list) -> str:
        """Convert TOC items to structured string."""
        lines = []
        for item in toc_items:
            indent = "  " * item.get('level', 0)
            lines.append(f"{indent}{item.get('title', '')}")
        return "\n".join(lines)


class GoogleBooksFetcher(MetadataFetcher):
    """Fetch from Google Books API - good for descriptions."""
    
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def fetch(self, identifier: str) -> Optional[dict]:
        async with httpx.AsyncClient() as client:
            # Try ISBN first
            if identifier.replace("-", "").isdigit():
                query = f"isbn:{identifier.replace('-', '')}"
            else:
                query = identifier
            
            response = await client.get(
                self.BASE_URL,
                params={"q": query, "key": self.api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('totalItems', 0) > 0:
                    return self._parse_volume(data['items'][0])
        
        return None
    
    def _parse_volume(self, item: dict) -> dict:
        info = item.get('volumeInfo', {})
        return {
            'title': info.get('title'),
            'authors': info.get('authors', []),
            'description': info.get('description'),
            'page_count': info.get('pageCount'),
            'publication_year': int(info.get('publishedDate', '0')[:4]) or None,
            'categories': info.get('categories', [])
        }
```

### 5.2 Summarization Service

Uses LLMs with hierarchical/map-reduce strategies for long documents.

```python
from anthropic import Anthropic
from typing import List, Tuple

class SummarizationService:
    """
    Generate multi-level summaries using LLMs.
    Follows Adler's inspectional reading principles:
    - What is the book about as a whole?
    - What is being said in detail, and how?
    - What is the author's main argument/thesis?
    """
    
    def __init__(self, anthropic_client: Anthropic, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic_client
        self.model = model
        self.max_chunk_tokens = 100000  # For hierarchical processing
    
    async def generate_hierarchical_summary(
        self,
        full_text: str,
        title: str
    ) -> dict:
        """
        Generate summaries at multiple levels:
        - Short: 2-3 sentences (elevator pitch)
        - Detailed: 1-2 paragraphs (chapter-level overview)
        - Thesis: The author's central argument
        """
        
        # For very long texts, use map-reduce
        if len(full_text.split()) > 50000:
            return await self._hierarchical_summarize(full_text, title)
        
        # Direct summarization for shorter texts
        prompt = f"""Analyze this book titled "{title}" and provide:

1. SHORT_SUMMARY: A 2-3 sentence summary suitable for quickly understanding what the book is about. This helps readers decide if the book is relevant to their interests.

2. DETAILED_SUMMARY: A 1-2 paragraph summary that covers the main topics, structure, and key insights. This helps readers understand what they would learn from the book.

3. MAIN_THESIS: In 1-2 sentences, what is the author's central argument or main point? What does the author want readers to believe or understand after reading?

4. KEY_CONCEPTS: List 5-10 main concepts or topics covered (just the concept names, comma-separated).

Text:
{full_text[:200000]}  # Truncate if needed

Respond in this exact format:
SHORT_SUMMARY: [your summary]
DETAILED_SUMMARY: [your summary]
MAIN_THESIS: [the thesis]
KEY_CONCEPTS: [concept1, concept2, ...]"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_summary_response(response.content[0].text)
    
    async def _hierarchical_summarize(
        self, 
        full_text: str, 
        title: str
    ) -> dict:
        """Map-reduce for very long documents."""
        
        # Split into semantic chunks (by chapter if possible)
        chunks = self._split_into_chunks(full_text)
        
        # Map: Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            summary = await self._summarize_chunk(chunk, i, len(chunks))
            chunk_summaries.append(summary)
        
        # Reduce: Combine chunk summaries into final summary
        combined = "\n\n---\n\n".join(chunk_summaries)
        
        prompt = f"""You have section-by-section summaries of the book "{title}".
        
Synthesize these into:
1. SHORT_SUMMARY: 2-3 sentences capturing the essence
2. DETAILED_SUMMARY: 1-2 paragraphs covering main topics and insights
3. MAIN_THESIS: The author's central argument in 1-2 sentences
4. KEY_CONCEPTS: 5-10 main concepts (comma-separated)

Section summaries:
{combined}

Respond in this exact format:
SHORT_SUMMARY: [your summary]
DETAILED_SUMMARY: [your summary]
MAIN_THESIS: [the thesis]
KEY_CONCEPTS: [concept1, concept2, ...]"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return self._parse_summary_response(response.content[0].text)
    
    async def summarize_section(
        self, 
        section_text: str, 
        section_title: str
    ) -> str:
        """Summarize a single chapter or section."""
        
        prompt = f"""Summarize this chapter/section titled "{section_title}" in 2-3 sentences.
Focus on:
- What is the main point of this section?
- What will readers learn?

Text:
{section_text[:50000]}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text.strip()
    
    async def summarize_from_metadata(
        self,
        title: str,
        description: str,
        authors: List[str]
    ) -> str:
        """Generate summary when only metadata is available."""
        
        prompt = f"""Based on this book information, write a 2-3 sentence summary 
that would help a reader understand what this book is about and whether 
it might be relevant to them.

Title: {title}
Authors: {', '.join(authors)}
Description: {description}

Summary:"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text.strip()
    
    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into semantic chunks."""
        # Try to split on chapter boundaries first
        chapter_markers = [
            r'\n(?:Chapter|CHAPTER)\s+\d+',
            r'\n(?:Part|PART)\s+\d+',
            r'\n#{1,2}\s+',  # Markdown headers
        ]
        
        import re
        for pattern in chapter_markers:
            splits = re.split(pattern, text)
            if len(splits) > 3:
                return [s.strip() for s in splits if s.strip()]
        
        # Fall back to fixed-size chunks with overlap
        words = text.split()
        chunk_size = 10000
        overlap = 500
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def _parse_summary_response(self, response: str) -> dict:
        """Parse the structured summary response."""
        result = {
            'short': '',
            'detailed': '',
            'thesis': '',
            'key_concepts': []
        }
        
        lines = response.split('\n')
        current_key = None
        current_value = []
        
        for line in lines:
            if line.startswith('SHORT_SUMMARY:'):
                if current_key:
                    result[current_key] = ' '.join(current_value).strip()
                current_key = 'short'
                current_value = [line.replace('SHORT_SUMMARY:', '').strip()]
            elif line.startswith('DETAILED_SUMMARY:'):
                if current_key:
                    result[current_key] = ' '.join(current_value).strip()
                current_key = 'detailed'
                current_value = [line.replace('DETAILED_SUMMARY:', '').strip()]
            elif line.startswith('MAIN_THESIS:'):
                if current_key:
                    result[current_key] = ' '.join(current_value).strip()
                current_key = 'thesis'
                current_value = [line.replace('MAIN_THESIS:', '').strip()]
            elif line.startswith('KEY_CONCEPTS:'):
                if current_key:
                    result[current_key] = ' '.join(current_value).strip()
                concepts = line.replace('KEY_CONCEPTS:', '').strip()
                result['key_concepts'] = [c.strip() for c in concepts.split(',')]
                current_key = None
            elif current_key:
                current_value.append(line.strip())
        
        if current_key:
            result[current_key] = ' '.join(current_value).strip()
        
        return result
```

### 5.3 Concept Extractor & Knowledge Graph Builder

```python
from neo4j import GraphDatabase
from typing import List, Dict, Tuple

class ConceptExtractor:
    """
    Extract concepts from text and identify relationships.
    Uses LLM for extraction and existing knowledge graphs 
    (DBpedia, Wikidata) for enrichment.
    """
    
    def __init__(
        self, 
        anthropic_client: Anthropic,
        embedding_service: 'EmbeddingService',
        wikidata_client: 'WikidataClient'
    ):
        self.client = anthropic_client
        self.embedding_service = embedding_service
        self.wikidata = wikidata_client
    
    async def extract_concepts(
        self,
        text: str,
        chapters: List[Chapter]
    ) -> List[Dict]:
        """
        Extract concepts and their coverage from text.
        Returns list of {concept, depth, chapter_refs}
        """
        
        prompt = f"""Analyze this text and extract the main concepts that are taught or explained.

For each concept, indicate:
1. The concept name (use standard terminology)
2. Coverage depth: "introduces" (briefly mentioned), "explains" (full explanation), or "deep_dive" (comprehensive treatment)
3. Any prerequisite concepts needed to understand this

Text:
{text[:100000]}

Format your response as:
CONCEPT: [name] | DEPTH: [introduces/explains/deep_dive] | PREREQUISITES: [concept1, concept2] or "none"
...repeat for each concept..."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        concepts = self._parse_concept_response(response.content[0].text)
        
        # Enrich with external knowledge
        for concept in concepts:
            enriched = await self._enrich_concept(concept['name'])
            concept.update(enriched)
        
        return concepts
    
    async def _enrich_concept(self, concept_name: str) -> Dict:
        """Enrich concept with external knowledge graph data."""
        
        # Try to find in Wikidata
        wikidata_info = await self.wikidata.search_concept(concept_name)
        
        return {
            'wikidata_id': wikidata_info.get('id') if wikidata_info else None,
            'description': wikidata_info.get('description') if wikidata_info else None,
            'broader_concepts': wikidata_info.get('broader', []) if wikidata_info else [],
            'related_concepts': wikidata_info.get('related', []) if wikidata_info else []
        }
    
    def _parse_concept_response(self, response: str) -> List[Dict]:
        """Parse the concept extraction response."""
        concepts = []
        
        for line in response.strip().split('\n'):
            if line.startswith('CONCEPT:'):
                parts = line.split('|')
                if len(parts) >= 2:
                    name = parts[0].replace('CONCEPT:', '').strip()
                    depth = parts[1].replace('DEPTH:', '').strip() if len(parts) > 1 else 'explains'
                    prereqs = []
                    if len(parts) > 2:
                        prereq_str = parts[2].replace('PREREQUISITES:', '').strip()
                        if prereq_str.lower() != 'none':
                            prereqs = [p.strip() for p in prereq_str.split(',')]
                    
                    concepts.append({
                        'name': name,
                        'depth': depth,
                        'prerequisites': prereqs
                    })
        
        return concepts


class Neo4jStore:
    """
    Store and query the knowledge graph in Neo4j.
    """
    
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    async def save_material(self, material: Material):
        """Save a material and its relationships to the graph."""
        
        with self.driver.session() as session:
            # Create material node
            session.run("""
                MERGE (m:Material {id: $id})
                SET m.title = $title,
                    m.authors = $authors,
                    m.isbn = $isbn,
                    m.type = $type,
                    m.page_count = $page_count,
                    m.summary_short = $summary_short,
                    m.summary_detailed = $summary_detailed,
                    m.main_thesis = $main_thesis,
                    m.difficulty_level = $difficulty_level,
                    m.embedding = $embedding
            """, 
                id=material.id,
                title=material.title,
                authors=material.authors,
                isbn=material.isbn,
                type=material.material_type.value,
                page_count=material.page_count,
                summary_short=material.summary_short,
                summary_detailed=material.summary_detailed,
                main_thesis=material.main_thesis,
                difficulty_level=material.difficulty_level,
                embedding=material.embedding
            )
            
            # Create chapters
            for i, chapter in enumerate(material.chapters):
                session.run("""
                    MATCH (m:Material {id: $material_id})
                    MERGE (c:Chapter {id: $chapter_id})
                    SET c.title = $title,
                        c.chapter_number = $chapter_number,
                        c.page_start = $page_start,
                        c.page_end = $page_end,
                        c.summary = $summary,
                        c.embedding = $embedding
                    MERGE (m)-[:HAS_CHAPTER {order: $order}]->(c)
                """,
                    material_id=material.id,
                    chapter_id=chapter.id,
                    title=chapter.title,
                    chapter_number=chapter.chapter_number,
                    page_start=chapter.page_start,
                    page_end=chapter.page_end,
                    summary=chapter.summary,
                    embedding=chapter.embedding,
                    order=i
                )
            
            # Create concept relationships
            for concept_info in material.concepts_covered:
                # Ensure concept exists
                session.run("""
                    MERGE (c:Concept {name: $name})
                    ON CREATE SET c.id = randomUUID()
                """, name=concept_info['name'])
                
                # Link material to concept
                session.run("""
                    MATCH (m:Material {id: $material_id})
                    MATCH (c:Concept {name: $concept_name})
                    MERGE (m)-[r:COVERS]->(c)
                    SET r.depth = $depth
                """,
                    material_id=material.id,
                    concept_name=concept_info['name'],
                    depth=concept_info['depth']
                )
                
                # Add prerequisite relationships
                for prereq in concept_info.get('prerequisites', []):
                    session.run("""
                        MERGE (prereq:Concept {name: $prereq_name})
                        ON CREATE SET prereq.id = randomUUID()
                        
                        MATCH (c:Concept {name: $concept_name})
                        MERGE (prereq)-[:PREREQUISITE_OF]->(c)
                    """,
                        prereq_name=prereq,
                        concept_name=concept_info['name']
                    )
    
    async def find_materials_for_concept(
        self, 
        concept_name: str,
        min_depth: str = "introduces"
    ) -> List[Dict]:
        """Find all materials covering a concept."""
        
        depth_order = {"introduces": 1, "explains": 2, "deep_dive": 3}
        min_depth_val = depth_order.get(min_depth, 1)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Material)-[r:COVERS]->(c:Concept {name: $concept_name})
                WHERE CASE r.depth
                    WHEN 'introduces' THEN 1
                    WHEN 'explains' THEN 2
                    WHEN 'deep_dive' THEN 3
                    ELSE 0
                END >= $min_depth_val
                RETURN m, r.depth as depth
                ORDER BY CASE r.depth
                    WHEN 'deep_dive' THEN 1
                    WHEN 'explains' THEN 2
                    ELSE 3
                END
            """, concept_name=concept_name, min_depth_val=min_depth_val)
            
            return [{"material": dict(record["m"]), "depth": record["depth"]} 
                    for record in result]
    
    async def get_concept_prerequisites(self, concept_name: str) -> List[str]:
        """Get all prerequisites for a concept, recursively."""
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (prereq:Concept)-[:PREREQUISITE_OF*]->(c:Concept {name: $concept_name})
                RETURN DISTINCT prereq.name as name
                ORDER BY length(path) DESC
            """, concept_name=concept_name)
            
            return [record["name"] for record in result]
    
    async def get_learning_path(
        self, 
        start_concepts: List[str],  # What user knows
        target_concepts: List[str]   # What user wants to know
    ) -> List[Dict]:
        """
        Generate an optimal learning path from start to target concepts,
        considering prerequisites.
        """
        
        with self.driver.session() as session:
            result = session.run("""
                // Find all concepts needed (prerequisites of targets not in start)
                MATCH path = (prereq:Concept)-[:PREREQUISITE_OF*0..]->(target:Concept)
                WHERE target.name IN $targets
                AND NOT prereq.name IN $known
                WITH DISTINCT prereq, 
                     min(length(path)) as depth
                
                // Find best materials for each concept
                OPTIONAL MATCH (m:Material)-[r:COVERS]->(prereq)
                WHERE r.depth IN ['explains', 'deep_dive']
                
                RETURN prereq.name as concept,
                       depth,
                       collect(DISTINCT {
                           material_id: m.id,
                           material_title: m.title,
                           depth: r.depth
                       })[0..3] as recommended_materials
                ORDER BY depth DESC
            """, 
                targets=target_concepts,
                known=start_concepts
            )
            
            return [dict(record) for record in result]
```

### 5.4 Relevance Engine

Determines how relevant a material is to a user's learning goals.

```python
import numpy as np
from typing import List, Tuple

class RelevanceEngine:
    """
    Calculates relevance of materials to user's learning goals.
    
    Factors considered:
    1. Concept overlap with learning goals
    2. Coverage depth match (user wants survey vs deep dive)
    3. Prerequisite satisfaction
    4. Semantic similarity of summaries to goals
    """
    
    def __init__(
        self,
        graph_store: Neo4jStore,
        embedding_service: 'EmbeddingService'
    ):
        self.graph = graph_store
        self.embeddings = embedding_service
    
    async def score_relevance(
        self,
        material: Material,
        learning_goal: LearningGoal,
        user_knowledge: Dict[str, float]  # concept -> mastery level
    ) -> Tuple[float, Dict]:
        """
        Score how relevant a material is to a learning goal.
        Returns (score, explanation_dict).
        """
        
        scores = {}
        
        # 1. Concept coverage score
        goal_concepts = set(c.name for c in learning_goal.target_concepts)
        material_concepts = set(c['name'] for c in material.concepts_covered)
        
        coverage_overlap = len(goal_concepts & material_concepts)
        if goal_concepts:
            scores['concept_coverage'] = coverage_overlap / len(goal_concepts)
        else:
            scores['concept_coverage'] = 0.0
        
        # 2. Depth match score
        depth_match = self._score_depth_match(
            material.concepts_covered,
            learning_goal.depth,
            goal_concepts
        )
        scores['depth_match'] = depth_match
        
        # 3. Prerequisite satisfaction
        prereq_score, missing = await self._check_prerequisites(
            material,
            user_knowledge
        )
        scores['prerequisites_met'] = prereq_score
        
        # 4. Semantic similarity
        if material.embedding and learning_goal.embedding:
            similarity = self._cosine_similarity(
                material.embedding,
                learning_goal.embedding
            )
            scores['semantic_similarity'] = similarity
        else:
            scores['semantic_similarity'] = 0.5  # neutral
        
        # Weighted combination
        weights = {
            'concept_coverage': 0.35,
            'depth_match': 0.25,
            'prerequisites_met': 0.20,
            'semantic_similarity': 0.20
        }
        
        total_score = sum(scores[k] * weights[k] for k in weights)
        
        explanation = {
            'scores': scores,
            'matching_concepts': list(goal_concepts & material_concepts),
            'missing_prerequisites': missing,
            'total_score': total_score
        }
        
        return total_score, explanation
    
    def _score_depth_match(
        self,
        material_concepts: List[Dict],
        goal_depth: DepthLevel,
        goal_concept_names: set
    ) -> float:
        """Score how well material depth matches goal depth."""
        
        depth_values = {
            'introduces': 1,
            'explains': 2,
            'deep_dive': 3
        }
        
        goal_depth_value = {
            DepthLevel.SURVEY: 1,
            DepthLevel.WORKING: 2,
            DepthLevel.EXPERT: 3
        }.get(goal_depth, 2)
        
        relevant_concepts = [
            c for c in material_concepts 
            if c['name'] in goal_concept_names
        ]
        
        if not relevant_concepts:
            return 0.5  # neutral
        
        # Calculate average depth match
        matches = []
        for concept in relevant_concepts:
            concept_depth = depth_values.get(concept['depth'], 2)
            # Perfect match = 1.0, off by 1 = 0.7, off by 2 = 0.3
            diff = abs(concept_depth - goal_depth_value)
            match = 1.0 - (diff * 0.35)
            matches.append(max(0, match))
        
        return sum(matches) / len(matches)
    
    async def _check_prerequisites(
        self,
        material: Material,
        user_knowledge: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        """Check if user has prerequisites for this material."""
        
        missing = []
        partially_known = []
        
        for prereq in material.prerequisites:
            mastery = user_knowledge.get(prereq.name, 0.0)
            if mastery < 0.3:
                missing.append(prereq.name)
            elif mastery < 0.7:
                partially_known.append(prereq.name)
        
        total_prereqs = len(material.prerequisites)
        if total_prereqs == 0:
            return 1.0, []
        
        # Score: fully known = 1.0, partially known = 0.5, missing = 0
        known_count = total_prereqs - len(missing) - len(partially_known)
        score = (known_count * 1.0 + len(partially_known) * 0.5) / total_prereqs
        
        return score, missing
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    async def find_relevant_chapters(
        self,
        material: Material,
        learning_goal: LearningGoal
    ) -> List[Tuple[Chapter, float]]:
        """
        Find which chapters of a book are most relevant to a goal.
        This supports partial reading (inspectional reading).
        """
        
        goal_embedding = learning_goal.embedding
        if not goal_embedding:
            goal_embedding = await self.embeddings.embed(
                f"{learning_goal.title}. {learning_goal.description}"
            )
        
        chapter_scores = []
        
        for chapter in material.chapters:
            if chapter.embedding:
                similarity = self._cosine_similarity(chapter.embedding, goal_embedding)
            else:
                # Fall back to keyword matching
                goal_keywords = set(learning_goal.title.lower().split())
                chapter_keywords = set(chapter.title.lower().split())
                if chapter.summary:
                    chapter_keywords.update(chapter.summary.lower().split())
                
                overlap = len(goal_keywords & chapter_keywords)
                similarity = min(1.0, overlap / max(len(goal_keywords), 1))
            
            chapter_scores.append((chapter, similarity))
        
        # Sort by relevance
        chapter_scores.sort(key=lambda x: x[1], reverse=True)
        
        return chapter_scores
```

### 5.5 User Knowledge State Tracker

```python
from datetime import datetime, timedelta

class UserKnowledgeTracker:
    """
    Tracks user's knowledge state across concepts.
    
    Knowledge sources:
    1. Self-reported familiarity
    2. Inferred from reading history
    3. Inferred from concept prerequisites
    """
    
    def __init__(self, graph_store: Neo4jStore):
        self.graph = graph_store
    
    async def get_knowledge_state(self, user_id: str) -> Dict[str, float]:
        """Get user's current knowledge state for all concepts."""
        
        with self.graph.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[r:FAMILIAR_WITH]->(c:Concept)
                RETURN c.name as concept, r.level as level, r.confidence as confidence
            """, user_id=user_id)
            
            return {
                record['concept']: record['level'] * record['confidence']
                for record in result
            }
    
    async def update_from_self_report(
        self,
        user_id: str,
        concept_name: str,
        familiarity: str  # "never_heard", "heard_of", "understand", "can_explain", "mastered"
    ):
        """Update knowledge state from user self-report."""
        
        level_map = {
            "never_heard": 0.0,
            "heard_of": 0.2,
            "understand": 0.5,
            "can_explain": 0.8,
            "mastered": 1.0
        }
        
        level = level_map.get(familiarity, 0.5)
        
        with self.graph.driver.session() as session:
            session.run("""
                MATCH (u:User {id: $user_id})
                MERGE (c:Concept {name: $concept_name})
                ON CREATE SET c.id = randomUUID()
                MERGE (u)-[r:FAMILIAR_WITH]->(c)
                SET r.level = $level,
                    r.confidence = 0.9,
                    r.last_assessed = datetime(),
                    r.source = 'self_reported'
            """,
                user_id=user_id,
                concept_name=concept_name,
                level=level
            )
    
    async def infer_from_reading(
        self,
        user_id: str,
        material_id: str,
        completion: float
    ):
        """
        Infer knowledge updates from reading a material.
        If user completed 80%+ of a book that covers concept X deeply,
        we can infer they have some familiarity with X.
        """
        
        with self.graph.driver.session() as session:
            # Get concepts covered by this material
            result = session.run("""
                MATCH (m:Material {id: $material_id})-[r:COVERS]->(c:Concept)
                RETURN c.name as concept, r.depth as depth
            """, material_id=material_id)
            
            for record in result:
                concept = record['concept']
                depth = record['depth']
                
                # Calculate inferred level based on completion and depth
                depth_factor = {'introduces': 0.3, 'explains': 0.6, 'deep_dive': 0.8}
                inferred_level = completion * depth_factor.get(depth, 0.5)
                
                # Update if higher than current (don't decrease)
                session.run("""
                    MATCH (u:User {id: $user_id})
                    MERGE (c:Concept {name: $concept_name})
                    ON CREATE SET c.id = randomUUID()
                    MERGE (u)-[r:FAMILIAR_WITH]->(c)
                    ON CREATE SET r.level = $level,
                                 r.confidence = $confidence,
                                 r.last_assessed = datetime(),
                                 r.source = 'inferred'
                    ON MATCH SET r.level = CASE 
                        WHEN $level > r.level AND r.source = 'inferred' 
                        THEN $level 
                        ELSE r.level 
                    END
                """,
                    user_id=user_id,
                    concept_name=concept,
                    level=inferred_level,
                    confidence=0.6  # Lower confidence for inferences
                )
    
    async def propagate_prerequisite_knowledge(self, user_id: str):
        """
        If user knows concept B, and A is prerequisite of B,
        user probably knows A too (unless explicitly marked unknown).
        """
        
        with self.graph.driver.session() as session:
            session.run("""
                // Find concepts user knows
                MATCH (u:User {id: $user_id})-[known:FAMILIAR_WITH]->(c:Concept)
                WHERE known.level >= 0.5
                
                // Find their prerequisites
                MATCH (prereq:Concept)-[:PREREQUISITE_OF]->(c)
                
                // Only update if not already tracked or if inferred
                MERGE (u)-[r:FAMILIAR_WITH]->(prereq)
                ON CREATE SET r.level = known.level * 0.8,
                             r.confidence = 0.5,
                             r.last_assessed = datetime(),
                             r.source = 'inferred_prerequisite'
            """, user_id=user_id)
```

---

## 6. Recommendation Engine

### 6.1 Main Recommendation Logic

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class RecommendationType(Enum):
    DIRECT_MATCH = "direct_match"      # Directly covers goal concepts
    PREREQUISITE = "prerequisite"       # Needed before direct materials
    COMPLEMENTARY = "complementary"     # Related but different angle
    SERENDIPITOUS = "serendipitous"    # Interesting tangent

@dataclass
class Recommendation:
    material: Material
    type: RecommendationType
    relevance_score: float
    reason: str
    suggested_chapters: List[Chapter]
    estimated_time_hours: float
    priority: int  # 1 = highest

class RecommendationEngine:
    """
    Generate personalized reading recommendations.
    
    Strategy:
    1. Find materials directly covering goal concepts
    2. Identify prerequisite materials if needed
    3. Find complementary materials for breadth
    4. Surface serendipitous finds from interest queue
    """
    
    def __init__(
        self,
        graph_store: Neo4jStore,
        relevance_engine: RelevanceEngine,
        knowledge_tracker: UserKnowledgeTracker
    ):
        self.graph = graph_store
        self.relevance = relevance_engine
        self.knowledge = knowledge_tracker
    
    async def generate_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Recommendation]:
        """Generate top recommendations for a user."""
        
        recommendations = []
        
        # Get user's active goals and knowledge state
        goals = await self._get_active_goals(user_id)
        knowledge_state = await self.knowledge.get_knowledge_state(user_id)
        
        for goal in goals:
            # 1. Direct matches
            direct_matches = await self._find_direct_matches(goal, knowledge_state)
            for material, score, chapters in direct_matches[:3]:
                recommendations.append(Recommendation(
                    material=material,
                    type=RecommendationType.DIRECT_MATCH,
                    relevance_score=score,
                    reason=f"Covers concepts in your goal: {goal.title}",
                    suggested_chapters=chapters,
                    estimated_time_hours=self._estimate_time(material, chapters),
                    priority=1
                ))
            
            # 2. Prerequisites (if direct matches have unmet prereqs)
            prereqs_needed = await self._find_prerequisite_materials(
                goal, 
                knowledge_state
            )
            for material, concepts in prereqs_needed[:2]:
                recommendations.append(Recommendation(
                    material=material,
                    type=RecommendationType.PREREQUISITE,
                    relevance_score=0.8,
                    reason=f"Will help you understand: {', '.join(concepts)}",
                    suggested_chapters=[],  # Read fully
                    estimated_time_hours=self._estimate_time(material, []),
                    priority=2
                ))
        
        # 3. Complementary materials (for breadth goals)
        breadth_goals = [g for g in goals if g.depth == DepthLevel.SURVEY]
        for goal in breadth_goals:
            complementary = await self._find_complementary(goal, knowledge_state)
            for material, reason in complementary[:2]:
                recommendations.append(Recommendation(
                    material=material,
                    type=RecommendationType.COMPLEMENTARY,
                    relevance_score=0.6,
                    reason=reason,
                    suggested_chapters=[],
                    estimated_time_hours=self._estimate_time(material, []),
                    priority=3
                ))
        
        # 4. Surface from interest queue
        queued = await self._get_interest_queue(user_id)
        for material, context in queued[:2]:
            relevance = await self._score_queue_item_relevance(
                material, 
                goals, 
                knowledge_state
            )
            if relevance > 0.3:
                recommendations.append(Recommendation(
                    material=material,
                    type=RecommendationType.SERENDIPITOUS,
                    relevance_score=relevance,
                    reason=f"From your interest queue: {context}",
                    suggested_chapters=[],
                    estimated_time_hours=self._estimate_time(material, []),
                    priority=4
                ))
        
        # Sort by priority then relevance
        recommendations.sort(key=lambda r: (r.priority, -r.relevance_score))
        
        return recommendations[:limit]
    
    async def _find_direct_matches(
        self,
        goal: LearningGoal,
        knowledge_state: Dict[str, float]
    ) -> List[Tuple[Material, float, List[Chapter]]]:
        """Find materials that directly cover goal concepts."""
        
        results = []
        
        # Get all materials covering goal concepts
        for concept in goal.target_concepts:
            materials = await self.graph.find_materials_for_concept(
                concept.name,
                min_depth="explains" if goal.depth != DepthLevel.SURVEY else "introduces"
            )
            
            for mat_info in materials:
                material = Material(**mat_info['material'])
                score, _ = await self.relevance.score_relevance(
                    material, 
                    goal, 
                    knowledge_state
                )
                
                # Find most relevant chapters
                relevant_chapters = await self.relevance.find_relevant_chapters(
                    material,
                    goal
                )
                top_chapters = [ch for ch, s in relevant_chapters if s > 0.5][:5]
                
                results.append((material, score, top_chapters))
        
        # Deduplicate and sort
        seen = set()
        unique_results = []
        for material, score, chapters in sorted(results, key=lambda x: -x[1]):
            if material.id not in seen:
                seen.add(material.id)
                unique_results.append((material, score, chapters))
        
        return unique_results
    
    async def _find_prerequisite_materials(
        self,
        goal: LearningGoal,
        knowledge_state: Dict[str, float]
    ) -> List[Tuple[Material, List[str]]]:
        """Find materials that cover missing prerequisites."""
        
        # Get prerequisites user doesn't know
        missing_prereqs = []
        for concept in goal.target_concepts:
            prereqs = await self.graph.get_concept_prerequisites(concept.name)
            for prereq in prereqs:
                if knowledge_state.get(prereq, 0) < 0.5:
                    missing_prereqs.append(prereq)
        
        # Find materials covering these
        prereq_materials = []
        for prereq in set(missing_prereqs):
            materials = await self.graph.find_materials_for_concept(
                prereq,
                min_depth="explains"
            )
            for mat_info in materials[:2]:
                material = Material(**mat_info['material'])
                prereq_materials.append((material, [prereq]))
        
        return prereq_materials
    
    def _estimate_time(
        self, 
        material: Material, 
        suggested_chapters: List[Chapter]
    ) -> float:
        """Estimate reading time in hours."""
        
        if suggested_chapters:
            total_pages = sum(
                (ch.page_end - ch.page_start) 
                for ch in suggested_chapters
            )
        else:
            total_pages = material.page_count or 200
        
        # Assume ~30 pages per hour for focused reading
        return total_pages / 30
```

---

## 7. User Interface Flows

### 7.1 Key User Journeys

```
┌─────────────────────────────────────────────────────────────────────┐
│                    JOURNEY 1: Define Learning Goal                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User: "I want to learn about distributed systems"                   │
│           ↓                                                          │
│  System: Identifies concept → Shows related concepts                 │
│           ↓                                                          │
│  User: Selects depth (survey / working / expert)                     │
│           ↓                                                          │
│  System: Asks about existing knowledge                               │
│          "Are you familiar with: networking, concurrency, ..."       │
│           ↓                                                          │
│  System: Creates learning goal → Generates initial recommendations   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│               JOURNEY 2: Evaluate a Specific Book                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User: "Is 'Designing Data-Intensive Applications' relevant         │
│         to my distributed systems goal?"                             │
│           ↓                                                          │
│  System: Fetches/generates book summary                              │
│           ↓                                                          │
│  System: Maps concepts covered vs. goal concepts                     │
│           ↓                                                          │
│  System: Shows relevance analysis:                                   │
│          "✓ 85% relevant - covers 5 of 6 target concepts"           │
│          "Chapters 5-9 are most relevant to your goal"              │
│          "⚠ Assumes familiarity with: databases, networking"        │
│           ↓                                                          │
│  User: Adds to reading queue / marks specific chapters               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│           JOURNEY 3: Quick Add to Interest Queue                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User: Discovers interesting book (podcast, article, friend)         │
│           ↓                                                          │
│  User: Quick-adds to system with context                             │
│        "Mentioned in podcast X, looks interesting for Y"             │
│           ↓                                                          │
│  System: Fetches metadata, generates summary                         │
│           ↓                                                          │
│  System: Stores in interest queue with context                       │
│           ↓                                                          │
│  Later: System surfaces when relevant to active goals                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                JOURNEY 4: Explore the Knowledge Map                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  User: Opens knowledge explorer                                      │
│           ↓                                                          │
│  System: Shows concept graph centered on user's goals                │
│          - Known concepts (green)                                    │
│          - Learning concepts (yellow)                                │
│          - Unknown prerequisites (red)                               │
│           ↓                                                          │
│  User: Clicks on concept → sees:                                     │
│        - Definition & context                                        │
│        - Materials covering it (ranked by quality)                   │
│        - Prerequisites                                               │
│        - What it unlocks (downstream concepts)                       │
│           ↓                                                          │
│  User: Adjusts learning path, discovers gaps                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 CLI Interface Example

```python
# Example CLI for the system

import asyncio
import click

@click.group()
def cli():
    """Learning-Directed Knowledge Management System"""
    pass

@cli.command()
@click.argument('title_or_isbn')
async def add_book(title_or_isbn: str):
    """Add a book to the system."""
    pipeline = get_ingestion_pipeline()
    material = await pipeline.ingest_material(title_or_isbn)
    
    click.echo(f"\n✓ Added: {material.title}")
    click.echo(f"  Authors: {', '.join(material.authors)}")
    click.echo(f"  Summary: {material.summary_short}")
    click.echo(f"  Concepts: {', '.join(c['name'] for c in material.concepts_covered[:5])}")

@cli.command()
@click.argument('goal_description')
@click.option('--depth', type=click.Choice(['survey', 'working', 'expert']), default='working')
async def set_goal(goal_description: str, depth: str):
    """Set a learning goal."""
    # Parse goal, identify concepts, create goal object
    goal = await create_learning_goal(goal_description, DepthLevel(depth))
    
    click.echo(f"\n✓ Goal created: {goal.title}")
    click.echo(f"  Target concepts: {', '.join(c.name for c in goal.target_concepts)}")
    click.echo(f"  Depth: {goal.depth.value}")
    
    # Get initial recommendations
    recommendations = await get_recommendations(goal)
    click.echo(f"\n📚 Recommended reading:")
    for i, rec in enumerate(recommendations[:5], 1):
        click.echo(f"  {i}. {rec.material.title}")
        click.echo(f"     Relevance: {rec.relevance_score:.0%} | {rec.reason}")
        if rec.suggested_chapters:
            chapters = ', '.join(ch.title for ch in rec.suggested_chapters[:3])
            click.echo(f"     Focus on: {chapters}")

@cli.command()
@click.argument('book_title')
async def evaluate(book_title: str):
    """Evaluate a book's relevance to your goals."""
    material = await find_material(book_title)
    goals = await get_active_goals()
    
    click.echo(f"\n📖 {material.title}")
    click.echo(f"   {material.summary_short}\n")
    
    for goal in goals:
        score, explanation = await score_relevance(material, goal)
        
        status = "✓" if score > 0.7 else "○" if score > 0.4 else "✗"
        click.echo(f"{status} Goal: {goal.title}")
        click.echo(f"  Relevance: {score:.0%}")
        click.echo(f"  Matching concepts: {', '.join(explanation['matching_concepts'])}")
        
        if explanation['missing_prerequisites']:
            click.echo(f"  ⚠ Missing prerequisites: {', '.join(explanation['missing_prerequisites'])}")
        
        # Show relevant chapters
        relevant_chapters = await find_relevant_chapters(material, goal)
        if relevant_chapters:
            click.echo(f"  📑 Most relevant chapters:")
            for chapter, chapter_score in relevant_chapters[:3]:
                if chapter_score > 0.5:
                    click.echo(f"     - {chapter.title} ({chapter_score:.0%})")

@cli.command()
async def recommend():
    """Get personalized reading recommendations."""
    user_id = get_current_user_id()
    recommendations = await generate_recommendations(user_id)
    
    click.echo("\n🎯 Your Reading Recommendations\n")
    
    by_type = {}
    for rec in recommendations:
        by_type.setdefault(rec.type, []).append(rec)
    
    if RecommendationType.PREREQUISITE in by_type:
        click.echo("📚 Build your foundation first:")
        for rec in by_type[RecommendationType.PREREQUISITE]:
            click.echo(f"   • {rec.material.title}")
            click.echo(f"     {rec.reason}")
    
    if RecommendationType.DIRECT_MATCH in by_type:
        click.echo("\n🎯 Direct matches for your goals:")
        for rec in by_type[RecommendationType.DIRECT_MATCH]:
            click.echo(f"   • {rec.material.title} ({rec.relevance_score:.0%})")
            click.echo(f"     {rec.reason}")
            if rec.suggested_chapters:
                click.echo(f"     Focus: {', '.join(ch.title for ch in rec.suggested_chapters[:2])}")

if __name__ == '__main__':
    cli()
```

---

## 8. Technology Stack Recommendations

### 8.1 Core Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Graph Database** | Neo4j | Best-in-class for knowledge graphs, excellent Python support, Cypher query language |
| **Vector Store** | Pinecone or Chroma | Semantic search for concept matching. Chroma for local dev, Pinecone for production |
| **LLM** | Claude (Anthropic) | Excellent for summarization, concept extraction, reasoning |
| **Backend** | Python + FastAPI | Async support, type hints, ecosystem |
| **Embeddings** | OpenAI Ada-002 or Voyage | High quality text embeddings |

### 8.2 Python Dependencies

```toml
# pyproject.toml
[project]
name = "learning-knowledge-system"
version = "0.1.0"
requires-python = ">=3.10"

dependencies = [
    # Core
    "fastapi>=0.100.0",
    "uvicorn>=0.22.0",
    "pydantic>=2.0.0",
    
    # Database
    "neo4j>=5.0.0",
    "neo4j-graphrag>=0.1.0",  # Neo4j's official GraphRAG package
    
    # AI/ML
    "anthropic>=0.25.0",
    "openai>=1.0.0",         # For embeddings
    "langchain>=0.1.0",       # For chains and orchestration
    "chromadb>=0.4.0",        # Local vector store
    
    # HTTP/APIs
    "httpx>=0.24.0",
    
    # Utilities
    "numpy>=1.24.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
    
    # CLI
    "click>=8.0.0",
    "rich>=13.0.0",          # Pretty terminal output
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
]
```

### 8.3 Project Structure

```
learning-knowledge-system/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app
│   ├── cli.py                     # CLI interface
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── concepts.py            # Concept, Material, Chapter
│   │   ├── users.py               # User, LearningGoal, KnowledgeState
│   │   └── recommendations.py     # Recommendation types
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py        # Main ingestion pipeline
│   │   │   ├── metadata_fetchers.py
│   │   │   └── concept_extractor.py
│   │   │
│   │   ├── summarization.py       # LLM summarization
│   │   ├── embeddings.py          # Embedding service
│   │   ├── relevance.py           # Relevance scoring
│   │   ├── recommendations.py     # Recommendation engine
│   │   └── knowledge_tracker.py   # User knowledge state
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── neo4j_store.py         # Neo4j operations
│   │   └── vector_store.py        # Vector storage
│   │
│   └── api/
│       ├── __init__.py
│       ├── routes/
│       │   ├── materials.py
│       │   ├── goals.py
│       │   ├── recommendations.py
│       │   └── knowledge.py
│       └── schemas.py             # Pydantic request/response
│
├── tests/
├── docs/
├── pyproject.toml
├── docker-compose.yml             # Neo4j, etc.
└── README.md
```

---

## 9. Implementation Phases

### Phase 1: Foundation (Weeks 1-3)
- [ ] Set up project structure and dependencies
- [ ] Implement Neo4j schema and basic operations
- [ ] Build metadata fetching from Open Library + Google Books
- [ ] Basic CLI for adding materials

### Phase 2: Intelligence (Weeks 4-6)
- [ ] LLM summarization service (hierarchical)
- [ ] Concept extraction and prerequisite identification
- [ ] Embedding generation and storage
- [ ] Basic relevance scoring

### Phase 3: User Experience (Weeks 7-9)
- [ ] Learning goal creation and management
- [ ] User knowledge state tracking
- [ ] Recommendation engine
- [ ] Chapter-level relevance analysis

### Phase 4: Polish (Weeks 10-12)
- [ ] Interest queue and serendipitous discovery
- [ ] Knowledge graph visualization
- [ ] Reading progress tracking
- [ ] API and potential web interface

---

## 10. Future Enhancements

1. **Social Features**: Share reading lists, see what others learning X read
2. **Spaced Repetition Integration**: Connect to Anki for concept review
3. **Full-Text Search**: Index actual book content (if available)
4. **Reading Time Optimization**: AI-assisted skimming suggestions
5. **Learning Analytics**: Track learning velocity, identify patterns
6. **Multi-Modal**: Support video courses, podcasts, papers
7. **Export**: Generate personalized syllabi, reading lists

---

## Appendix A: Concept Extraction Prompt

```text
You are a knowledge extractor. Given text from a book or article, identify:

1. CONCEPTS: Key ideas, theories, frameworks, or skills taught
2. DEPTH: How thoroughly each concept is covered
   - "introduces": briefly mentioned
   - "explains": full explanation
   - "deep_dive": comprehensive treatment
3. PREREQUISITES: What must be understood first

Format:
CONCEPT: [name] | DEPTH: [level] | PREREQUISITES: [list or "none"]

Example:
CONCEPT: Gradient Descent | DEPTH: deep_dive | PREREQUISITES: calculus, linear algebra
CONCEPT: Neural Networks | DEPTH: explains | PREREQUISITES: gradient descent, matrices
```

## Appendix B: Book Evaluation Prompt

```text
Given this book summary and a learning goal, evaluate relevance:

BOOK: {title}
SUMMARY: {summary}
CONCEPTS COVERED: {concepts}

LEARNING GOAL: {goal_title}
GOAL DESCRIPTION: {goal_description}
TARGET DEPTH: {depth}

Provide:
1. RELEVANCE_SCORE: 0.0 to 1.0
2. MATCHING_CONCEPTS: concepts in common
3. SUGGESTED_CHAPTERS: most relevant sections (if known)
4. PREREQUISITES_ASSUMED: knowledge the book assumes
5. RECOMMENDATION: brief advice on how to read this book for this goal
```

---

*This design document provides a comprehensive blueprint for building a learning-directed knowledge management system. The architecture is modular, allowing incremental implementation while maintaining a clear vision for the complete system.*
