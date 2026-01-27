from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db import connect, initialize  # noqa: E402


@pytest.fixture()
def db_conn(tmp_path: Path):
    db_path = tmp_path / "melvil.db"
    conn = connect(db_path)
    initialize(conn)
    try:
        yield conn
    finally:
        conn.close()
