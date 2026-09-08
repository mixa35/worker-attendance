# Roadmap

The system is **demo-ready and deployed** to an Oracle Cloud VM. This file tracks work that is
**deliberately deferred, not forgotten** — each item records the gap, the plan, and a rough cost,
so the trade-off is visible rather than implicit. Pick items off it in any order; nothing here
blocks the current demo.

Last reviewed: 2026-09-08.

---

## 🔴 Security / hardening

### HTTPS for the admin (DuckDNS + Caddy + Let's Encrypt)
Admin currently served over plain HTTP at `http://<vm-ip>:8000`. Basic Auth password travels in cleartext on every request.

**Plan**: free DuckDNS hostname → Caddy reverse-proxy on the VM → auto-fetched Let's Encrypt cert. Result: `https://<your>.duckdns.org` with a green padlock, certs auto-renew every 60 days.

**Manual prerequisites**:
- DuckDNS account (sign-in via GitHub/Google), pick subdomain, copy token.
- Open ports 80 + 443 in OCI security list and on the VM's iptables.

**Implementation**: `apt install caddy`, `Caddyfile` reverse-proxying to `localhost:8000`, restart. ~15 min once prerequisites are done.

### CSRF protection + session-based auth
Admin uses HTTP Basic Auth. A malicious page in another tab could forge POSTs to `/workers/{id}/delete` etc. while the owner is authenticated. Low real-world risk (single-owner, public IP, strong password), but standard hygiene gap.

**Plan**: replace Basic Auth with a session cookie + login form, embed CSRF tokens in every form. ~1.5h.

**Files affected**: `src/admin/app.py` (auth dependency, `/login`, `/logout`), all templates (token in hidden field), `i18n.py` (login strings).

### Off-VM backups (Backblaze B2 or similar)
Nightly local backups already run at 03:15 to `~/backups/<date>/` (30-day rolling). Survives container/disk corruption but **not** a VM termination event.

**Plan**: Backblaze B2 free tier (10 GB), `b2` CLI or rclone, weekly sync of `~/backups/` to a private bucket. Or: encrypted email of the last backup to the owner.

**Manual prerequisite**: Backblaze account + bucket creation.

---

## 🟡 UX / quality

### Owner chat-ID validation flow
`/owner/set` accepts any integer with no real check. A typo silently saves a wrong owner and the system locks the real owner out of monthly summaries / `/report`.

**Plan**: before saving, send a test DM via the bot to the new chat ID. If Telegram rejects (`chat not found` / `bot can't initiate conversation`), don't save. ~15 lines + 2 translation keys.

**Sketch** is in chat history of session ending 2026-05-08 — straightforward.

### Per-lead bot language preference
Currently `BOT_LANG` is a single global env var (defaults to `ka`). If a future team has English-only leads, all leads still get Georgian.

**Plan**: add `language` column to `leads` table (default NULL → falls back to `BOT_LANG`), expose a select on the admin Leads edit form. Bot resolves per-lead language for every send.

**Schema change**: small migration, no breakage.

### Drag-drop "team chip count" doesn't update without reload
After dragging a worker from Team A to Team B, the **2 active** chip on each team's header still reflects pre-drag values until manual reload. Cosmetic.

**Plan**: update both chips client-side after a successful move, no extra request needed.

---

## ⚠️ Time-sensitive

### ~~Oracle hardware migration — IP reservation~~ (retired 2026-09-08)
**Deadline was 2026-05-20.** Oracle flagged the underlying host as unstable and auto-migrated the
VM, which is a stop/start and releases the ephemeral public IP. The bot is unaffected either way
(outbound only to Telegram); only the admin URL moves.

This item retired itself as written — the deadline passed without the demo converting. If the
project is picked back up, reserve a static IP **before** any further migration:

**Steps when needed**:
1. OCI Console → Compute → Instances → `worker-attendance-bot`
2. Resources → Attached VNICs → click the VNIC
3. IPv4 Addresses → ⋮ → Edit
4. Change Public IP type from `Ephemeral` to `Reserved` → Create new reserved IP
5. Save

Free Tier allows 2 reserved IPs at no cost.

## 🟠 DevOps / operations

### GitHub → VM auto-deploy
Currently every change is `scp` + `docker compose up -d --build` from the laptop. A `git push` to main could trigger the VM to pull and rebuild itself.

**Plan options** (pick one):
- **Pull-based**: cron on VM runs `git pull && docker compose up -d --build` every N minutes. Simple, no secrets in CI.
- **Push-based**: GitHub Actions on `push: main` SSHes into the VM and runs the deploy. Faster, needs SSH key as a GitHub secret.

I'd suggest pull-based for simplicity (~10 min). Push-based when iteration speeds up.

### Add lint + typecheck to CI
`.github/workflows/ci.yml` now runs the test suite on Python 3.11 and 3.12 and builds the
deployment image on every push and pull request. Static analysis is still missing.

**Plan**: add `ruff check` and `mypy` steps plus their config in `pyproject.toml`. ~30 min one-time.
Expect a first-run backlog of findings in `admin/app.py` and `bot/handlers.py`.

### Container health probe is liveness-only
`/healthz` checks SQLite reachability but doesn't verify the bot is actually polling Telegram. If the polling task silently dies but uvicorn stays up, healthcheck still returns 200.

**Plan**: track `last_successful_getUpdates_at` timestamp in app state, return 503 if older than 120s.

### Per-team worker history / mid-month transfer fidelity
**Known limitation** documented in `CLAUDE.md`: moving a worker mid-month re-attributes the whole month's record to the new team in the Excel report. Cleaner fix is a `worker_team_history` table tracking start/end dates per assignment, then Excel renders by querying which team a worker belonged to **on each day**.

Not urgent — only matters if mid-month transfers become common.

---

## 📚 Documentation / showcase

### Architecture diagram with real screenshots
README has an ASCII diagram. Adding 1-2 screenshots (Telegram form + admin dashboard, both in Georgian) would make the GitHub repo visibly impressive in 2 seconds.

**Manual prerequisite**: take fresh screenshots without sensitive data (use a demo account with placeholder workers).

### Demo video / GIF
30-second screen recording: lead receives form → ticks workers → submits → owner runs `/report` → Excel opens with the fresh marks. Embed in README via GitHub-hosted video upload.

---

## ✅ Done (for reference)

- Telegram bot + scheduler + admin web in one container, deployed on Oracle Cloud Always Free.
- Daily auto-dispatch at 08:00 Asia/Tbilisi.
- Live `attendance.xlsx` with monthly sheets, team-colored rows, national-ID column, atomic writes.
- Monthly auto-summary on day 1 + on-demand `/report`.
- Admin web: dashboard, teams (color picker, edit, delete-with-safety), workers (drag-and-drop between teams, deactivate, archived section, delete-with-safety), leads (edit in place, pending-invites inbox), owner.
- Bilingual EN / Georgian — admin via cookie, bot via `BOT_LANG`.
- Pending-invites flow with 6h owner-DM cooldown; auto-refresh of bot menus on lead changes (no restart needed).
- SQLite WAL mode, atomic Excel writes, healthcheck endpoint, Docker `HEALTHCHECK`, log rotation, nightly local backups.
- Pinned dependency lockfile, drag handle restricted to ⋮⋮ column, favicon, self-hosted SortableJS.
- GitHub repo published with description, topics, and README.
- Test suite (19 tests) covering the migration runner and the monthly workbook rendering,
  plus GitHub Actions CI running them on Python 3.11 + 3.12 and building the Docker image.
- MIT license.
