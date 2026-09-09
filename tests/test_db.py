"""Migration runner and schema guarantees."""

from __future__ import annotations

import sqlite3

import pytest

from worker_attendance import db as db_module


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    return {row["name"] for row in rows}


def test_init_db_creates_the_expected_schema(conn: sqlite3.Connection) -> None:
    assert {
        "teams",
        "workers",
        "leads",
        "attendance",
        "submissions",
        "owner",
        "form_state",
        "pending_leads",
    } <= _tables(conn)


def test_init_db_applies_every_migration_once(conn: sqlite3.Connection) -> None:
    expected = {version for version, _ in db_module._migration_files()}
    applied = {
        row["version"] for row in conn.execute("SELECT version FROM schema_version")
    }
    assert applied == expected
    assert expected, "no migrations were discovered"


def test_init_db_is_idempotent(conn: sqlite3.Connection) -> None:
    """Re-running migrations on a live database must not raise or re-apply."""
    before = conn.execute("SELECT version, applied_at FROM schema_version").fetchall()
    db_module.init_db()
    db_module.init_db()
    after = conn.execute("SELECT version, applied_at FROM schema_version").fetchall()
    assert [tuple(r) for r in before] == [tuple(r) for r in after]


def test_foreign_keys_are_enforced(conn: sqlite3.Connection) -> None:
    """Without PRAGMA foreign_keys the cascade deletes silently do nothing."""
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO workers(team_id, name) VALUES (999, 'Nobody')")


def test_deleting_a_team_cascades_to_its_workers(seeded: sqlite3.Connection) -> None:
    seeded.execute("DELETE FROM teams WHERE id = 1")
    seeded.commit()
    remaining = seeded.execute("SELECT id FROM workers").fetchall()
    assert [row["id"] for row in remaining] == [3]


def test_national_id_is_unique_but_optional(seeded: sqlite3.Connection) -> None:
    """The partial index must reject duplicates while allowing many NULLs."""
    seeded.execute(
        "INSERT INTO workers(team_id, name, national_id) VALUES (1, 'Nino', NULL)"
    )
    seeded.execute(
        "INSERT INTO workers(team_id, name, national_id) VALUES (1, 'Dato', NULL)"
    )
    seeded.commit()

    with pytest.raises(sqlite3.IntegrityError):
        seeded.execute(
            "INSERT INTO workers(team_id, name, national_id) "
            "VALUES (1, 'Impostor', '01001')"
        )


def test_attendance_is_keyed_by_date_and_worker(seeded: sqlite3.Connection) -> None:
    seeded.execute(
        "INSERT INTO attendance(date, worker_id, present) VALUES ('2026-05-04', 1, 1)"
    )
    seeded.commit()
    with pytest.raises(sqlite3.IntegrityError):
        seeded.execute(
            "INSERT INTO attendance(date, worker_id, present) "
            "VALUES ('2026-05-04', 1, 0)"
        )
