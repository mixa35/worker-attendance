# Worker Attendance Tracker

Telegram bot that lets construction team leads mark daily worker attendance. Data lives in SQLite; one persistent `attendance.xlsx` is updated on each submission with a sheet per month and color-coded rows per team. Includes a small FastAPI admin page (Basic Auth) and a YAML seed file as alternative ways to manage workers/teams.

## Stack
Python 3.11+ · `python-telegram-bot` · `openpyxl` · `FastAPI` · `APScheduler` · SQLite. Single process. Runs on Oracle Cloud Always Free VM.

## Run
- Copy `.env.example` → `.env` and fill `BOT_TOKEN`, `OWNER_CHAT_ID`, `ADMIN_PASSWORD`.
- First run: `python -m src.seed` to load `data/seed.yaml`.
- `docker compose up -d` (or `python -m src` for local dev).

## Key files
[src/__main__.py](src/__main__.py) · [src/db.py](src/db.py) · [src/excel.py](src/excel.py) · [src/bot/handlers.py](src/bot/handlers.py) · [src/admin/app.py](src/admin/app.py)

## Known limitation
Workers belong to one team at a time (no per-day team history). Moving a worker mid-month re-attributes their entire month's attendance to the new team in the Excel report. Plan transfers at month boundaries. Deeper fix (worker_team_history table) deferred.
