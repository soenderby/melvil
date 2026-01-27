from __future__ import annotations

import json

import pytest

from src.resolve import ResolutionError, resolve_book_id, resolve_concept_id


def _add_book(conn, title: str) -> int:
    cursor = conn.execute("INSERT INTO books (title) VALUES (?)", (title,))
    return int(cursor.lastrowid)


def _add_alias(conn, alias: str, book_id: int) -> None:
    conn.execute(
        "INSERT INTO aliases (alias, book_id) VALUES (?, ?)", (alias, book_id)
    )


def _add_concept(conn, name: str, aliases: list[str] | None = None) -> int:
    raw_aliases = json.dumps(aliases) if aliases is not None else None
    cursor = conn.execute(
        "INSERT INTO concepts (name, aliases) VALUES (?, ?)",
        (name, raw_aliases),
    )
    return int(cursor.lastrowid)


def test_resolve_book_id_prefers_alias_then_exact(db_conn):
    book_id = _add_book(db_conn, "Designing Data-Intensive Applications")
    _add_alias(db_conn, "DDIA", book_id)

    resolved_id, resolved_title = resolve_book_id(db_conn, "DDIA")
    assert resolved_id == book_id
    assert resolved_title == "Designing Data-Intensive Applications"

    resolved_id, resolved_title = resolve_book_id(
        db_conn, "designing data-intensive applications"
    )
    assert resolved_id == book_id
    assert resolved_title == "Designing Data-Intensive Applications"


def test_resolve_book_id_prefix_and_ambiguous(db_conn):
    book_id = _add_book(db_conn, "Designing Data-Intensive Applications")
    _add_book(db_conn, "Design Patterns")

    resolved_id, _ = resolve_book_id(db_conn, "Designing")
    assert resolved_id == book_id

    with pytest.raises(ResolutionError, match="Ambiguous book"):
        resolve_book_id(db_conn, "Des")


def test_resolve_book_id_fuzzy_single_match(db_conn):
    book_id = _add_book(db_conn, "Refactoring")

    resolved_id, resolved_title = resolve_book_id(db_conn, "Refactring")
    assert resolved_id == book_id
    assert resolved_title == "Refactoring"


def test_resolve_book_id_no_books(db_conn):
    with pytest.raises(ResolutionError, match="No books found"):
        resolve_book_id(db_conn, "Anything")


def test_resolve_concept_alias_and_ambiguous(db_conn):
    concept_id = _add_concept(db_conn, "consensus", ["raft", "paxos"])

    resolved_id, resolved_name = resolve_concept_id(db_conn, "raft")
    assert resolved_id == concept_id
    assert resolved_name == "consensus"

    _add_concept(db_conn, "clock", ["shared"])
    _add_concept(db_conn, "cache", ["shared"])
    with pytest.raises(ResolutionError, match="matches multiple concepts"):
        resolve_concept_id(db_conn, "shared")


def test_resolve_concept_prefix_ambiguous(db_conn):
    _add_concept(db_conn, "consensus")
    _add_concept(db_conn, "consumption")

    with pytest.raises(ResolutionError, match="Ambiguous concept"):
        resolve_concept_id(db_conn, "cons")
