from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from src import db as melvil_db
from src.zotero import (
    create_book_from_zotero,
    find_item_by_title,
    map_item_type,
    resolve_zotero_db_path,
)


def _create_zotero_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "zotero.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT)"
    )
    conn.execute(
        "CREATE TABLE items (itemID INTEGER PRIMARY KEY, key TEXT, itemTypeID INTEGER)"
    )
    conn.execute(
        "CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT)"
    )
    conn.execute(
        "CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT)"
    )
    conn.execute(
        "CREATE TABLE itemData (itemID INTEGER, fieldID INTEGER, valueID INTEGER)"
    )
    conn.execute(
        "CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT)"
    )
    conn.execute(
        "CREATE TABLE itemCreators (itemID INTEGER, creatorID INTEGER, orderIndex INTEGER)"
    )

    conn.executemany(
        "INSERT INTO itemTypes (itemTypeID, typeName) VALUES (?, ?)",
        [(1, "book"), (2, "journalArticle"), (3, "bookSection")],
    )
    conn.executemany(
        "INSERT INTO fields (fieldID, fieldName) VALUES (?, ?)",
        [(1, "title"), (2, "date")],
    )

    def insert_value(value: str) -> int:
        cursor = conn.execute(
            "INSERT INTO itemDataValues (value) VALUES (?)",
            (value,),
        )
        return int(cursor.lastrowid)

    def add_item(
        *,
        item_id: int,
        key: str,
        item_type_id: int,
        title: str,
        date: str | None,
        creators: list[tuple[str, str]] | None = None,
    ) -> None:
        conn.execute(
            "INSERT INTO items (itemID, key, itemTypeID) VALUES (?, ?, ?)",
            (item_id, key, item_type_id),
        )
        title_id = insert_value(title)
        conn.execute(
            "INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?, ?, ?)",
            (item_id, 1, title_id),
        )
        if date is not None:
            date_id = insert_value(date)
            conn.execute(
                "INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?, ?, ?)",
                (item_id, 2, date_id),
            )
        if creators:
            for index, (first, last) in enumerate(creators):
                cursor = conn.execute(
                    "INSERT INTO creators (firstName, lastName) VALUES (?, ?)",
                    (first, last),
                )
                creator_id = int(cursor.lastrowid)
                conn.execute(
                    "INSERT INTO itemCreators (itemID, creatorID, orderIndex) VALUES (?, ?, ?)",
                    (item_id, creator_id, index),
                )

    add_item(
        item_id=1,
        key="REF1",
        item_type_id=2,
        title="Refactoring",
        date="1999",
        creators=[("Martin", "Fowler"), ("Kent", "Beck")],
    )
    add_item(
        item_id=2,
        key="REF2",
        item_type_id=3,
        title="Refactoring 2nd Edition",
        date="2018-01-01",
    )
    add_item(
        item_id=3,
        key="DEEP1",
        item_type_id=1,
        title="Deep Work",
        date="2016",
    )
    add_item(
        item_id=4,
        key="DEEP2",
        item_type_id=1,
        title="Deep Learning",
        date="2016",
    )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture()
def zotero_db(tmp_path: Path) -> Path:
    return _create_zotero_db(tmp_path)


def test_resolve_zotero_db_path_env_and_explicit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "explicit.sqlite"
    db_path.touch()

    assert resolve_zotero_db_path(db_path) == db_path

    env_path = tmp_path / "env.sqlite"
    env_path.touch()
    monkeypatch.setenv("ZOTERO_DB_PATH", str(env_path))
    assert resolve_zotero_db_path() == env_path


def test_find_item_by_title_exact_and_ambiguous(zotero_db: Path):
    conn = sqlite3.connect(zotero_db)
    conn.row_factory = sqlite3.Row

    item = find_item_by_title(conn, "Refactoring")
    assert item.title == "Refactoring"
    assert item.year == 1999

    with pytest.raises(ValueError, match="Ambiguous title"):
        find_item_by_title(conn, "Deep")

    conn.close()


def test_map_item_type_variants():
    assert map_item_type("journalArticle") == "paper"
    assert map_item_type("ConferencePaper") == "paper"
    assert map_item_type("bookSection") == "article"
    assert map_item_type("Book") == "book"


def test_create_book_from_zotero(zotero_db: Path, tmp_path: Path):
    melvil_path = tmp_path / "melvil.db"
    conn = melvil_db.connect(melvil_path)
    melvil_db.initialize(conn)

    created = create_book_from_zotero(
        conn,
        title="Refactoring",
        zotero_db_path=zotero_db,
    )

    assert created["title"] == "Refactoring"
    assert created["type"] == "paper"
    assert created["year"] == 1999

    authors = json.loads(created["authors"])
    assert authors == ["Martin Fowler", "Kent Beck"]
    assert created["zotero_key"] == "REF1"

    conn.close()
