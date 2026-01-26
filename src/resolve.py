from __future__ import annotations

import sqlite3


class ResolutionError(ValueError):
    pass


def resolve_book_id(conn: sqlite3.Connection, title: str) -> tuple[int, str]:
    row = conn.execute(
        """
        SELECT b.id, b.title
        FROM aliases a
        JOIN books b ON b.id = a.book_id
        WHERE a.alias = ?
        """,
        (title,),
    ).fetchone()
    if row:
        return row["id"], row["title"]

    row = conn.execute(
        "SELECT id, title FROM books WHERE title = ?",
        (title,),
    ).fetchone()
    if row:
        return row["id"], row["title"]

    rows = conn.execute(
        "SELECT id, title FROM books WHERE title LIKE ? ORDER BY title",
        (f"{title}%",),
    ).fetchall()
    if len(rows) == 1:
        return rows[0]["id"], rows[0]["title"]
    if len(rows) > 1:
        raise ResolutionError(_candidate_message("book", title, rows))

    rows = conn.execute(
        "SELECT id, title FROM books WHERE title LIKE ? ORDER BY title",
        (f"%{title}%",),
    ).fetchall()
    if len(rows) == 1:
        return rows[0]["id"], rows[0]["title"]
    if len(rows) > 1:
        raise ResolutionError(_candidate_message("book", title, rows))

    raise ResolutionError(f'No book found for "{title}".')


def resolve_concept_id(conn: sqlite3.Connection, name: str) -> tuple[int, str]:
    row = conn.execute(
        "SELECT id, name FROM concepts WHERE name = ?",
        (name,),
    ).fetchone()
    if row:
        return row["id"], row["name"]

    rows = conn.execute(
        "SELECT id, name FROM concepts WHERE name LIKE ? ORDER BY name",
        (f"{name}%",),
    ).fetchall()
    if len(rows) == 1:
        return rows[0]["id"], rows[0]["name"]
    if len(rows) > 1:
        raise ResolutionError(_candidate_message("concept", name, rows))

    rows = conn.execute(
        "SELECT id, name FROM concepts WHERE name LIKE ? ORDER BY name",
        (f"%{name}%",),
    ).fetchall()
    if len(rows) == 1:
        return rows[0]["id"], rows[0]["name"]
    if len(rows) > 1:
        raise ResolutionError(_candidate_message("concept", name, rows))

    raise ResolutionError(f'No concept found for "{name}".')


def _candidate_message(kind: str, query: str, rows: list[sqlite3.Row]) -> str:
    options = ", ".join(row[1] for row in rows[:8])
    suffix = "..." if len(rows) > 8 else ""
    return f'Ambiguous {kind} "{query}". Candidates: {options}{suffix}'
