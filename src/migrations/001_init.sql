-- Initial schema for the worker attendance tracker.

CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS teams (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    color_hex   TEXT NOT NULL DEFAULT 'CCCCCC'
);

CREATE TABLE IF NOT EXISTS workers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id     INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_workers_team ON workers(team_id);

CREATE TABLE IF NOT EXISTS leads (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id             INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    telegram_chat_id    INTEGER NOT NULL UNIQUE,
    name                TEXT
);

CREATE TABLE IF NOT EXISTS attendance (
    date        TEXT NOT NULL,           -- YYYY-MM-DD
    worker_id   INTEGER NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    present     INTEGER NOT NULL,        -- 0 / 1
    PRIMARY KEY (date, worker_id)
);

CREATE TABLE IF NOT EXISTS submissions (
    team_id         INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    date            TEXT NOT NULL,
    submitted_at    TEXT NOT NULL,
    lead_chat_id    INTEGER NOT NULL,
    PRIMARY KEY (team_id, date)
);

CREATE TABLE IF NOT EXISTS owner (
    telegram_chat_id INTEGER PRIMARY KEY
);
