from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
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
                suffix_parts = []
                if row["number"]:
                    suffix_parts.append(f"Ch. {row['number']}")
                if row["location"]:
                    suffix_parts.append(row["location"])
                if suffix_parts:
                    detail += f" ({', '.join(suffix_parts)})"
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


def export_map_obsidian(conn: sqlite3.Connection, output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    if output_dir.exists():
        if not output_dir.is_dir():
            raise ValueError(f"Output path {output_dir} is not a directory.")
        if any(output_dir.iterdir()):
            raise ValueError(f"Output directory {output_dir} is not empty.")
    output_dir.mkdir(parents=True, exist_ok=True)

    books_dir = output_dir / "Books"
    concepts_dir = output_dir / "Concepts"
    notes_dir = output_dir / "Notes"
    books_dir.mkdir(exist_ok=True)
    concepts_dir.mkdir(exist_ok=True)
    notes_dir.mkdir(exist_ok=True)

    books = conn.execute(
        """
        SELECT id, title, authors, year, depth, about
        FROM books
        ORDER BY title
        """
    ).fetchall()
    concepts = conn.execute(
        """
        SELECT id, name, definition
        FROM concepts
        ORDER BY name
        """
    ).fetchall()
    concept_links = conn.execute(
        """
        SELECT from_concept_id, to_concept_id, link_type
        FROM concept_links
        ORDER BY from_concept_id, to_concept_id
        """
    ).fetchall()
    book_concepts = conn.execute(
        """
        SELECT bc.book_id, bc.concept_id, ch.number, bc.location
        FROM book_concepts bc
        LEFT JOIN chapters ch ON ch.id = bc.chapter_id
        ORDER BY bc.book_id, bc.concept_id
        """
    ).fetchall()
    notes = conn.execute(
        """
        SELECT id, title, body, note_type, source_location, book_id, is_quote
        FROM notes
        ORDER BY id
        """
    ).fetchall()
    note_concepts = conn.execute(
        """
        SELECT nc.note_id, nc.concept_id
        FROM note_concepts nc
        ORDER BY nc.note_id, nc.concept_id
        """
    ).fetchall()

    concept_names = {row["id"]: row["name"] for row in concepts}
    book_titles = {row["id"]: row["title"] for row in books}

    used_book_names: set[str] = set()
    book_file_names = {
        row["id"]: _unique_obsidian_name(row["title"], used_book_names, str(row["id"]))
        for row in books
    }
    used_concept_names: set[str] = set()
    concept_file_names = {
        row["id"]: _unique_obsidian_name(row["name"], used_concept_names, str(row["id"]))
        for row in concepts
    }
    note_file_names = {row["id"]: f"Note {row['id']}" for row in notes}

    concept_related: dict[int, list[tuple[int, str]]] = {}
    for row in concept_links:
        concept_related.setdefault(row["from_concept_id"], []).append(
            (row["to_concept_id"], row["link_type"])
        )

    concept_books: dict[int, list[dict[str, str | None]]] = {}
    book_concept_ids: dict[int, set[int]] = {}
    for row in book_concepts:
        concept_books.setdefault(row["concept_id"], []).append(
            {
                "book_id": row["book_id"],
                "chapter_number": row["number"],
                "location": row["location"],
            }
        )
        book_concept_ids.setdefault(row["book_id"], set()).add(row["concept_id"])

    concept_note_ids: dict[int, list[int]] = {}
    note_concept_ids: dict[int, list[int]] = {}
    for row in note_concepts:
        concept_note_ids.setdefault(row["concept_id"], []).append(row["note_id"])
        note_concept_ids.setdefault(row["note_id"], []).append(row["concept_id"])

    for book in books:
        book_id = book["id"]
        book_name = book["title"]
        file_name = book_file_names[book_id]
        lines: list[str] = [f"# {book_name}", ""]
        aliases = _aliases_front_matter([book_name], file_name)
        if aliases:
            lines = aliases + lines
        authors = _format_authors(book["authors"])
        if authors:
            lines.append(f"- **Author**: {authors}")
        if book["year"]:
            lines.append(f"- **Year**: {book['year']}")
        if book["depth"]:
            lines.append(f"- **Depth**: {book['depth']}")
        if book["about"]:
            lines.append(f"- **About**: {book['about']}")
        concepts_for_book = sorted(
            [concept_names[concept_id] for concept_id in book_concept_ids.get(book_id, set())]
        )
        if concepts_for_book:
            lines.append("")
            lines.append("## Concepts")
            for concept_name in concepts_for_book:
                lines.append(f"- [[{concept_name}]]")
        _write_markdown(books_dir / f"{file_name}.md", lines)

    for concept in concepts:
        concept_id = concept["id"]
        concept_name = concept["name"]
        file_name = concept_file_names[concept_id]
        lines = [f"# {concept_name}", ""]
        aliases = _aliases_front_matter([concept_name], file_name)
        if aliases:
            lines = aliases + lines
        if concept["definition"]:
            lines.append(f"**Definition**: {concept['definition']}")
            lines.append("")
        related = concept_related.get(concept_id, [])
        if related:
            lines.append("## Related Concepts")
            for related_id, link_type in related:
                related_name = concept_names.get(related_id, f"Concept {related_id}")
                lines.append(f"- [[{related_name}]] ({link_type})")
            lines.append("")
        book_refs = concept_books.get(concept_id, [])
        if book_refs:
            lines.append("## Books")
            for ref in book_refs:
                book_title = book_titles.get(ref["book_id"], f"Book {ref['book_id']}")
                chapter = ref["chapter_number"]
                location = ref["location"]
                suffix = ""
                if chapter and location:
                    suffix = f" (Ch. {chapter}, {location})"
                elif chapter:
                    suffix = f" (Ch. {chapter})"
                elif location:
                    suffix = f" ({location})"
                lines.append(f"- [[{book_title}]]{suffix}")
            lines.append("")
        notes_for_concept = concept_note_ids.get(concept_id, [])
        if notes_for_concept:
            lines.append("## Notes")
            for note_id in notes_for_concept:
                lines.append(f"- [[{note_file_names[note_id]}]]")
        _write_markdown(concepts_dir / f"{file_name}.md", lines)

    for note in notes:
        note_id = note["id"]
        file_name = note_file_names[note_id]
        heading = note["title"] or file_name
        lines = [f"# {heading}", ""]
        if note["note_type"]:
            lines.append(f"- **Type**: {note['note_type']}")
        if note["source_location"]:
            lines.append(f"- **Source**: {note['source_location']}")
        if note["is_quote"]:
            lines.append("- **Quote**: yes")
        if note["book_id"]:
            book_title = book_titles.get(note["book_id"], f"Book {note['book_id']}")
            lines.append(f"- **Book**: [[{book_title}]]")
        concepts_for_note = [concept_names[cid] for cid in note_concept_ids.get(note_id, [])]
        if concepts_for_note:
            links = ", ".join(f"[[{name}]]" for name in concepts_for_note)
            lines.append(f"- **Concepts**: {links}")
        lines.append("")
        lines.append(note["body"].strip())
        _write_markdown(notes_dir / f"{file_name}.md", lines)

    return output_dir


def obsidian_default_dir() -> Path:
    return Path(f"melvil-obsidian-{_export_timestamp()}")


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


def _safe_obsidian_name(name: str) -> str:
    forbidden = set('<>:"/\\|?*')
    cleaned = "".join("-" if ch in forbidden else ch for ch in name)
    cleaned = " ".join(cleaned.split())
    cleaned = cleaned.strip().strip(".")
    return cleaned or "Untitled"


def _unique_obsidian_name(name: str, used: set[str], suffix: str) -> str:
    candidate = _safe_obsidian_name(name)
    if candidate in used:
        candidate = f"{candidate} ({suffix})"
    counter = 2
    while candidate in used:
        candidate = f"{candidate} ({suffix}-{counter})"
        counter += 1
    used.add(candidate)
    return candidate


def _aliases_front_matter(aliases: list[str], file_name: str) -> list[str]:
    normalized = [alias for alias in aliases if alias and alias != file_name]
    if not normalized:
        return []
    escaped = [alias.replace("\\", "\\\\").replace('"', '\\"') for alias in normalized]
    alias_list = ", ".join(f'"{alias}"' for alias in escaped)
    return ["---", f"aliases: [{alias_list}]", "---", ""]


def _write_markdown(path: Path, lines: list[str]) -> None:
    content = "\n".join(lines).rstrip() + "\n"
    path.write_text(content, encoding="utf-8")


def _escape_dot(value: str) -> str:
    return value.replace('"', '\\"')
