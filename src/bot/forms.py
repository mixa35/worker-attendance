"""Builds the daily attendance form and helpers to load/initialize its state."""

from __future__ import annotations

from sqlite3 import Connection

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from ..admin.i18n import bot_t
from ..db import connect
from ..timeutils import today_iso

PRESENT_ICON = "✅"
ABSENT_ICON = "⬜"


def build_keyboard(workers_with_state, date_iso: str) -> InlineKeyboardMarkup:
    """workers_with_state: iterable of (worker_id, name, present)."""
    rows = []
    for worker_id, name, present in workers_with_state:
        icon = PRESENT_ICON if present else ABSENT_ICON
        rows.append(
            [
                InlineKeyboardButton(
                    f"{icon} {name}", callback_data=f"t:{worker_id}:{date_iso}"
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                bot_t("bot.form.submit"), callback_data=f"s:{date_iso}"
            )
        ]
    )
    return InlineKeyboardMarkup(rows)


def initialize_form_state(conn: Connection, team_id: int, date_iso: str) -> None:
    """Ensure a form_state row exists for every active worker in the team for date.

    If attendance was already submitted that day, mirror those values so re-opening
    the form lets the lead correct individual entries (same-day late edits).
    """
    workers = conn.execute(
        "SELECT id FROM workers WHERE team_id = ? AND active = 1", (team_id,)
    ).fetchall()
    for w in workers:
        att = conn.execute(
            "SELECT present FROM attendance WHERE worker_id = ? AND date = ?",
            (w["id"], date_iso),
        ).fetchone()
        default_present = att["present"] if att else 0
        conn.execute(
            "INSERT INTO form_state(team_id, date, worker_id, present) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(team_id, date, worker_id) DO NOTHING",
            (team_id, date_iso, w["id"], default_present),
        )


def fetch_form_state(conn: Connection, team_id: int, date_iso: str):
    return conn.execute(
        "SELECT fs.worker_id, w.name, fs.present "
        "FROM form_state fs JOIN workers w ON w.id = fs.worker_id "
        "WHERE fs.team_id = ? AND fs.date = ? "
        "ORDER BY w.name",
        (team_id, date_iso),
    ).fetchall()


async def open_form_for_team(
    bot: Bot, chat_id: int, team_id: int, team_name: str
) -> None:
    """Send a fresh attendance form for today to the given chat."""
    date_iso = today_iso()
    conn = connect()
    try:
        initialize_form_state(conn, team_id, date_iso)
        conn.commit()
        rows = fetch_form_state(conn, team_id, date_iso)
    finally:
        conn.close()

    keyboard = build_keyboard(
        [(r["worker_id"], r["name"], r["present"]) for r in rows], date_iso
    )
    await bot.send_message(
        chat_id=chat_id,
        text=bot_t("bot.form.title", team_name=team_name, date=date_iso),
        reply_markup=keyboard,
        parse_mode="Markdown",
    )
