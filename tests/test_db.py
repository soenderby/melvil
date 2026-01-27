from __future__ import annotations

from src import db


def test_initialize_creates_schema(tmp_path):
    db_path = tmp_path / "melvil.db"
    conn = db.connect(db_path)
    db.initialize(conn)

    rows = conn.execute(
        "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'index', 'trigger')"
    ).fetchall()
    names = {row["name"] for row in rows}

    for table in (
        "schema_migrations",
        "books",
        "chapters",
        "concepts",
        "book_concepts",
        "concept_links",
        "notes",
        "note_concepts",
        "note_links",
        "aliases",
        "notes_fts",
    ):
        assert table in names

    for trigger in ("notes_ai", "notes_au", "notes_ad"):
        assert trigger in names

    for index in (
        "books_title_idx",
        "books_depth_idx",
        "chapters_book_id_idx",
        "concepts_name_idx",
        "notes_type_idx",
        "note_concepts_note_id_idx",
    ):
        assert index in names

    conn.close()


def test_connect_enables_foreign_keys(tmp_path):
    db_path = tmp_path / "melvil.db"
    conn = db.connect(db_path)
    pragma = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    assert pragma == 1
    conn.close()


def test_notes_fts_triggers(db_conn):
    cursor = db_conn.execute(
        "INSERT INTO notes (title, body, note_type) VALUES (?, ?, ?)",
        ("Title", "Initial body", "standard"),
    )
    note_id = int(cursor.lastrowid)

    row = db_conn.execute(
        "SELECT rowid, body FROM notes_fts WHERE rowid = ?",
        (note_id,),
    ).fetchone()
    assert row["rowid"] == note_id
    assert row["body"] == "Initial body"

    db_conn.execute(
        "UPDATE notes SET body = ? WHERE id = ?",
        ("Updated body", note_id),
    )
    row = db_conn.execute(
        "SELECT body FROM notes_fts WHERE rowid = ?",
        (note_id,),
    ).fetchone()
    assert row["body"] == "Updated body"

    db_conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    row = db_conn.execute(
        "SELECT COUNT(*) AS count FROM notes_fts WHERE rowid = ?",
        (note_id,),
    ).fetchone()
    assert row["count"] == 0
