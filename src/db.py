from __future__ import annotations

import sqlite3
from pathlib import Path

MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL COLLATE NOCASE,
            authors TEXT,
            year INTEGER,
            type TEXT DEFAULT 'book' CHECK (type IN ('book', 'paper', 'article')),
            zotero_key TEXT,
            identifiers TEXT,
            depth TEXT DEFAULT 'listed' CHECK (depth IN ('listed', 'mapped', 'reading', 'read', 'deep')),
            about TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(title)
        );

        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            number TEXT,
            title TEXT NOT NULL,
            parent_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
            position INTEGER,
            page_start INTEGER,
            page_end INTEGER,
            summary TEXT,
            relevance TEXT
        );

        CREATE TABLE IF NOT EXISTS concepts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL COLLATE NOCASE,
            aliases TEXT,
            definition TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name)
        );

        CREATE TABLE IF NOT EXISTS book_concepts (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
            chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
            location TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS concept_links (
            id INTEGER PRIMARY KEY,
            from_concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
            to_concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
            link_type TEXT NOT NULL
                CHECK (link_type IN ('related', 'prerequisite', 'contradicts', 'specializes', 'generalizes')),
            notes TEXT,
            UNIQUE(from_concept_id, to_concept_id, link_type)
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT NOT NULL,
            book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
            chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
            note_type TEXT DEFAULT 'standard' CHECK (note_type IN ('standard', 'relation')),
            source_location TEXT,
            is_quote INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS note_concepts (
            id INTEGER PRIMARY KEY,
            note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            concept_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
            source TEXT DEFAULT 'explicit' CHECK (source IN ('explicit', 'wikilink')),
            UNIQUE(note_id, concept_id)
        );

        CREATE TABLE IF NOT EXISTS note_links (
            id INTEGER PRIMARY KEY,
            from_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            to_note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            UNIQUE(from_note_id, to_note_id)
        );

        CREATE TABLE IF NOT EXISTS aliases (
            id INTEGER PRIMARY KEY,
            alias TEXT NOT NULL COLLATE NOCASE,
            book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
            UNIQUE(alias)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
            title,
            body,
            content='notes',
            content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS notes_ai
        AFTER INSERT ON notes
        BEGIN
            INSERT INTO notes_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
        END;

        CREATE TRIGGER IF NOT EXISTS notes_au
        AFTER UPDATE ON notes
        BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, title, body)
            VALUES ('delete', old.id, old.title, old.body);
            INSERT INTO notes_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
        END;

        CREATE TRIGGER IF NOT EXISTS notes_ad
        AFTER DELETE ON notes
        BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, title, body)
            VALUES ('delete', old.id, old.title, old.body);
        END;

        INSERT INTO notes_fts(notes_fts) VALUES ('rebuild');

        CREATE INDEX IF NOT EXISTS books_title_idx ON books(title);
        CREATE INDEX IF NOT EXISTS books_depth_idx ON books(depth);

        CREATE INDEX IF NOT EXISTS chapters_book_id_idx ON chapters(book_id);
        CREATE INDEX IF NOT EXISTS chapters_parent_id_idx ON chapters(parent_id);
        CREATE INDEX IF NOT EXISTS chapters_position_idx ON chapters(book_id, position);

        CREATE INDEX IF NOT EXISTS concepts_name_idx ON concepts(name);

        CREATE INDEX IF NOT EXISTS book_concepts_book_id_idx ON book_concepts(book_id);
        CREATE INDEX IF NOT EXISTS book_concepts_concept_id_idx ON book_concepts(concept_id);
        CREATE INDEX IF NOT EXISTS book_concepts_chapter_id_idx ON book_concepts(chapter_id);

        CREATE INDEX IF NOT EXISTS concept_links_from_idx ON concept_links(from_concept_id);
        CREATE INDEX IF NOT EXISTS concept_links_to_idx ON concept_links(to_concept_id);
        CREATE INDEX IF NOT EXISTS concept_links_type_idx ON concept_links(link_type);

        CREATE INDEX IF NOT EXISTS notes_book_id_idx ON notes(book_id);
        CREATE INDEX IF NOT EXISTS notes_chapter_id_idx ON notes(chapter_id);
        CREATE INDEX IF NOT EXISTS notes_type_idx ON notes(note_type);
        CREATE INDEX IF NOT EXISTS notes_quote_idx ON notes(is_quote);

        CREATE INDEX IF NOT EXISTS note_concepts_note_id_idx ON note_concepts(note_id);
        CREATE INDEX IF NOT EXISTS note_concepts_concept_id_idx ON note_concepts(concept_id);
        CREATE INDEX IF NOT EXISTS note_concepts_source_idx ON note_concepts(source);

        CREATE INDEX IF NOT EXISTS note_links_from_idx ON note_links(from_note_id);
        CREATE INDEX IF NOT EXISTS note_links_to_idx ON note_links(to_note_id);

        CREATE INDEX IF NOT EXISTS aliases_book_id_idx ON aliases(book_id);
        """,
    ),
    (
        2,
        """
        ALTER TABLE chapters ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP;
        """,
    ),
]


def connect(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    current_version = conn.execute(
        "SELECT COALESCE(MAX(version), 0) FROM schema_migrations;"
    ).fetchone()[0]
    for version, sql in MIGRATIONS:
        if version <= current_version:
            continue
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (version) VALUES (?);", (version,)
        )
    conn.commit()
