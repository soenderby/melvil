from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import db  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Melvil MVP perf harness.")
    parser.add_argument("--books", type=int, default=100)
    parser.add_argument("--concepts", type=int, default=500)
    parser.add_argument("--notes", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--db-path", type=Path, default=Path("/tmp/melvil_perf.db"))
    return parser.parse_args()


def timed(label: str, fn) -> float:
    start = time.perf_counter()
    fn()
    elapsed = time.perf_counter() - start
    print(f"{label}: {elapsed * 1000:.2f}ms")
    return elapsed


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    if args.db_path.exists():
        args.db_path.unlink()

    conn = db.connect(args.db_path)
    db.initialize(conn)

    depths = ["listed", "mapped", "reading", "read", "deep"]
    with conn:
        conn.executemany(
            """
            INSERT INTO books (title, authors, year, depth)
            VALUES (?, ?, ?, ?);
            """,
            [
                (
                    f"Book {i:04d}",
                    json.dumps([f"Author {i%7}"]),
                    2000 + (i % 24),
                    depths[i % len(depths)],
                )
                for i in range(args.books)
            ],
        )
        conn.executemany(
            "INSERT INTO concepts (name) VALUES (?);",
            [(f"Concept {i:04d}",) for i in range(args.concepts)],
        )

        concept_ids = [
            row[0] for row in conn.execute("SELECT id FROM concepts;").fetchall()
        ]
        book_ids = [row[0] for row in conn.execute("SELECT id FROM books;").fetchall()]

        notes_payload = []
        note_concepts_payload = []
        book_concepts_payload = []
        for i in range(args.notes):
            concept_id = rng.choice(concept_ids)
            book_id = rng.choice(book_ids)
            notes_payload.append(
                (
                    f"Note {i:04d}",
                    f"Note {i:04d} body about Concept {concept_id}.",
                    book_id,
                    "standard",
                )
            )
        conn.executemany(
            """
            INSERT INTO notes (title, body, book_id, note_type)
            VALUES (?, ?, ?, ?);
            """,
            notes_payload,
        )

        note_ids = [row[0] for row in conn.execute("SELECT id FROM notes;").fetchall()]
        for note_id in note_ids:
            concept_id = rng.choice(concept_ids)
            note_concepts_payload.append((note_id, concept_id, "explicit"))
        conn.executemany(
            """
            INSERT INTO note_concepts (note_id, concept_id, source)
            VALUES (?, ?, ?);
            """,
            note_concepts_payload,
        )

        for book_id in book_ids:
            for _ in range(3):
                concept_id = rng.choice(concept_ids)
                book_concepts_payload.append((book_id, concept_id))
        conn.executemany(
            "INSERT INTO book_concepts (book_id, concept_id) VALUES (?, ?);",
            book_concepts_payload,
        )

    print("Benchmark dataset ready.")

    any_book_id = book_ids[0]
    any_depth = depths[0]
    any_term = "Concept"

    timed(
        "Books list",
        lambda: conn.execute(
            "SELECT id, title FROM books ORDER BY title LIMIT 100;"
        ).fetchall(),
    )
    timed(
        "Books by depth",
        lambda: conn.execute(
            "SELECT id, title FROM books WHERE depth = ? ORDER BY title;",
            (any_depth,),
        ).fetchall(),
    )
    timed(
        "Concepts by book",
        lambda: conn.execute(
            """
            SELECT c.id, c.name
            FROM concepts c
            JOIN book_concepts bc ON bc.concept_id = c.id
            WHERE bc.book_id = ?
            GROUP BY c.id
            ORDER BY c.name;
            """,
            (any_book_id,),
        ).fetchall(),
    )
    timed(
        "Notes search (FTS5)",
        lambda: conn.execute(
            "SELECT rowid FROM notes_fts WHERE notes_fts MATCH ? LIMIT 20;",
            (any_term,),
        ).fetchall(),
    )

    conn.close()


if __name__ == "__main__":
    main()
