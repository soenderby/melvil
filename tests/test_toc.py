from __future__ import annotations

import pytest

from src.toc import ChapterInput, TocError, add_chapter, parse_pages, resolve_chapter_id


def _add_book(conn, title: str) -> int:
    cursor = conn.execute("INSERT INTO books (title) VALUES (?)", (title,))
    return int(cursor.lastrowid)


def test_parse_pages_variants():
    assert parse_pages(None) == (None, None)
    assert parse_pages("12-15") == (12, 15)
    assert parse_pages(" 7 ") == (7, None)
    assert parse_pages(" - ") == (None, None)


def test_parse_pages_invalid():
    with pytest.raises(TocError, match="Invalid page value"):
        parse_pages("12a")


def test_resolve_chapter_id_by_id_and_number(db_conn):
    book_id = _add_book(db_conn, "Test Book")
    chapter_id = add_chapter(
        db_conn,
        book_id,
        chapter=ChapterInput(
            number="1",
            title="Intro",
            parent_id=None,
            position=1,
            page_start=1,
            page_end=2,
        ),
    )

    resolved_by_id = resolve_chapter_id(db_conn, book_id, str(chapter_id))
    assert resolved_by_id == chapter_id

    resolved_by_number = resolve_chapter_id(db_conn, book_id, "1")
    assert resolved_by_number == chapter_id


def test_resolve_chapter_id_ambiguous_number(db_conn):
    book_id = _add_book(db_conn, "Test Book")
    for position in (1, 2):
        add_chapter(
            db_conn,
            book_id,
            chapter=ChapterInput(
                number="I",
                title=f"Ch {position}",
                parent_id=None,
                position=position,
                page_start=position,
                page_end=position + 1,
            ),
        )

    with pytest.raises(TocError, match="Ambiguous chapter"):
        resolve_chapter_id(db_conn, book_id, "I")
