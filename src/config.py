from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB_NAME = "melvil.db"


def default_db_path() -> Path:
    return Path.home() / ".melvil" / DEFAULT_DB_NAME


def resolve_db_path(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit)
    env_path = os.getenv("MELVIL_DB_PATH")
    if env_path:
        return Path(env_path)
    return default_db_path()
