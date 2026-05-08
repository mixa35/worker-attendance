"""Loads data/seed.yaml into the DB. Run: python -m src.seed [--force]."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .config import settings
from .db import connect, init_db


def load_seed(seed_path: Path, force: bool) -> None:
    if not seed_path.exists():
        sys.exit(f"seed file not found: {seed_path}")
    with seed_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    init_db()
    conn = connect()
    try:
        existing = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
        if existing and not force:
            sys.exit(
                f"DB already has {existing} team(s). Re-run with --force to wipe and reload."
            )
        if force:
            conn.executescript(
                "DELETE FROM submissions;"
                "DELETE FROM attendance;"
                "DELETE FROM leads;"
                "DELETE FROM workers;"
                "DELETE FROM teams;"
                "DELETE FROM owner;"
            )

        owner_id = data.get("owner_chat_id")
        if owner_id:
            conn.execute(
                "INSERT INTO owner(telegram_chat_id) VALUES (?)", (int(owner_id),)
            )

        for team in data.get("teams", []):
            cur = conn.execute(
                "INSERT INTO teams(name, color_hex) VALUES (?, ?)",
                (team["name"], team.get("color_hex", "CCCCCC")),
            )
            team_id = cur.lastrowid
            lead = team.get("lead") or {}
            if lead.get("telegram_chat_id"):
                conn.execute(
                    "INSERT INTO leads(team_id, telegram_chat_id, name) VALUES (?, ?, ?)",
                    (team_id, int(lead["telegram_chat_id"]), lead.get("name")),
                )
            for worker_entry in team.get("workers", []) or []:
                if isinstance(worker_entry, str):
                    worker_name = worker_entry
                    national_id = None
                else:
                    worker_name = worker_entry["name"]
                    national_id = worker_entry.get("national_id")
                    if national_id is not None:
                        national_id = str(national_id).strip() or None
                conn.execute(
                    "INSERT INTO workers(team_id, name, national_id) "
                    "VALUES (?, ?, ?)",
                    (team_id, worker_name, national_id),
                )
        conn.commit()
        print(f"Seeded from {seed_path}")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the attendance DB from a YAML file.")
    parser.add_argument(
        "--seed-file",
        default=str(Path(settings.data_dir) / "seed.yaml"),
        help="Path to seed YAML (default: <data_dir>/seed.yaml).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Wipe all data first (irreversible).",
    )
    args = parser.parse_args()
    load_seed(Path(args.seed_file), args.force)


if __name__ == "__main__":
    main()
