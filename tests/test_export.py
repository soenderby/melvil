from __future__ import annotations

import json

from src import export


def _seed_export_data(conn) -> dict[str, int]:
    alpha_book = conn.execute(
        "INSERT INTO books (title, authors, year, depth, about) VALUES (?, ?, ?, ?, ?)",
        ("Alpha Book", json.dumps(["Ada Author"]), 2001, "mapped", "Alpha summary"),
    ).lastrowid
    beta_book = conn.execute(
        "INSERT INTO books (title, authors, year, depth) VALUES (?, ?, ?, ?)",
        ("Beta Book", json.dumps(["Bob Writer"]), 1999, "listed"),
    ).lastrowid

    alpha_concept = conn.execute(
        "INSERT INTO concepts (name, definition) VALUES (?, ?)",
        ("Alpha \"Quoted\"", "Alpha definition"),
    ).lastrowid
    zeta_concept = conn.execute(
        "INSERT INTO concepts (name, definition) VALUES (?, ?)",
        ("Zeta", None),
    ).lastrowid

    chapter_id = conn.execute(
        "INSERT INTO chapters (book_id, number, title, position) VALUES (?, ?, ?, ?)",
        (alpha_book, "1", "Intro", 1),
    ).lastrowid

    conn.execute(
        "INSERT INTO book_concepts (book_id, concept_id, chapter_id, location, notes) VALUES (?, ?, ?, ?, ?)",
        (alpha_book, alpha_concept, chapter_id, "p.10", "Mention"),
    )
    conn.execute(
        "INSERT INTO book_concepts (book_id, concept_id) VALUES (?, ?)",
        (beta_book, zeta_concept),
    )
    conn.execute(
        "INSERT INTO concept_links (from_concept_id, to_concept_id, link_type, notes) VALUES (?, ?, ?, ?)",
        (alpha_concept, zeta_concept, "related", ""),
    )

    note_one = conn.execute(
        "INSERT INTO notes (title, body, note_type, source_location) VALUES (?, ?, ?, ?)",
        ("Alpha note", "First note body", "standard", "p.1"),
    ).lastrowid
    note_two = conn.execute(
        "INSERT INTO notes (title, body, note_type) VALUES (?, ?, ?)",
        (None, "Second note body", "relation"),
    ).lastrowid

    conn.execute(
        "INSERT INTO note_concepts (note_id, concept_id, source) VALUES (?, ?, ?)",
        (note_one, alpha_concept, "explicit"),
    )
    conn.execute(
        "INSERT INTO note_concepts (note_id, concept_id, source) VALUES (?, ?, ?)",
        (note_two, zeta_concept, "explicit"),
    )

    conn.commit()
    return {
        "alpha_book": int(alpha_book),
        "beta_book": int(beta_book),
        "alpha_concept": int(alpha_concept),
        "zeta_concept": int(zeta_concept),
        "note_one": int(note_one),
        "note_two": int(note_two),
    }


def test_export_map_json_ordering(db_conn):
    _seed_export_data(db_conn)

    payload = export.export_map_json(db_conn)

    assert [book["title"] for book in payload["books"]] == [
        "Alpha Book",
        "Beta Book",
    ]
    assert [concept["name"] for concept in payload["concepts"]] == [
        "Alpha \"Quoted\"",
        "Zeta",
    ]
    assert [note["id"] for note in payload["notes"]] == sorted(
        [note["id"] for note in payload["notes"]]
    )


def test_export_map_markdown_sections_and_order(monkeypatch, db_conn):
    _seed_export_data(db_conn)
    monkeypatch.setattr(export, "_export_timestamp", lambda: "2026-01-27")

    output = export.export_map_markdown(db_conn)

    assert "# Concept Map" in output
    assert "*Exported from Melvil on 2026-01-27*" in output
    assert "## Books (2)" in output
    assert "## Concepts (2)" in output
    assert "## Notes (2)" in output

    assert output.index("### Alpha Book") < output.index("### Beta Book")
    assert output.index("### Alpha \"Quoted\"") < output.index("### Zeta")
    assert output.index("### #1:") < output.index("### #2:")
    assert "Ch. 1, p.10" in output


def test_export_map_dot_escaping(db_conn):
    _seed_export_data(db_conn)

    output = export.export_map_dot(db_conn)

    assert 'label="Alpha \\"Quoted\\""' in output
    assert output.startswith("digraph MelvilMap")


def test_export_map_obsidian_writes_vault(tmp_path, db_conn):
    _seed_export_data(db_conn)

    output_dir = tmp_path / "vault"
    result = export.export_map_obsidian(db_conn, output_dir)

    assert result == output_dir
    assert (output_dir / "Books").is_dir()
    assert (output_dir / "Concepts").is_dir()
    assert (output_dir / "Notes").is_dir()

    concept_files = list((output_dir / "Concepts").glob("*.md"))
    assert any('Alpha "Quoted"' in path.read_text() for path in concept_files)
    alpha_concept = next(
        path for path in concept_files if 'Alpha "Quoted"' in path.read_text()
    )
    assert "[[Zeta]]" in alpha_concept.read_text()

    book_files = list((output_dir / "Books").glob("*.md"))
    assert any("Alpha Book" in path.read_text() for path in book_files)

    note_files = list((output_dir / "Notes").glob("*.md"))
    assert any("First note body" in path.read_text() for path in note_files)
