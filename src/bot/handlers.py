"""Telegram command and callback handlers."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from ..admin.i18n import bot_t
from ..db import connect
from ..excel import XLSX_PATH, render_month_sheet
from ..timeutils import now_local, today_iso
from .forms import build_keyboard, fetch_form_state, open_form_for_team

logger = logging.getLogger(__name__)

OWNER_NOTIFY_COOLDOWN_SECONDS = 6 * 3600


def _record_pending_lead(
    chat_id: int,
    first_name: str | None,
    last_name: str | None,
    username: str | None,
) -> bool:
    """Insert/update pending_leads row. Returns True if owner should be notified now."""
    now_dt = now_local()
    now_iso = now_dt.isoformat(timespec="seconds")
    conn = connect()
    try:
        existing = conn.execute(
            "SELECT last_owner_notified_at FROM pending_leads WHERE telegram_chat_id = ?",
            (chat_id,),
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE pending_leads SET last_seen_at = ?, "
                "    first_name = COALESCE(?, first_name), "
                "    last_name  = COALESCE(?, last_name), "
                "    username   = COALESCE(?, username) "
                "WHERE telegram_chat_id = ?",
                (now_iso, first_name, last_name, username, chat_id),
            )
            last_notified = existing["last_owner_notified_at"]
            if not last_notified:
                should_notify = True
            else:
                try:
                    last_dt = datetime.fromisoformat(last_notified)
                    should_notify = (
                        now_dt - last_dt
                    ).total_seconds() > OWNER_NOTIFY_COOLDOWN_SECONDS
                except ValueError:
                    should_notify = True
        else:
            conn.execute(
                "INSERT INTO pending_leads("
                "  telegram_chat_id, first_name, last_name, username, "
                "  first_seen_at, last_seen_at"
                ") VALUES (?, ?, ?, ?, ?, ?)",
                (chat_id, first_name, last_name, username, now_iso, now_iso),
            )
            should_notify = True

        if should_notify:
            conn.execute(
                "UPDATE pending_leads SET last_owner_notified_at = ? "
                "WHERE telegram_chat_id = ?",
                (now_iso, chat_id),
            )
        conn.commit()
    finally:
        conn.close()
    return should_notify


async def _notify_owner_pending(
    bot,
    chat_id: int,
    first_name: str | None,
    last_name: str | None,
    username: str | None,
) -> None:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT telegram_chat_id FROM owner LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return
    name = " ".join(p for p in (first_name, last_name) if p) or "(no name)"
    handle = f"@{username}\n" if username else ""
    text = bot_t(
        "bot.owner_pending_notif", name=name, handle=handle, chat_id=chat_id
    )
    try:
        await bot.send_message(
            chat_id=row["telegram_chat_id"], text=text, parse_mode="Markdown"
        )
    except Exception:
        logger.exception("Failed to DM owner about pending user")


def _lookup_lead(chat_id: int):
    conn = connect()
    try:
        return conn.execute(
            "SELECT l.team_id, t.name AS team_name "
            "FROM leads l JOIN teams t ON t.id = l.team_id "
            "WHERE l.telegram_chat_id = ?",
            (chat_id,),
        ).fetchone()
    finally:
        conn.close()


def _is_owner(chat_id: int) -> bool:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT 1 FROM owner WHERE telegram_chat_id = ?", (chat_id,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    lead = _lookup_lead(chat_id)
    if lead:
        await open_form_for_team(
            context.bot, chat_id, lead["team_id"], lead["team_name"]
        )
        return
    if _is_owner(chat_id):
        await update.message.reply_text(bot_t("bot.owner_mode"))
        return

    user = update.effective_user
    fn = user.first_name if user else None
    ln = user.last_name if user else None
    un = user.username if user else None
    notify = _record_pending_lead(chat_id, fn, ln, un)

    await update.message.reply_text(bot_t("bot.unknown_user"))

    if notify:
        await _notify_owner_pending(context.bot, chat_id, fn, ln, un)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    lead = _lookup_lead(chat_id)
    is_owner = _is_owner(chat_id)

    lines: list[str] = []
    if lead:
        lines.append(bot_t("bot.help.lead_header"))
        lines.append(bot_t("bot.help.today"))
        lines.append(bot_t("bot.help.today_note"))
        lines.append("")
    if is_owner:
        lines.append(bot_t("bot.help.owner_header"))
        lines.append(bot_t("bot.help.report"))
        lines.append(bot_t("bot.help.report_note"))
        lines.append("")
    if not lead and not is_owner:
        lines.append(bot_t("bot.help.unknown"))
        lines.append(bot_t("bot.help.your_id", chat_id=chat_id))
        lines.append(bot_t("bot.help.contact_admin"))
    else:
        lines.append(bot_t("bot.help.help_cmd"))
        lines.append(bot_t("bot.help.start_cmd"))

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    lead = _lookup_lead(chat_id)
    if not lead:
        await update.message.reply_text(bot_t("bot.today.not_lead"))
        return
    await open_form_for_team(
        context.bot, chat_id, lead["team_id"], lead["team_name"]
    )


async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not _is_owner(chat_id):
        await update.message.reply_text(bot_t("bot.report.owner_only"))
        return
    if not XLSX_PATH.exists():
        await update.message.reply_text(bot_t("bot.report.empty"))
        return
    with XLSX_PATH.open("rb") as f:
        await context.bot.send_document(
            chat_id=chat_id,
            document=f,
            filename=XLSX_PATH.name,
            caption=bot_t(
                "bot.report.caption",
                timestamp=f"{now_local():%Y-%m-%d %H:%M}",
            ),
        )


async def toggle_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat_id = update.effective_chat.id
    lead = _lookup_lead(chat_id)
    if not lead:
        await query.answer(bot_t("bot.form.not_lead"), show_alert=True)
        return

    parts = query.data.split(":")
    if len(parts) != 3:
        await query.answer()
        return
    _, worker_id_str, date_iso = parts
    if date_iso != today_iso():
        await query.answer(bot_t("bot.form.expired"), show_alert=True)
        return
    worker_id = int(worker_id_str)

    conn = connect()
    try:
        row = conn.execute(
            "SELECT present FROM form_state "
            "WHERE team_id = ? AND date = ? AND worker_id = ?",
            (lead["team_id"], date_iso, worker_id),
        ).fetchone()
        if not row:
            await query.answer(bot_t("bot.form.not_in_form"), show_alert=True)
            return
        new_present = 0 if row["present"] else 1
        conn.execute(
            "UPDATE form_state SET present = ? "
            "WHERE team_id = ? AND date = ? AND worker_id = ?",
            (new_present, lead["team_id"], date_iso, worker_id),
        )
        conn.commit()
        rows = fetch_form_state(conn, lead["team_id"], date_iso)
    finally:
        conn.close()

    keyboard = build_keyboard(
        [(r["worker_id"], r["name"], r["present"]) for r in rows], date_iso
    )
    try:
        await query.edit_message_reply_markup(reply_markup=keyboard)
    except Exception:
        logger.debug("edit_message_reply_markup failed (likely unchanged)", exc_info=True)
    await query.answer()


async def submit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat_id = update.effective_chat.id
    lead = _lookup_lead(chat_id)
    if not lead:
        await query.answer(bot_t("bot.form.not_lead"), show_alert=True)
        return

    parts = query.data.split(":")
    if len(parts) != 2:
        await query.answer()
        return
    _, date_iso = parts
    if date_iso != today_iso():
        await query.answer(bot_t("bot.form.expired"), show_alert=True)
        return

    submitted_at = now_local().isoformat(timespec="seconds")

    conn = connect()
    try:
        rows = conn.execute(
            "SELECT worker_id, present FROM form_state "
            "WHERE team_id = ? AND date = ?",
            (lead["team_id"], date_iso),
        ).fetchall()
        for r in rows:
            conn.execute(
                "INSERT INTO attendance(date, worker_id, present) VALUES (?, ?, ?) "
                "ON CONFLICT(date, worker_id) DO UPDATE SET present = excluded.present",
                (date_iso, r["worker_id"], r["present"]),
            )
        conn.execute(
            "INSERT INTO submissions(team_id, date, submitted_at, lead_chat_id) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(team_id, date) DO UPDATE SET "
            "submitted_at = excluded.submitted_at, "
            "lead_chat_id = excluded.lead_chat_id",
            (lead["team_id"], date_iso, submitted_at, chat_id),
        )
        present_count = sum(1 for r in rows if r["present"])
        total = len(rows)
        conn.commit()
    finally:
        conn.close()

    year, month = int(date_iso[:4]), int(date_iso[5:7])
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, render_month_sheet, year, month)
    except Exception:
        logger.exception("Excel re-render failed for %s-%s", year, month)

    await query.edit_message_text(
        bot_t(
            "bot.submit.confirmation",
            team_name=lead["team_name"],
            date=date_iso,
            present=present_count,
            total=total,
        ),
        parse_mode="Markdown",
    )
    await query.answer(bot_t("bot.form.saved_alert"))
