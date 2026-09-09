"""Shared fixtures.

Both `db.DB_PATH` and `excel.XLSX_PATH` are module-level constants derived from
`settings.data_dir` at import time, so tests redirect them at the module object
rather than trying to re-import the package with a different environment.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from worker_attendance import db as db_module
from worker_attendance import excel as excel_module


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the DB and the workbook at a throwaway directory."""
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "attendance.db")
    monkeypatch.setattr(excel_module, "XLSX_PATH", tmp_path / "attendance.xlsx")
    return tmp_path


@pytest.fixture
def conn(data_dir: Path) -> sqlite3.Connection:
    """A migrated, empty database."""
    db_module.init_db()
    connection = db_module.connect()
    yield connection
    connection.close()


@pytest.fixture
def seeded(conn: sqlite3.Connection) -> sqlite3.Connection:
    """Two teams, three workers, one of them inactive.

    Alba   (red)  -> Ana (national id 01001), Beka (no national id)
    Bravo  (blue) -> Giorgi (inactive)
    """
    conn.execute("INSERT INTO teams(id, name, color_hex) VALUES (1, 'Alba', 'FF0000')")
    conn.execute("INSERT INTO teams(id, name, color_hex) VALUES (2, 'Bravo', '0000FF')")
    conn.execute(
        "INSERT INTO workers(id, team_id, name, national_id, active) "
        "VALUES (1, 1, 'Ana', '01001', 1)"
    )
    conn.execute(
        "INSERT INTO workers(id, team_id, name, national_id, active) "
        "VALUES (2, 1, 'Beka', NULL, 1)"
    )
    conn.execute(
        "INSERT INTO workers(id, team_id, name, national_id, active) "
        "VALUES (3, 2, 'Giorgi', NULL, 0)"
    )
    conn.commit()
    return conn


@pytest.fixture
def mark(seeded: sqlite3.Connection):
    """Record one attendance row: mark(worker_id, "2026-05-04", present=1)."""

    def _mark(worker_id: int, date_iso: str, present: int = 1) -> None:
        seeded.execute(
            "INSERT OR REPLACE INTO attendance(date, worker_id, present) "
            "VALUES (?, ?, ?)",
            (date_iso, worker_id, present),
        )
        seeded.commit()

    return _mark
