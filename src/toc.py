from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import sqlite3


class TocError(ValueError):
    pass


@dataclass
class ChapterInput:
    number: str | None
    title: str
    parent_id: int | None
    position: int | None
    page_start: int | None
    page_end: int | None


def add_chapter(
    conn: sqlite3.Connection, book_id: int, chapter: ChapterInput
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO chapters (
            book_id, number, title, parent_id, position, page_start, page_end
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (
            book_id,
            chapter.number,
            chapter.title,
            chapter.parent_id,
            chapter.position,
            chapter.page_start,
            chapter.page_end,
        ),
    )
    return int(cursor.lastrowid)


def update_summary(conn: sqlite3.Connection, chapter_id: int, summary: str) -> None:
    conn.execute(
        "UPDATE chapters SET summary = ? WHERE id = ?;",
        (summary, chapter_id),
    )


def resolve_chapter_id(
    conn: sqlite3.Connection, book_id: int, chapter_ref: str
) -> int:
    if chapter_ref.isdigit():
        row = conn.execute(
            "SELECT id FROM chapters WHERE book_id = ? AND id = ?;",
            (book_id, int(chapter_ref)),
        ).fetchone()
        if row:
            return int(row["id"])

    rows = conn.execute(
        "SELECT id FROM chapters WHERE book_id = ? AND number = ?;",
        (book_id, chapter_ref),
    ).fetchall()
    if len(rows) == 1:
        return int(rows[0]["id"])
    if len(rows) > 1:
        raise TocError(
            f'Ambiguous chapter "{chapter_ref}" for book {book_id}. '
            "Multiple matches on chapter number."
        )

    raise TocError(f'No chapter "{chapter_ref}" found for book {book_id}.')


def import_from_pdf(
    conn: sqlite3.Connection, book_id: int, pdf_path: Path
) -> int:
    try:
        import fitz  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional dependency
        raise TocError("PyMuPDF (fitz) is required for PDF import.") from exc

    doc = fitz.open(pdf_path)
    toc = doc.get_toc(simple=True)
    if not toc:
        raise TocError("No PDF outline found to import.")

    inserted = 0
    stack: list[tuple[int, int]] = []
    for position, (level, title, page) in enumerate(toc, start=1):
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent_id = stack[-1][1] if stack else None
        chapter = ChapterInput(
            number=None,
            title=title.strip(),
            parent_id=parent_id,
            position=position,
            page_start=int(page) if page else None,
            page_end=None,
        )
        chapter_id = add_chapter(conn, book_id, chapter)
        stack.append((level, chapter_id))
        inserted += 1
    return inserted


def parse_pages(pages: str | None) -> tuple[int | None, int | None]:
    if not pages:
        return None, None
    if "-" in pages:
        start, end = pages.split("-", maxsplit=1)
        return _parse_page(start), _parse_page(end)
    return _parse_page(pages), None


def _parse_page(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    if not value.isdigit():
        raise TocError(f'Invalid page value "{value}".')
    return int(value)
