"""Registers the Telegram command menu (the '/' button) per chat role."""

from __future__ import annotations

import logging

from telegram import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from telegram.ext import Application

from ..db import connect

logger = logging.getLogger(__name__)


async def install_command_menus(app: Application) -> None:
    """Set the command menu shown by Telegram clients, scoped per chat role."""
    await app.bot.set_my_commands(
        [BotCommand("start", "Begin")],
        scope=BotCommandScopeDefault(),
    )

    conn = connect()
    try:
        leads = conn.execute("SELECT telegram_chat_id FROM leads").fetchall()
        owner_row = conn.execute(
            "SELECT telegram_chat_id FROM owner LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    lead_ids = {r["telegram_chat_id"] for r in leads}
    owner_id = owner_row["telegram_chat_id"] if owner_row else None

    targets = set(lead_ids)
    if owner_id is not None:
        targets.add(owner_id)

    for chat_id in targets:
        cmds: list[BotCommand] = []
        if chat_id in lead_ids:
            cmds.append(BotCommand("today", "Open today's attendance form"))
        if chat_id == owner_id:
            cmds.append(BotCommand("report", "Get the current attendance.xlsx"))
        cmds.append(BotCommand("help", "Show available commands"))
        cmds.append(BotCommand("start", "Begin"))
        try:
            await app.bot.set_my_commands(
                cmds, scope=BotCommandScopeChat(chat_id=chat_id)
            )
        except Exception:
            logger.exception("Failed to set command menu for chat %s", chat_id)
