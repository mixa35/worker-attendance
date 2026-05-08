"""FastAPI admin app — Basic Auth, swappable to session+bcrypt later."""

from __future__ import annotations

import logging
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..config import settings
from ..db import connect
from ..excel import XLSX_PATH
from .i18n import LANGS, bot_t, get_lang, make_t

logger = logging.getLogger(__name__)

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
STATIC_DIR = Path(__file__).parent / "static"

security = HTTPBasic()


def _auth(creds: HTTPBasicCredentials = Depends(security)) -> str:
    user_ok = secrets.compare_digest(creds.username, "admin")
    pw_ok = secrets.compare_digest(creds.password, settings.admin_password or "")
    if not (user_ok and pw_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bad credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return creds.username


app = FastAPI(title="Worker Attendance Admin", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(str(STATIC_DIR / "favicon.svg"), media_type="image/svg+xml")


@app.get("/healthz", include_in_schema=False)
async def healthz():
    """Simple liveness probe — verifies the SQLite DB is reachable."""
    try:
        c = connect()
        try:
            c.execute("SELECT 1").fetchone()
        finally:
            c.close()
    except Exception:
        raise HTTPException(status_code=503, detail="db unreachable")
    return {"status": "ok"}


router = APIRouter(dependencies=[Depends(_auth)])


def _ctx(request: Request, **extra) -> dict:
    """Build the standard template context — language + translations always present."""
    lang = get_lang(request)
    return {"lang": lang, "t": make_t(lang), **extra}


async def _refresh_bot_menus(request: Request) -> None:
    """Reapply per-chat command menus after a lead change. No-op if bot not attached."""
    bot_app = getattr(request.app.state, "bot_app", None)
    if bot_app is None:
        return
    try:
        from ..bot.menu import install_command_menus
        await install_command_menus(bot_app)
    except Exception:
        logger.exception("Failed to refresh bot command menus")


# ============================================================
# Language switch (not auth-protected so the login page works)
# ============================================================

@app.get("/set-lang")
async def set_lang(lang: str, request: Request):
    target = lang if lang in LANGS else "en"
    referer = request.headers.get("referer", "/")
    resp = RedirectResponse(url=referer, status_code=303)
    resp.set_cookie("lang", target, max_age=60 * 60 * 24 * 365, samesite="lax")
    return resp


# ============================================================
# Dashboard
# ============================================================

@router.get("/")
async def index(request: Request, msg: str | None = None):
    conn = connect()
    try:
        teams = conn.execute("SELECT COUNT(*) AS c FROM teams").fetchone()["c"]
        workers_active = conn.execute(
            "SELECT COUNT(*) AS c FROM workers WHERE active = 1"
        ).fetchone()["c"]
        workers_total = conn.execute("SELECT COUNT(*) AS c FROM workers").fetchone()["c"]
        leads = conn.execute("SELECT COUNT(*) AS c FROM leads").fetchone()["c"]
        owner = conn.execute(
            "SELECT telegram_chat_id FROM owner LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(
        request,
        "index.html",
        _ctx(
            request,
            teams_count=teams,
            workers_active=workers_active,
            workers_total=workers_total,
            leads_count=leads,
            owner_chat_id=owner["telegram_chat_id"] if owner else None,
            xlsx_exists=XLSX_PATH.exists(),
            msg=msg,
        ),
    )


# ============================================================
# Teams
# ============================================================

def _normalize_color(raw: str) -> str | None:
    val = (raw or "").strip().lstrip("#").upper()
    if len(val) != 6 or any(c not in "0123456789ABCDEF" for c in val):
        return None
    return val


@router.get("/teams")
async def teams_page(request: Request, msg: str | None = None):
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT t.id, t.name, t.color_hex, "
            "       (SELECT COUNT(*) FROM workers w WHERE w.team_id = t.id AND w.active = 1) AS active_count "
            "FROM teams t ORDER BY t.id"
        ).fetchall()
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(
        request, "teams.html", _ctx(request, teams=rows, msg=msg)
    )


@router.post("/teams/add")
async def teams_add(name: str = Form(...), color_hex: str = Form("CCCCCC")):
    name = name.strip()
    color = _normalize_color(color_hex)
    if not name:
        return RedirectResponse(url="/teams?msg=name_required", status_code=303)
    if color is None:
        return RedirectResponse(url="/teams?msg=invalid_color", status_code=303)
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO teams(name, color_hex) VALUES (?, ?)", (name, color)
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/teams?msg=team_added", status_code=303)


@router.post("/teams/{team_id}/edit")
async def teams_edit(
    team_id: int, name: str = Form(...), color_hex: str = Form(...)
):
    name = name.strip()
    color = _normalize_color(color_hex)
    if not name:
        return RedirectResponse(url="/teams?msg=name_required", status_code=303)
    if color is None:
        return RedirectResponse(url="/teams?msg=invalid_color", status_code=303)
    conn = connect()
    try:
        conn.execute(
            "UPDATE teams SET name = ?, color_hex = ? WHERE id = ?",
            (name, color, team_id),
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/teams?msg=team_updated", status_code=303)


@router.post("/teams/{team_id}/delete")
async def teams_delete(team_id: int):
    conn = connect()
    try:
        worker_count = conn.execute(
            "SELECT COUNT(*) AS c FROM workers WHERE team_id = ?", (team_id,)
        ).fetchone()["c"]
        if worker_count > 0:
            return RedirectResponse(
                url="/teams?msg=team_has_workers", status_code=303
            )
        conn.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/teams?msg=team_deleted", status_code=303)


# ============================================================
# Workers
# ============================================================

@router.get("/workers")
async def workers_page(request: Request, msg: str | None = None):
    conn = connect()
    try:
        teams = conn.execute("SELECT id, name, color_hex FROM teams ORDER BY id").fetchall()
        workers_by_team = {}
        for team in teams:
            ws = conn.execute(
                "SELECT id, name, national_id, active FROM workers "
                "WHERE team_id = ? ORDER BY active DESC, name",
                (team["id"],),
            ).fetchall()
            workers_by_team[team["id"]] = ws
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(
        request,
        "workers.html",
        _ctx(request, teams=teams, workers_by_team=workers_by_team, msg=msg),
    )


@router.post("/workers/add")
async def workers_add(
    team_id: int = Form(...),
    name: str = Form(...),
    national_id: str = Form(""),
):
    name = name.strip()
    nid = national_id.strip() or None
    if not name:
        return RedirectResponse(url="/workers?msg=name_required", status_code=303)
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO workers(team_id, name, national_id) VALUES (?, ?, ?)",
            (team_id, name, nid),
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/workers?msg=worker_added", status_code=303)


@router.post("/workers/{worker_id}/deactivate")
async def workers_deactivate(worker_id: int):
    conn = connect()
    try:
        conn.execute("UPDATE workers SET active = 0 WHERE id = ?", (worker_id,))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/workers?msg=worker_deactivated", status_code=303)


@router.post("/workers/{worker_id}/activate")
async def workers_activate(worker_id: int):
    conn = connect()
    try:
        conn.execute("UPDATE workers SET active = 1 WHERE id = ?", (worker_id,))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/workers?msg=worker_reactivated", status_code=303)


@router.post("/workers/{worker_id}/delete")
async def workers_delete(worker_id: int):
    conn = connect()
    try:
        att_count = conn.execute(
            "SELECT COUNT(*) AS c FROM attendance WHERE worker_id = ?", (worker_id,)
        ).fetchone()["c"]
        if att_count > 0:
            return RedirectResponse(
                url="/workers?msg=worker_has_attendance", status_code=303
            )
        conn.execute("DELETE FROM workers WHERE id = ?", (worker_id,))
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/workers?msg=worker_deleted", status_code=303)


@router.post("/workers/{worker_id}/move")
async def workers_move(worker_id: int, team_id: int = Form(...)):
    conn = connect()
    try:
        team_exists = conn.execute(
            "SELECT 1 FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        if not team_exists:
            return RedirectResponse(
                url="/workers?msg=target_team_not_found", status_code=303
            )
        conn.execute(
            "UPDATE workers SET team_id = ? WHERE id = ?", (team_id, worker_id)
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/workers?msg=worker_moved", status_code=303)


# ============================================================
# Leads
# ============================================================

@router.get("/leads")
async def leads_page(request: Request, msg: str | None = None):
    conn = connect()
    try:
        teams = conn.execute("SELECT id, name FROM teams ORDER BY id").fetchall()
        leads = conn.execute(
            "SELECT l.id, l.telegram_chat_id, l.name, l.team_id, t.name AS team_name "
            "FROM leads l JOIN teams t ON t.id = l.team_id "
            "ORDER BY t.id"
        ).fetchall()
        teams_without_lead = conn.execute(
            "SELECT id, name FROM teams WHERE id NOT IN ("
            "  SELECT team_id FROM leads"
            ") ORDER BY id"
        ).fetchall()
        pending = conn.execute(
            "SELECT telegram_chat_id, first_name, last_name, username, first_seen_at "
            "FROM pending_leads ORDER BY first_seen_at"
        ).fetchall()
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(
        request,
        "leads.html",
        _ctx(
            request,
            teams=teams,
            teams_without_lead=teams_without_lead,
            leads=leads,
            pending=pending,
            msg=msg,
        ),
    )


@router.post("/leads/add")
async def leads_add(
    request: Request,
    team_id: int = Form(...),
    telegram_chat_id: int = Form(...),
    name: str = Form(""),
):
    nm = name.strip() or None
    conn = connect()
    try:
        already_has_lead = conn.execute(
            "SELECT 1 FROM leads WHERE team_id = ?", (team_id,)
        ).fetchone()
        if already_has_lead:
            return RedirectResponse(
                url="/leads?msg=team_already_has_lead", status_code=303
            )
        conflict = conn.execute(
            "SELECT 1 FROM leads WHERE telegram_chat_id = ?", (telegram_chat_id,)
        ).fetchone()
        if conflict:
            return RedirectResponse(
                url="/leads?msg=chat_id_conflict", status_code=303
            )
        conn.execute(
            "INSERT INTO leads(team_id, telegram_chat_id, name) VALUES (?, ?, ?)",
            (team_id, telegram_chat_id, nm),
        )
        conn.commit()
    finally:
        conn.close()
    await _refresh_bot_menus(request)
    return RedirectResponse(url="/leads?msg=lead_saved", status_code=303)


@router.post("/leads/{lead_id}/edit")
async def leads_edit(
    request: Request,
    lead_id: int,
    team_id: int = Form(...),
    telegram_chat_id: int = Form(...),
    name: str = Form(""),
):
    nm = name.strip() or None
    conn = connect()
    try:
        # Another lead already on this team?
        team_conflict = conn.execute(
            "SELECT 1 FROM leads WHERE team_id = ? AND id != ?",
            (team_id, lead_id),
        ).fetchone()
        if team_conflict:
            return RedirectResponse(
                url="/leads?msg=team_already_has_lead", status_code=303
            )
        # Another lead with same chat ID?
        chat_conflict = conn.execute(
            "SELECT 1 FROM leads WHERE telegram_chat_id = ? AND id != ?",
            (telegram_chat_id, lead_id),
        ).fetchone()
        if chat_conflict:
            return RedirectResponse(
                url="/leads?msg=chat_id_conflict", status_code=303
            )
        conn.execute(
            "UPDATE leads SET team_id = ?, telegram_chat_id = ?, name = ? WHERE id = ?",
            (team_id, telegram_chat_id, nm, lead_id),
        )
        conn.commit()
    finally:
        conn.close()
    await _refresh_bot_menus(request)
    return RedirectResponse(url="/leads?msg=lead_updated", status_code=303)


async def _dm_new_lead(request: Request, chat_id: int, team_name: str) -> None:
    """Send a Telegram DM to a freshly-assigned lead. No-op if bot not attached."""
    bot_app = getattr(request.app.state, "bot_app", None)
    if bot_app is None:
        return
    try:
        await bot_app.bot.send_message(
            chat_id=chat_id,
            text=bot_t("bot.lead.assigned_dm", team_name=team_name),
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Failed to DM newly assigned lead")


@router.post("/leads/assign-pending")
async def leads_assign_pending(
    request: Request,
    telegram_chat_id: int = Form(...),
    team_id: int = Form(...),
):
    conn = connect()
    try:
        team = conn.execute(
            "SELECT id, name FROM teams WHERE id = ?", (team_id,)
        ).fetchone()
        if not team:
            return RedirectResponse(
                url="/leads?msg=target_team_not_found", status_code=303
            )
        if conn.execute(
            "SELECT 1 FROM leads WHERE team_id = ?", (team_id,)
        ).fetchone():
            return RedirectResponse(
                url="/leads?msg=team_already_has_lead", status_code=303
            )
        if conn.execute(
            "SELECT 1 FROM leads WHERE telegram_chat_id = ?", (telegram_chat_id,)
        ).fetchone():
            return RedirectResponse(
                url="/leads?msg=chat_id_conflict", status_code=303
            )
        pending = conn.execute(
            "SELECT first_name, last_name, username FROM pending_leads "
            "WHERE telegram_chat_id = ?",
            (telegram_chat_id,),
        ).fetchone()
        if not pending:
            return RedirectResponse(url="/leads", status_code=303)
        name = " ".join(
            p for p in (pending["first_name"], pending["last_name"]) if p
        ) or pending["username"] or None
        team_name = team["name"]
        conn.execute(
            "INSERT INTO leads(team_id, telegram_chat_id, name) VALUES (?, ?, ?)",
            (team_id, telegram_chat_id, name),
        )
        conn.execute(
            "DELETE FROM pending_leads WHERE telegram_chat_id = ?",
            (telegram_chat_id,),
        )
        conn.commit()
    finally:
        conn.close()
    await _refresh_bot_menus(request)
    await _dm_new_lead(request, telegram_chat_id, team_name)
    return RedirectResponse(url="/leads?msg=lead_saved", status_code=303)


@router.post("/leads/pending/{chat_id}/dismiss")
async def leads_pending_dismiss(chat_id: int):
    conn = connect()
    try:
        conn.execute(
            "DELETE FROM pending_leads WHERE telegram_chat_id = ?", (chat_id,)
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/leads?msg=pending_dismissed", status_code=303)


@router.post("/leads/{lead_id}/delete")
async def leads_delete(request: Request, lead_id: int):
    conn = connect()
    try:
        conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()
    finally:
        conn.close()
    await _refresh_bot_menus(request)
    return RedirectResponse(url="/leads?msg=lead_removed", status_code=303)


# ============================================================
# Owner
# ============================================================

@router.get("/owner")
async def owner_page(request: Request, msg: str | None = None):
    conn = connect()
    try:
        row = conn.execute(
            "SELECT telegram_chat_id FROM owner LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    return TEMPLATES.TemplateResponse(
        request,
        "owner.html",
        _ctx(
            request,
            owner_chat_id=row["telegram_chat_id"] if row else None,
            msg=msg,
        ),
    )


@router.post("/owner/set")
async def owner_set(telegram_chat_id: int = Form(...)):
    conn = connect()
    try:
        conn.execute("DELETE FROM owner")
        conn.execute(
            "INSERT INTO owner(telegram_chat_id) VALUES (?)", (telegram_chat_id,)
        )
        conn.commit()
    finally:
        conn.close()
    return RedirectResponse(url="/owner?msg=owner_updated", status_code=303)


# ============================================================
# Excel download
# ============================================================

@router.get("/download")
async def download_xlsx():
    if not XLSX_PATH.exists():
        raise HTTPException(404, "No attendance file yet.")
    return FileResponse(
        path=str(XLSX_PATH),
        filename=XLSX_PATH.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


app.include_router(router)
