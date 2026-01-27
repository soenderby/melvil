from __future__ import annotations

import difflib
import json
import sqlite3


class ResolutionError(ValueError):
    pass


class ResolutionNotFoundError(ResolutionError):
    pass


def resolve_book_id(conn: sqlite3.Connection, title: str) -> tuple[int, str]:
    row = conn.execute(
        """
        SELECT b.id, b.title
        FROM aliases a
        JOIN books b ON b.id = a.book_id
        WHERE a.alias = ? COLLATE NOCASE
        """,
        (title,),
    ).fetchone()
    if row:
        return row["id"], row["title"]

    row = conn.execute(
        "SELECT id, title FROM books WHERE title = ? COLLATE NOCASE",
        (title,),
    ).fetchone()
    if row:
        return row["id"], row["title"]

    rows = conn.execute(
        "SELECT id, title FROM books WHERE title LIKE ? COLLATE NOCASE ORDER BY title",
        (f"{title}%",),
    ).fetchall()
    if len(rows) == 1:
        return rows[0]["id"], rows[0]["title"]
    if len(rows) > 1:
        raise ResolutionError(_candidate_message("book", title, rows))

    all_rows = conn.execute("SELECT id, title FROM books ORDER BY title").fetchall()
    if not all_rows:
        raise ResolutionError("No books found.")
    titles = [row["title"] for row in all_rows]
    matches = difflib.get_close_matches(title, titles, n=3, cutoff=0.6)
    if len(matches) == 1:
        match = matches[0]
        for row in all_rows:
            if row["title"] == match:
                return row["id"], row["title"]
    if matches:
        raise ResolutionError(f'Fuzzy match found multiple books: {", ".join(matches)}')

    raise ResolutionError(f'No book found for "{title}".')


def resolve_concept_id(conn: sqlite3.Connection, name: str) -> tuple[int, str]:
    row = conn.execute(
        "SELECT id, name FROM concepts WHERE name = ? COLLATE NOCASE",
        (name,),
    ).fetchone()
    if row:
        return row["id"], row["name"]

    matches = []
    for row in conn.execute("SELECT id, name, aliases FROM concepts").fetchall():
        raw = row["aliases"]
        if not raw:
            continue
        try:
            aliases = json.loads(raw)
        except json.JSONDecodeError:
            aliases = []
        if any(str(alias).lower() == name.lower() for alias in aliases):
            matches.append(row)
    if len(matches) == 1:
        return matches[0]["id"], matches[0]["name"]
    if len(matches) > 1:
        raise ResolutionError(f'Concept alias "{name}" matches multiple concepts.')

    rows = conn.execute(
        "SELECT id, name FROM concepts WHERE name LIKE ? COLLATE NOCASE ORDER BY name",
        (f"{name}%",),
    ).fetchall()
    if len(rows) == 1:
        return rows[0]["id"], rows[0]["name"]
    if len(rows) > 1:
        raise ResolutionError(_candidate_message("concept", name, rows))

    all_rows = conn.execute("SELECT id, name FROM concepts ORDER BY name").fetchall()
    if not all_rows:
        raise ResolutionNotFoundError("No concepts found.")
    names = [row["name"] for row in all_rows]
    matches = difflib.get_close_matches(name, names, n=3, cutoff=0.6)
    if len(matches) == 1:
        match = matches[0]
        for row in all_rows:
            if row["name"] == match:
                return row["id"], row["name"]
    if matches:
        raise ResolutionError(f'Fuzzy match found multiple concepts: {", ".join(matches)}')

    raise ResolutionNotFoundError(f'No concept found for "{name}".')


def resolve_concept_id_exact(conn: sqlite3.Connection, name: str) -> tuple[int, str]:
    row = conn.execute(
        "SELECT id, name FROM concepts WHERE name = ? COLLATE NOCASE",
        (name,),
    ).fetchone()
    if row:
        return row["id"], row["name"]

    matches = []
    for row in conn.execute("SELECT id, name, aliases FROM concepts").fetchall():
        raw = row["aliases"]
        if not raw:
            continue
        try:
            aliases = json.loads(raw)
        except json.JSONDecodeError:
            aliases = []
        if any(str(alias).lower() == name.lower() for alias in aliases):
            matches.append(row)
    if len(matches) == 1:
        return matches[0]["id"], matches[0]["name"]
    if len(matches) > 1:
        raise ResolutionError(f'Concept alias "{name}" matches multiple concepts.')

    raise ResolutionNotFoundError(f'No concept found for "{name}".')


def _candidate_message(kind: str, query: str, rows: list[sqlite3.Row]) -> str:
    options = ", ".join(row[1] for row in rows[:8])
    suffix = "..." if len(rows) > 8 else ""
    return f'Ambiguous {kind} "{query}". Candidates: {options}{suffix}'
