"""Daily form dispatch (08:00 local) and monthly summary (1st @ 09:00 local)."""

from __future__ import annotations

import logging
from datetime import time

from telegram.ext import Application, ContextTypes

from .admin.i18n import bot_t
from .bot.forms import open_form_for_team
from .config import settings
from .db import connect
from .excel import XLSX_PATH
from .timeutils import now_local, tz

logger = logging.getLogger(__name__)


async def daily_dispatch(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send today's attendance form to every registered team lead."""
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT t.id AS team_id, t.name AS team_name, l.telegram_chat_id AS chat_id "
            "FROM teams t JOIN leads l ON l.team_id = t.id"
        ).fetchall()
    finally:
        conn.close()

    for r in rows:
        try:
            await open_form_for_team(
                context.bot, r["chat_id"], r["team_id"], r["team_name"]
            )
        except Exception:
            logger.exception(
                "Failed to send daily form to team %s (chat %s)",
                r["team_name"], r["chat_id"],
            )


async def monthly_summary(context: ContextTypes.DEFAULT_TYPE) -> None:
    """On the 1st of the month, DM the owner the workbook for the month that just ended."""
    now = now_local()
    if now.month == 1:
        year, month = now.year - 1, 12
    else:
        year, month = now.year, now.month - 1

    conn = connect()
    try:
        owner = conn.execute(
            "SELECT telegram_chat_id FROM owner LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    if not owner:
        logger.warning("Monthly summary skipped: no owner registered.")
        return
    if not XLSX_PATH.exists():
        logger.warning("Monthly summary skipped: %s does not exist.", XLSX_PATH)
        return

    with XLSX_PATH.open("rb") as f:
        await context.bot.send_document(
            chat_id=owner["telegram_chat_id"],
            document=f,
            filename=XLSX_PATH.name,
            caption=bot_t("bot.scheduler.monthly_caption", year=year, month=month),
        )


def setup_jobs(app: Application) -> None:
    h, m = (int(x) for x in settings.daily_send_time.split(":"))
    daily_t = time(h, m, tzinfo=tz())
    monthly_t = time(9, 0, tzinfo=tz())

    app.job_queue.run_daily(daily_dispatch, time=daily_t, name="daily_dispatch")
    app.job_queue.run_monthly(
        monthly_summary, when=monthly_t, day=1, name="monthly_summary"
    )
    logger.info(
        "Scheduled: daily_dispatch @ %s %s, monthly_summary @ day=1 %s %s",
        daily_t.strftime("%H:%M"), settings.tz,
        monthly_t.strftime("%H:%M"), settings.tz,
    )
