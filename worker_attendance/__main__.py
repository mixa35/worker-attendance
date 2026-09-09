"""Entrypoint: starts the Telegram bot, scheduler, and admin web app."""

from __future__ import annotations

import asyncio
import logging

import uvicorn
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from .admin.app import app as admin_app
from .bot.handlers import (
    help_handler,
    report_handler,
    start_handler,
    submit_handler,
    today_handler,
    toggle_handler,
)
from .bot.menu import install_command_menus
from .config import settings
from .db import init_db
from .scheduler import setup_jobs

logger = logging.getLogger(__name__)


async def _post_init(app):
    await install_command_menus(app)
    admin_app.state.bot_app = app  # let admin trigger menu refreshes after lead changes
    config = uvicorn.Config(
        admin_app,
        host=settings.admin_host,
        port=settings.admin_port,
        log_level="info",
        access_log=False,
    )
    server = uvicorn.Server(config)
    asyncio.create_task(server.serve())
    logger.info(
        "Admin web app started on http://%s:%s",
        settings.admin_host, settings.admin_port,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if not settings.bot_token:
        raise SystemExit(
            "BOT_TOKEN is not set. Copy .env.example to .env and fill it in."
        )

    init_db()

    app = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(_post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("today", today_handler))
    app.add_handler(CommandHandler("report", report_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CallbackQueryHandler(toggle_handler, pattern=r"^t:"))
    app.add_handler(CallbackQueryHandler(submit_handler, pattern=r"^s:"))

    setup_jobs(app)

    logger.info("Bot starting…")
    app.run_polling()


if __name__ == "__main__":
    main()
