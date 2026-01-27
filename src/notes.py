from __future__ import annotations

import re
import sqlite3

from .resolve import ResolutionNotFoundError, resolve_concept_id

WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")


def parse_wikilinks(text: str) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for match in WIKILINK_RE.finditer(text):
        name = match.group(1).strip()
        if not name:
            continue
        lowered = name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        results.append(name)
    return results


def resolve_or_create_concept_id(conn: sqlite3.Connection, name: str) -> int:
    try:
        concept_id, _ = resolve_concept_id(conn, name)
        return concept_id
    except ResolutionNotFoundError:
        cursor = conn.execute(
            "INSERT INTO concepts (name) VALUES (?)",
            (name,),
        )
        return int(cursor.lastrowid)


def insert_note_concepts(
    conn: sqlite3.Connection,
    *,
    note_id: int,
    concept_ids: list[int],
    source: str,
) -> None:
    for concept_id in concept_ids:
        conn.execute(
            """
            INSERT OR IGNORE INTO note_concepts (note_id, concept_id, source)
            VALUES (?, ?, ?)
            """,
            (note_id, concept_id, source),
        )


def sync_wikilink_concepts(
    conn: sqlite3.Connection,
    *,
    note_id: int,
    wikilink_names: list[str],
    explicit_ids: set[int],
) -> set[int]:
    resolved_ids = {
        resolve_or_create_concept_id(conn, name) for name in wikilink_names
    }
    wikilink_ids = resolved_ids - explicit_ids

    if wikilink_ids:
        placeholders = ",".join("?" for _ in wikilink_ids)
        conn.execute(
            f"""
            DELETE FROM note_concepts
            WHERE note_id = ? AND source = 'wikilink'
              AND concept_id NOT IN ({placeholders})
            """,
            (note_id, *wikilink_ids),
        )
    else:
        conn.execute(
            "DELETE FROM note_concepts WHERE note_id = ? AND source = 'wikilink'",
            (note_id,),
        )

    insert_note_concepts(
        conn,
        note_id=note_id,
        concept_ids=sorted(wikilink_ids),
        source="wikilink",
    )

    return wikilink_ids
