from __future__ import annotations

import json
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from src.cli import cli
from src.db import connect, initialize


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "melvil.db"
    conn = connect(db_path)
    initialize(conn)
    conn.close()
    return db_path


def _invoke(db_path: Path, args: list[str]):
    runner = CliRunner()
    return runner.invoke(cli, ["--db", str(db_path), *args])


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return _init_db(tmp_path)


def test_add_show_list_depth_about_alias(db_path: Path):
    result = _invoke(
        db_path,
        [
            "add",
            "Designing Data-Intensive Applications",
            "--author",
            "Martin Kleppmann",
            "--year",
            "2017",
        ],
    )
    assert result.exit_code == 0
    assert "Added: Designing Data-Intensive Applications" in result.output

    result = _invoke(db_path, ["show", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    assert "Designing Data-Intensive Applications" in result.output

    result = _invoke(
        db_path,
        ["about", "Designing Data-Intensive Applications", "Systems thinking"],
    )
    assert result.exit_code == 0
    assert "Updated about" in result.output

    result = _invoke(
        db_path,
        ["depth", "Designing Data-Intensive Applications", "mapped"],
    )
    assert result.exit_code == 0
    assert "Updated depth" in result.output

    result = _invoke(
        db_path,
        ["alias", "DDIA", "Designing Data-Intensive Applications"],
    )
    assert result.exit_code == 0
    assert "Alias added" in result.output

    result = _invoke(db_path, ["show", "DDIA"])
    assert result.exit_code == 0
    assert "Designing Data-Intensive Applications" in result.output

    result = _invoke(db_path, ["books", "--depth", "mapped"])
    assert result.exit_code == 0
    assert "Designing Data-Intensive Applications" in result.output


def test_book_updates_set_updated_at(db_path: Path):
    result = _invoke(db_path, ["add", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0

    conn = connect(db_path)
    book_id = conn.execute(
        "SELECT id FROM books WHERE title = ?",
        ("Designing Data-Intensive Applications",),
    ).fetchone()["id"]
    conn.execute(
        "UPDATE books SET updated_at = ? WHERE id = ?",
        ("2000-01-01 00:00:00", book_id),
    )
    conn.commit()
    conn.close()

    result = _invoke(
        db_path,
        ["depth", "Designing Data-Intensive Applications", "mapped"],
    )
    assert result.exit_code == 0

    conn = connect(db_path)
    updated_at = conn.execute(
        "SELECT updated_at FROM books WHERE id = ?",
        (book_id,),
    ).fetchone()["updated_at"]
    conn.close()
    assert updated_at != "2000-01-01 00:00:00"


def test_books_invalid_depth(db_path: Path):
    result = _invoke(db_path, ["books", "--depth", "unknown"])
    assert result.exit_code != 0
    assert "Depth must be one of" in result.output


def test_alias_duplicate_friendly_error(db_path: Path):
    result = _invoke(db_path, ["add", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        ["alias", "DDIA", "Designing Data-Intensive Applications"],
    )
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        ["alias", "DDIA", "Designing Data-Intensive Applications"],
    )
    assert result.exit_code != 0
    assert 'Alias "DDIA" is already in use.' in result.output


def test_show_ambiguous_book(db_path: Path):
    for title in ("Designing Data-Intensive Applications", "Design Patterns"):
        result = _invoke(db_path, ["add", title])
        assert result.exit_code == 0

    result = _invoke(db_path, ["show", "Des"])
    assert result.exit_code != 0
    assert "Ambiguous book" in result.output


def test_concept_commands_and_map(db_path: Path):
    result = _invoke(db_path, ["add", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        ["toc", "add", "Designing Data-Intensive Applications", "--number", "1", "--title", "Intro"],
    )
    assert result.exit_code == 0

    result = _invoke(db_path, ["concept", "consensus"])
    assert result.exit_code == 0
    assert "Created concept" in result.output

    result = _invoke(db_path, ["concept", "linearizability"])
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "concept",
            "link",
            "consensus",
            "--book",
            "Designing Data-Intensive Applications",
            "--chapter",
            "1",
            "--location",
            "p.10",
            "--note",
            "Intro mention",
        ],
    )
    assert result.exit_code == 0
    assert "Linked" in result.output

    result = _invoke(
        db_path,
        ["toc", "add", "Designing Data-Intensive Applications", "--number", "2", "--title", "More"],
    )
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "concept",
            "link",
            "consensus",
            "--book",
            "Designing Data-Intensive Applications",
            "--chapter",
            "2",
            "--location",
            "p.20",
            "--note",
            "Second mention",
        ],
    )
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        ["note", "--concept", "consensus", "--title", "Key note", "Consensus note body."],
    )
    assert result.exit_code == 0
    assert "Added note" in result.output

    result = _invoke(
        db_path,
        ["concept", "relate", "consensus", "linearizability", "--type", "related"],
    )
    assert result.exit_code == 0
    assert "Related" in result.output

    result = _invoke(db_path, ["concept", "alias", "consensus", "raft", "paxos"])
    assert result.exit_code == 0
    assert "Aliases updated" in result.output

    result = _invoke(db_path, ["concept", "show", "consensus"])
    assert result.exit_code == 0
    assert "consensus" in result.output
    assert "Key note" in result.output

    result = _invoke(db_path, ["concept", "mentions", "--book", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    assert "Concept mentions" in result.output

    result = _invoke(db_path, ["concepts"])
    assert result.exit_code == 0
    assert "consensus" in result.output

    result = _invoke(db_path, ["map"])
    assert result.exit_code == 0
    assert "Concept Map" in result.output

    result = _invoke(db_path, ["map", "--concept", "consensus"])
    assert result.exit_code == 0
    assert "Books covering" in result.output
    assert result.output.count("Designing") == 1

    result = _invoke(db_path, ["map", "--book", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    assert result.output.count("consensus") == 1

    result = _invoke(db_path, ["map", "--book", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    assert "Concepts in" in result.output

    result = _invoke(db_path, ["map", "--related", "consensus"])
    assert result.exit_code == 0
    assert "Related concepts" in result.output


def test_concepts_orphan_excludes_note_links(db_path: Path):
    result = _invoke(db_path, ["concept", "consensus"])
    assert result.exit_code == 0

    result = _invoke(db_path, ["note", "--concept", "consensus", "Note body."])
    assert result.exit_code == 0

    result = _invoke(db_path, ["concepts", "--orphan"])
    assert result.exit_code == 0
    assert "Orphan concepts" in result.output
    assert "consensus" not in result.output


def test_concept_link_missing_chapter(db_path: Path):
    result = _invoke(db_path, ["add", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    result = _invoke(db_path, ["concept", "consensus"])
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "concept",
            "link",
            "consensus",
            "--book",
            "Designing Data-Intensive Applications",
            "--chapter",
            "99",
        ],
    )
    assert result.exit_code != 0
    assert "No chapter \"99\" found for book" in result.output


def test_concept_link_ambiguous_chapter_number(db_path: Path):
    result = _invoke(db_path, ["add", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    result = _invoke(db_path, ["concept", "consensus"])
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "toc",
            "add",
            "Designing Data-Intensive Applications",
            "--number",
            "I",
            "--title",
            "Intro",
            "--pages",
            "1-10",
        ],
    )
    assert result.exit_code == 0
    result = _invoke(
        db_path,
        [
            "toc",
            "add",
            "Designing Data-Intensive Applications",
            "--number",
            "I",
            "--title",
            "Prelude",
            "--pages",
            "11-20",
        ],
    )
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "concept",
            "link",
            "consensus",
            "--book",
            "Designing Data-Intensive Applications",
            "--chapter",
            "I",
        ],
    )
    assert result.exit_code != 0
    assert "Ambiguous chapter \"I\"" in result.output


def test_note_and_quote_commands(db_path: Path):
    result = _invoke(db_path, ["add", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    result = _invoke(db_path, ["concept", "consensus"])
    assert result.exit_code == 0
    result = _invoke(db_path, ["concept", "linearizability"])
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "note",
            "--concept",
            "consensus",
            "Single concept note.",
        ],
    )
    assert result.exit_code == 0
    assert "Added note" in result.output

    result = _invoke(
        db_path,
        [
            "note",
            "--concept",
            "consensus",
            "--concept",
            "linearizability",
            "Too many concepts",
        ],
    )
    assert result.exit_code != 0
    assert "Standard notes can link to at most one concept" in result.output

    result = _invoke(
        db_path,
        [
            "note",
            "--type",
            "relation",
            "--concept",
            "consensus",
            "--concept",
            "linearizability",
            "Relation note",
        ],
    )
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "quote",
            "--book",
            "Designing Data-Intensive Applications",
            "--location",
            "p.1",
            "Quoted text.",
        ],
    )
    assert result.exit_code == 0
    assert "Added quote" in result.output

    result = _invoke(db_path, ["notes"])
    assert result.exit_code == 0
    assert "Notes" in result.output


def test_standard_note_concept_limit_does_not_create_concepts(db_path: Path):
    result = _invoke(
        db_path,
        [
            "note",
            "--concept",
            "alpha",
            "See [[beta]].",
        ],
    )
    assert result.exit_code != 0
    assert "Standard notes can link to at most one concept" in result.output

    conn = connect(db_path)
    concept_count = conn.execute("SELECT COUNT(*) AS count FROM concepts").fetchone()[
        "count"
    ]
    conn.close()
    assert concept_count == 0


def test_note_edit_wikilink_sync(db_path: Path, monkeypatch: pytest.MonkeyPatch):
    result = _invoke(db_path, ["note", "See [[consensus]]."])
    assert result.exit_code == 0

    conn = connect(db_path)
    note_id = conn.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1").fetchone()[
        "id"
    ]
    conn.execute(
        "UPDATE notes SET updated_at = ? WHERE id = ?",
        ("2000-01-01 00:00:00", note_id),
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(click, "edit", lambda _: "Updated with [[raft]].")
    result = _invoke(db_path, ["note", "edit", str(note_id)])
    assert result.exit_code == 0
    assert "Updated note" in result.output

    conn = connect(db_path)
    rows = conn.execute(
        """
        SELECT c.name
        FROM note_concepts nc
        JOIN concepts c ON c.id = nc.concept_id
        WHERE nc.note_id = ? AND nc.source = 'wikilink'
        """,
        (note_id,),
    ).fetchall()
    names = [row["name"] for row in rows]
    assert names == ["raft"]

    updated_at = conn.execute(
        "SELECT updated_at FROM notes WHERE id = ?",
        (note_id,),
    ).fetchone()["updated_at"]
    assert updated_at != "2000-01-01 00:00:00"
    conn.close()


def test_note_edit_standard_note_concept_limit(
    db_path: Path, monkeypatch: pytest.MonkeyPatch
):
    result = _invoke(db_path, ["concept", "consensus"])
    assert result.exit_code == 0
    result = _invoke(db_path, ["note", "--concept", "consensus", "Original."])
    assert result.exit_code == 0

    conn = connect(db_path)
    note_id = conn.execute("SELECT id FROM notes ORDER BY id DESC LIMIT 1").fetchone()[
        "id"
    ]
    conn.close()

    monkeypatch.setattr(click, "edit", lambda _: "Updated with [[raft]].")
    result = _invoke(db_path, ["note", "edit", str(note_id)])
    assert result.exit_code != 0
    assert "Standard notes can link to at most one concept" in result.output


def test_notes_search(db_path: Path):
    result = _invoke(db_path, ["note", "Consensus note body."])
    assert result.exit_code == 0
    result = _invoke(db_path, ["note", "Availability note body."])
    assert result.exit_code == 0

    result = _invoke(db_path, ["notes", "search", "consensus"])
    assert result.exit_code == 0
    assert "Consensus note body." in result.output
    assert "Availability note body." not in result.output

    result = _invoke(db_path, ["notes", "search", '"consensus'])
    assert result.exit_code != 0
    assert "Invalid FTS query" in result.output


def test_toc_and_export_commands(db_path: Path):
    result = _invoke(db_path, ["add", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    result = _invoke(db_path, ["concept", "consensus"])
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "toc",
            "add",
            "Designing Data-Intensive Applications",
            "--number",
            "1",
            "--title",
            "Intro",
            "--pages",
            "1-10",
        ],
    )
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "toc",
            "summarize",
            "Designing Data-Intensive Applications",
            "--chapter",
            "1",
            "High-level summary",
        ],
    )
    assert result.exit_code == 0

    result = _invoke(db_path, ["toc", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    assert "TOC for" in result.output

    result = _invoke(db_path, ["concept", "link", "consensus", "--book", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0

    result = _invoke(db_path, ["export", "map", "--format", "markdown"])
    assert result.exit_code == 0
    assert "# Concept Map" in result.output

    result = _invoke(db_path, ["export", "map", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "concepts" in payload

    result = _invoke(db_path, ["export", "map", "--format", "dot"])
    assert result.exit_code == 0
    assert "digraph" in result.output


def test_book_concept_mentions_show_all_and_ordered(db_path: Path):
    result = _invoke(db_path, ["add", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    result = _invoke(db_path, ["concept", "consensus"])
    assert result.exit_code == 0
    result = _invoke(
        db_path,
        [
            "toc",
            "add",
            "Designing Data-Intensive Applications",
            "--number",
            "2",
            "--title",
            "Chapter Two",
        ],
    )
    assert result.exit_code == 0
    result = _invoke(
        db_path,
        [
            "toc",
            "add",
            "Designing Data-Intensive Applications",
            "--number",
            "1",
            "--title",
            "Chapter One",
        ],
    )
    assert result.exit_code == 0

    result = _invoke(
        db_path,
        [
            "concept",
            "link",
            "consensus",
            "--book",
            "Designing Data-Intensive Applications",
            "--chapter",
            "2",
            "--location",
            "p.20",
        ],
    )
    assert result.exit_code == 0
    result = _invoke(
        db_path,
        [
            "concept",
            "link",
            "consensus",
            "--book",
            "Designing Data-Intensive Applications",
            "--chapter",
            "1",
            "--location",
            "p.10",
        ],
    )
    assert result.exit_code == 0

    result = _invoke(db_path, ["show", "Designing Data-Intensive Applications"])
    assert result.exit_code == 0
    assert "p.10" in result.output
    assert "p.20" in result.output
    assert result.output.index("p.10") < result.output.index("p.20")

    result = _invoke(
        db_path, ["map", "--book", "Designing Data-Intensive Applications"]
    )
    assert result.exit_code == 0
    assert "p.10" in result.output
    assert "p.20" in result.output
    assert result.output.index("p.10") < result.output.index("p.20")
