# Worker Attendance — Telegram Bot + Admin Web

[![CI](https://github.com/mixa35/worker-attendance/actions/workflows/ci.yml/badge.svg)](https://github.com/mixa35/worker-attendance/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Deploy: Docker](https://img.shields.io/badge/deploy-docker%20compose-2496ED.svg)](docker-compose.yml)

Daily attendance tracking for a construction company with multiple field crews. Each morning at 08:00 (Asia/Tbilisi) every team lead receives a Telegram message with an inline form listing their workers; they tap to mark who showed up and submit. Results accumulate into a single Excel workbook with one sheet per month, color-coded per team. The owner can pull the workbook anytime via `/report`, and on the 1st of each month the previous month's workbook is auto-DM'd. Workers, teams, and leads are managed through a small bilingual (English / Georgian) admin web page.

The whole system runs as a single Python container on a free Oracle Cloud VM.

## Demo

- **Bot**: lead opens the daily form (`/today` or auto-sent at 08:00) → toggles ✅/⬜ per worker → Submit. Owner runs `/report` to get the live `attendance.xlsx`.
- **Admin** (`http://VM_IP:8000`): manage teams (with color picker), workers (drag-and-drop between teams), leads (with pending-invites inbox for new users who DM'd the bot), and the owner's chat ID. Bilingual EN / ქართული.

## Stack

| Layer | Tech |
|---|---|
| Bot framework | [`python-telegram-bot`](https://docs.python-telegram-bot.org/) v22 (async) |
| Web admin | [FastAPI](https://fastapi.tiangolo.com/) + Jinja2 templates + [SortableJS](https://sortablejs.github.io/Sortable/) (drag-drop) |
| Scheduler | `python-telegram-bot` JobQueue (APScheduler under the hood) |
| Storage | SQLite (single file, WAL mode) + persistent `attendance.xlsx` re-rendered on every submission |
| Excel | [openpyxl](https://openpyxl.readthedocs.io/) — one sheet per month, team-colored rows, atomic write via `os.replace` |
| Auth | HTTP Basic Auth on the admin (one user, env-configured password) |
| i18n | Per-language dicts in [`worker_attendance/admin/i18n.py`](worker_attendance/admin/i18n.py); language picked via cookie for the web, env var for the bot |
| Process | One container running bot polling, scheduler, and the FastAPI admin in the same asyncio event loop |
| Deploy | Docker Compose on an Oracle Cloud Always Free VM (Ubuntu 22.04, x86-64) |

## Architecture

```
┌──────────────────────── Telegram cloud ────────────────────────┐
│   Lead chats (one per team)             Owner chat              │
└──────────┬─────────────────────────────────────┬───────────────┘
           │ getUpdates / sendMessage            │
           ▼                                     ▼
┌──────────────────────── VM (Frankfurt) ────────────────────────┐
│  Single Python process (Docker container, restart=always)      │
│   ├─ python-telegram-bot polling + handlers                    │
│   ├─ JobQueue: 08:00 dispatch, monthly summary on day 1        │
│   └─ FastAPI admin on :8000 (sidebar nav, drag-drop, bilingual)│
│                                                                 │
│  Persistent volume → ./data                                     │
│   ├─ attendance.db   (SQLite, WAL)                              │
│   ├─ attendance.xlsx (live workbook, atomic writes)             │
│   └─ seed.yaml       (initial teams/workers, optional)          │
└────────────────────────────────────────────────────────────────┘
              │ nightly cron 03:15
              ▼
       ~/backups/<date>/  (db + xlsx, 30-day rolling)
```

## Data model

```
teams(id, name, color_hex)
workers(id, team_id → teams, name, national_id?, active)
leads(id, team_id → teams, telegram_chat_id, name?)
attendance(date, worker_id → workers, present)   PK (date, worker_id)
form_state(team_id, date, worker_id, present)    -- draft until Submit
submissions(team_id, date, submitted_at, lead_chat_id)
owner(telegram_chat_id)
pending_leads(telegram_chat_id PK, first_name, last_name, username, …)
schema_version(version, applied_at)
```

Migrations live as numbered SQL files in [`worker_attendance/migrations/`](worker_attendance/migrations/) and apply automatically on startup.

## Local development

```bash
git clone <this-repo>
cd worker-attendance
python -m venv .venv
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -r requirements.lock
pip install --no-deps -e .

cp .env.example .env
# Fill BOT_TOKEN, OWNER_CHAT_ID, ADMIN_PASSWORD
cp data/seed.example.yaml data/seed.yaml
# Edit teams, workers, lead chat IDs

python -m worker_attendance.seed     # one-time DB seed
python -m worker_attendance   # starts bot + admin
```

Admin opens at `http://localhost:8000` (login: `admin` / `$ADMIN_PASSWORD`).

## Tests

```bash
pip install -e ".[dev]"
python -m pytest -q          # 19 tests
```

The suite covers the two things that would corrupt the owner's report without
anyone noticing:

- **Migrations** ([`tests/test_db.py`](tests/test_db.py)) — every numbered migration applies
  exactly once, re-running `init_db()` is a no-op, foreign keys are actually enforced
  (without the `PRAGMA` the cascade deletes silently do nothing), the partial unique index on
  `national_id` rejects duplicates while still allowing many NULLs, and `attendance` really is
  keyed by `(date, worker_id)`.
- **Workbook rendering** ([`tests/test_excel.py`](tests/test_excel.py)) — day columns match the
  length of the month (including a leap February), present days are marked and totalled,
  attendance from an adjacent month is not counted, `render_month_sheet` is idempotent as
  documented, each month gets its own sheet, the `national_id` fallback to `#<row id>` works,
  an inactive worker appears only in months where they have history, and the atomic write
  leaves no `.tmp` file behind.

CI runs the suite on Python 3.11 (what the container runs) and 3.12, and separately builds the
deployment image so a stale `requirements.lock` fails loudly instead of at deploy time.

## Production deployment (Docker)

```bash
cp .env.example .env  # fill in
cp data/seed.example.yaml data/seed.yaml  # fill in (or skip and use admin UI)
docker compose run --rm app python -m worker_attendance.seed   # one-time
docker compose up -d --build
```

Container has `restart: unless-stopped` and a `/healthz` HEALTHCHECK so Docker auto-restarts it on crashes or VM reboots. Port 8000 exposed.

For the Oracle Cloud setup specifically, open ports 22 + 8000 in the security list, install Docker via `apt`, allow port 8000 in `iptables`, persist with `netfilter-persistent save`.

## Configuration

Everything via environment (loaded from `.env`):

| Var | Default | Notes |
|---|---|---|
| `BOT_TOKEN` | — | From [@BotFather](https://t.me/BotFather) on Telegram |
| `OWNER_CHAT_ID` | `0` | Auto-discovered: send any message to the bot, it replies with your chat ID |
| `ADMIN_PASSWORD` | — | For the admin web page (Basic Auth, user is always `admin`) |
| `TZ` | `Asia/Tbilisi` | Timezone for daily/monthly schedules |
| `DAILY_SEND_TIME` | `08:00` | Local time the morning form fires |
| `BOT_LANG` | `ka` | `en` or `ka` — language of all bot-side messages |
| `DATA_DIR` | `/data` (in container) | SQLite + Excel + seed files location |
| `ADMIN_HOST` / `ADMIN_PORT` | `0.0.0.0` / `8000` | FastAPI bind |

## Admin web page

Sidebar layout, brand-aligned palette (dark navy + emerald accent). Pages:

- **Dashboard** — counts of teams / active workers / leads, owner chat ID, Excel download
- **Teams** — add / rename / recolor (HTML5 color picker) / delete (blocked if team has workers)
- **Workers** — per-team tables with drag-and-drop between teams, deactivate / reactivate, delete (blocked if any attendance history)
- **Leads** — pending-invites inbox + assign-to-team flow, edit existing leads (replace chat ID without recreating)
- **Owner** — set the owner's Telegram chat ID

Language switch in the sidebar footer (cookie-based, applies instantly).

## Bot commands

| Role | Command | Effect |
|---|---|---|
| Lead | `/today`, `/start` | Open today's attendance form |
| Lead | (taps) | Toggle ✅/⬜ per worker |
| Lead | (Submit button) | Save attendance, re-render Excel |
| Owner | `/report`, `/start` | DM the live `attendance.xlsx` |
| Anyone | `/help` | Role-aware command list |
| Unknown | `/start` | Bot records them as "pending"; owner gets a DM with a 6h cooldown |

## Operational notes

- **Backups**: nightly `~/worker-attendance/backup.sh` cron at 03:15 copies `data/*` to `~/backups/<date>/`, keeps 30 days. Off-VM backup deferred (Backblaze B2 candidate).
- **Logs**: container logs capped at 10 MB × 3 files via Docker logging options.
- **Healthcheck**: `/healthz` pings SQLite. Docker `HEALTHCHECK` polls every 60s.
- **Atomicity**: SQLite in WAL mode; Excel re-renders write to `.tmp` then `os.replace`.

## Known limitations / planned

- Workers belong to a single team at a time. Mid-month transfer re-attributes the whole month in the Excel display. A `worker_team_history` table is the cleaner fix; deferred until transfers become frequent.
- Admin is plain HTTP. Adding [Caddy](https://caddyserver.com/) + DuckDNS for free auto-HTTPS is on the roadmap.
- Admin auth is Basic Auth; CSRF protection requires migrating to session cookies (planned).
- Bot UI is global-language (one `BOT_LANG` for everyone). Per-lead preference would be a small `leads.language` column when multi-language teams emerge.

## Project layout

```
worker_attendance/
├── __main__.py        # entrypoint: starts bot + scheduler + admin in one event loop
├── config.py          # env loading via pydantic-settings
├── db.py              # SQLite connection + migrations runner
├── seed.py            # YAML → DB bootstrap
├── excel.py           # render_month_sheet — atomic openpyxl write
├── scheduler.py       # daily 08:00 dispatch, monthly day-1 summary
├── timeutils.py       # tz helpers
├── bot/
│   ├── handlers.py    # /start, /today, /report, /help, callbacks
│   ├── forms.py       # InlineKeyboardMarkup builder + form state
│   └── menu.py        # per-chat command-menu installer
├── admin/
│   ├── app.py         # FastAPI routes + auth + healthz + static mount
│   ├── i18n.py        # EN / KA dicts; bot_t() helper
│   ├── static/        # Sortable.min.js, favicon.svg
│   └── templates/     # Jinja2 templates (sidebar layout)
└── migrations/
    ├── 001_init.sql
    ├── 002_form_state.sql
    ├── 003_national_id.sql
    └── 004_pending_leads.sql

tests/
├── conftest.py        # tmp-dir DB + workbook fixtures
├── test_db.py         # migrations, constraints, cascades
└── test_excel.py      # month rendering, totals, idempotency

.github/workflows/
└── ci.yml             # pytest on 3.11 + 3.12, plus a docker build
```

## License

[MIT](LICENSE).
