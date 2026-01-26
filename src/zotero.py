from __future__ import annotations

import difflib
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


@dataclass(frozen=True)
class ZoteroItem:
    item_id: int
    item_key: str
    title: str
    item_type: str
    creators: list[str]
    year: int | None


def resolve_zotero_db_path(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit)
    env_path = os.getenv("ZOTERO_DB_PATH")
    if env_path:
        return Path(env_path)
    candidates = [Path.home() / "Zotero" / "zotero.sqlite", Path.home() / ".zotero" / "zotero.sqlite"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Zotero database not found. Set ZOTERO_DB_PATH or pass --zotero-db."
    )


def find_item_by_title(conn: sqlite3.Connection, title: str) -> ZoteroItem:
    items = _fetch_items(conn)
    if not items:
        raise ValueError("No Zotero items found.")

    exact = [item for item in items if item.title.lower() == title.lower()]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise ValueError(_candidate_message("title", title, exact))

    prefix = [item for item in items if item.title.lower().startswith(title.lower())]
    if len(prefix) == 1:
        return prefix[0]
    if len(prefix) > 1:
        raise ValueError(_candidate_message("title", title, prefix))

    titles = [item.title for item in items]
    matches = difflib.get_close_matches(title, titles, n=3, cutoff=0.6)
    if len(matches) == 1:
        match_title = matches[0]
        for item in items:
            if item.title == match_title:
                return item
    if matches:
        raise ValueError(f"Fuzzy match found multiple items: {', '.join(matches)}")

    raise ValueError(f'No Zotero item found for "{title}".')


def map_item_type(item_type: str) -> str:
    normalized = item_type.lower()
    if normalized in {"journalarticle", "conferencepaper"}:
        return "paper"
    if normalized in {"booksection", "magazinearticle", "newspaperarticle"}:
        return "article"
    return "book"


def item_to_book_payload(item: ZoteroItem) -> dict:
    return {
        "title": item.title,
        "authors": item.creators,
        "year": item.year,
        "book_type": map_item_type(item.item_type),
        "zotero_key": item.item_key,
        "identifiers": None,
    }


def create_book_from_zotero(
    conn: sqlite3.Connection,
    *,
    title: str,
    zotero_db_path: str | Path | None = None,
) -> dict:
    db_path = resolve_zotero_db_path(zotero_db_path)
    with sqlite3.connect(db_path) as zotero_conn:
        zotero_conn.row_factory = sqlite3.Row
        item = find_item_by_title(zotero_conn, title)
    payload = item_to_book_payload(item)
    authors_json = _json_dumps(payload["authors"])
    identifiers_json = _json_dumps(payload["identifiers"])
    cursor = conn.execute(
        """
        INSERT INTO books (title, authors, year, type, zotero_key, identifiers)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload["title"],
            authors_json,
            payload["year"],
            payload["book_type"],
            payload["zotero_key"],
            identifiers_json,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM books WHERE id = ?", (cursor.lastrowid,)).fetchone()
    if row is None:
        raise ValueError("Failed to create book from Zotero.")
    return dict(row)


def _json_dumps(value: object | None) -> str | None:
    if value is None:
        return None
    import json

    return json.dumps(value)


def _fetch_items(conn: sqlite3.Connection) -> list[ZoteroItem]:
    rows = conn.execute(
        """
        SELECT i.itemID,
               i.key,
               it.typeName,
               v.value AS title
        FROM items i
        JOIN itemTypes it ON it.itemTypeID = i.itemTypeID
        JOIN itemData d ON d.itemID = i.itemID
        JOIN fields f ON f.fieldID = d.fieldID
        JOIN itemDataValues v ON v.valueID = d.valueID
        WHERE f.fieldName = 'title'
        """
    ).fetchall()
    items = []
    for row in rows:
        item_id = row[0]
        creators = _fetch_creators(conn, item_id)
        year = _fetch_year(conn, item_id)
        items.append(
            ZoteroItem(
                item_id=item_id,
                item_key=row[1],
                title=row[3],
                item_type=row[2],
                creators=creators,
                year=year,
            )
        )
    return items


def _fetch_creators(conn: sqlite3.Connection, item_id: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT c.firstName, c.lastName
        FROM itemCreators ic
        JOIN creators c ON c.creatorID = ic.creatorID
        WHERE ic.itemID = ?
        ORDER BY ic.orderIndex
        """,
        (item_id,),
    ).fetchall()
    creators: list[str] = []
    for row in rows:
        first = row[0] or ""
        last = row[1] or ""
        name = (first + " " + last).strip()
        if name:
            creators.append(name)
    return creators


def _fetch_year(conn: sqlite3.Connection, item_id: int) -> int | None:
    row = conn.execute(
        """
        SELECT v.value
        FROM itemData d
        JOIN fields f ON f.fieldID = d.fieldID
        JOIN itemDataValues v ON v.valueID = d.valueID
        WHERE d.itemID = ? AND f.fieldName = 'date'
        """,
        (item_id,),
    ).fetchone()
    if not row or not row[0]:
        return None
    match = _YEAR_RE.search(str(row[0]))
    if not match:
        return None
    return int(match.group(0))


def _candidate_message(kind: str, query: str, items: Iterable[ZoteroItem]) -> str:
    collected = list(items)
    titles = ", ".join(item.title for item in collected[:8])
    suffix = "..." if len(collected) > 8 else ""
    return f"Ambiguous {kind} '{query}'. Candidates: {titles}{suffix}"
