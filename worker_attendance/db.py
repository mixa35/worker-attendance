"""SQLite connection, migrations runner, and helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import settings

DB_PATH = Path(settings.data_dir) / "attendance.db"
_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _migration_files() -> list[tuple[int, Path]]:
    out: list[tuple[int, Path]] = []
    for path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        prefix = path.name.split("_", 1)[0]
        if not prefix.isdigit():
            continue
        out.append((int(prefix), path))
    return out


def init_db() -> None:
    """Apply pending SQL migrations in order. Idempotent."""
    conn = connect()
    try:
        conn.executescript(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "version INTEGER PRIMARY KEY,"
            "applied_at TEXT NOT NULL DEFAULT (datetime('now'))"
            ")"
        )
        applied = {
            row["version"] for row in conn.execute("SELECT version FROM schema_version")
        }
        for version, path in _migration_files():
            if version in applied:
                continue
            conn.executescript(path.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT OR IGNORE INTO schema_version(version) VALUES (?)", (version,)
            )
            conn.commit()
    finally:
        conn.close()
