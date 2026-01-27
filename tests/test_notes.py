from __future__ import annotations

from src.notes import (
    parse_wikilinks,
    resolve_or_create_concept_id,
    sync_wikilink_concepts,
)


def _add_concept(conn, name: str) -> int:
    cursor = conn.execute("INSERT INTO concepts (name) VALUES (?)", (name,))
    return int(cursor.lastrowid)


def _add_note(conn, body: str) -> int:
    cursor = conn.execute("INSERT INTO notes (body) VALUES (?)", (body,))
    return int(cursor.lastrowid)


def test_parse_wikilinks_dedup_and_trim():
    text = "See [[Consensus]] and [[consensus ]] and [[ ]] plus [[Linearizability]]"
    assert parse_wikilinks(text) == ["Consensus", "Linearizability"]


def test_resolve_or_create_concept_id(db_conn):
    concept_id = _add_concept(db_conn, "consensus")
    resolved = resolve_or_create_concept_id(db_conn, "consensus")
    assert resolved == concept_id

    created = resolve_or_create_concept_id(db_conn, "linearizability")
    assert created != concept_id


def test_sync_wikilink_concepts_creates_and_removes(db_conn):
    note_id = _add_note(db_conn, "body")
    explicit_id = _add_concept(db_conn, "explicit")
    wikilink_id = _add_concept(db_conn, "wikilink")
    obsolete_id = _add_concept(db_conn, "obsolete")

    db_conn.execute(
        "INSERT INTO note_concepts (note_id, concept_id, source) VALUES (?, ?, ?)",
        (note_id, explicit_id, "explicit"),
    )
    db_conn.execute(
        "INSERT INTO note_concepts (note_id, concept_id, source) VALUES (?, ?, ?)",
        (note_id, obsolete_id, "wikilink"),
    )

    wikilink_ids = sync_wikilink_concepts(
        db_conn,
        note_id=note_id,
        wikilink_names=["wikilink", "new concept"],
        explicit_ids={explicit_id},
    )

    rows = db_conn.execute(
        "SELECT concept_id FROM note_concepts WHERE note_id = ? AND source = 'wikilink'",
        (note_id,),
    ).fetchall()
    stored_ids = {row[0] for row in rows}

    assert wikilink_ids == stored_ids
    assert wikilink_id in stored_ids
    assert obsolete_id not in stored_ids
