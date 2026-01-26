from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import sqlite3


def export_map_json(conn: sqlite3.Connection) -> dict[str, Any]:
    books = [dict(row) for row in conn.execute("SELECT * FROM books ORDER BY title")]
    concepts = [dict(row) for row in conn.execute("SELECT * FROM concepts ORDER BY name")]
    concept_links = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM concept_links ORDER BY from_concept_id, to_concept_id"
        )
    ]
    book_concepts = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM book_concepts ORDER BY book_id, concept_id"
        )
    ]
    notes = [dict(row) for row in conn.execute("SELECT * FROM notes ORDER BY id")]
    note_concepts = [
        dict(row)
        for row in conn.execute(
            "SELECT * FROM note_concepts ORDER BY note_id, concept_id"
        )
    ]
    note_links = [
        dict(row)
        for row in conn.execute("SELECT * FROM note_links ORDER BY from_note_id")
    ]

    return {
        "exported_at": _export_timestamp(),
        "books": books,
        "concepts": concepts,
        "book_concepts": book_concepts,
        "concept_links": concept_links,
        "notes": notes,
        "note_concepts": note_concepts,
        "note_links": note_links,
    }


def export_map_markdown(conn: sqlite3.Connection) -> str:
    exported_at = _export_timestamp()
    lines: list[str] = ["# Concept Map", "", f"*Exported from Melvil on {exported_at}*", ""]

    books = conn.execute(
        """
        SELECT id, title, authors, year, depth, about
        FROM books
        ORDER BY title
        """
    ).fetchall()
    lines.append(f"## Books ({len(books)})")
    lines.append("")
    for book in books:
        lines.append(f"### {book['title']}")
        authors = _format_authors(book["authors"])
        if authors:
            lines.append(f"- **Author**: {authors}")
        if book["year"]:
            lines.append(f"- **Year**: {book['year']}")
        lines.append(f"- **Depth**: {book['depth']}")
        if book["about"]:
            lines.append(f"- **About**: {book['about']}")
        concept_rows = conn.execute(
            """
            SELECT c.name
            FROM concepts c
            JOIN book_concepts bc ON bc.concept_id = c.id
            WHERE bc.book_id = ?
            GROUP BY c.id
            ORDER BY c.name
            """,
            (book["id"],),
        ).fetchall()
        if concept_rows:
            concepts = ", ".join(row["name"] for row in concept_rows)
            lines.append(f"- **Concepts**: {concepts}")
        lines.append("")

    concepts = conn.execute(
        """
        SELECT id, name, definition
        FROM concepts
        ORDER BY name
        """
    ).fetchall()
    lines.append(f"## Concepts ({len(concepts)})")
    lines.append("")
    for concept in concepts:
        lines.append(f"### {concept['name']}")
        if concept["definition"]:
            lines.append(f"- **Definition**: {concept['definition']}")
        related_rows = conn.execute(
            """
            SELECT c.name, cl.link_type
            FROM concept_links cl
            JOIN concepts c ON c.id = cl.to_concept_id
            WHERE cl.from_concept_id = ?
            ORDER BY c.name
            """,
            (concept["id"],),
        ).fetchall()
        if related_rows:
            related = ", ".join(
                f"{row['name']} ({row['link_type']})" for row in related_rows
            )
            lines.append(f"- **Related**: {related}")
        book_rows = conn.execute(
            """
            SELECT b.title, ch.number, bc.location
            FROM book_concepts bc
            JOIN books b ON b.id = bc.book_id
            LEFT JOIN chapters ch ON ch.id = bc.chapter_id
            WHERE bc.concept_id = ?
            ORDER BY b.title
            """,
            (concept["id"],),
        ).fetchall()
        if book_rows:
            refs = []
            for row in book_rows:
                detail = row["title"]
                if row["number"]:
                    detail += f" (Ch. {row['number']})"
                elif row["location"]:
                    detail += f" ({row['location']})"
                refs.append(detail)
            lines.append(f"- **Books**: {', '.join(refs)}")
        note_rows = conn.execute(
            """
            SELECT n.id, n.title, n.body
            FROM notes n
            JOIN note_concepts nc ON nc.note_id = n.id
            WHERE nc.concept_id = ?
            ORDER BY n.id
            """,
            (concept["id"],),
        ).fetchall()
        if note_rows:
            lines.append("")
            lines.append("#### Notes")
            for row in note_rows:
                text = row["title"] or row["body"]
                text = text.replace("\n", " ").strip()
                if len(text) > 120:
                    text = text[:117].rstrip() + "..."
                lines.append(f"{row['id']}. {text}")
        lines.append("")

    notes = conn.execute(
        """
        SELECT id, title, body, note_type, source_location
        FROM notes
        ORDER BY id
        """
    ).fetchall()
    lines.append(f"## Notes ({len(notes)})")
    lines.append("")
    for note in notes:
        title = note["title"] or f"Note {note['id']}"
        lines.append(f"### #{note['id']}: {title}")
        if note["source_location"]:
            lines.append(f"- **Source**: {note['source_location']}")
        if note["note_type"]:
            lines.append(f"- **Type**: {note['note_type']}")
        body = note["body"].strip()
        lines.append("")
        lines.append(body)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def export_map_dot(conn: sqlite3.Connection) -> str:
    lines = ["digraph MelvilMap {"]
    lines.append('  graph [splines=true, overlap=false];')
    lines.append('  node [shape=ellipse];')

    concepts = conn.execute("SELECT id, name FROM concepts ORDER BY name").fetchall()
    for concept in concepts:
        lines.append(f'  c{concept["id"]} [label="{_escape_dot(concept["name"])}"];')

    links = conn.execute(
        """
        SELECT from_concept_id, to_concept_id, link_type
        FROM concept_links
        ORDER BY from_concept_id, to_concept_id
        """
    ).fetchall()
    for link in links:
        lines.append(
            f'  c{link["from_concept_id"]} -> c{link["to_concept_id"]} '
            f'[label="{_escape_dot(link["link_type"])}"];'
        )

    lines.append("}")
    return "\n".join(lines) + "\n"


def _export_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _format_authors(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(data, list):
        return ", ".join(str(item) for item in data)
    return str(data)


def _escape_dot(value: str) -> str:
    return value.replace('"', '\\"')
