-- Per-team draft state for the daily attendance form.
-- Rows are created when a lead opens the form and updated as buttons are tapped.
-- Only on Submit are values copied into the `attendance` table.

CREATE TABLE IF NOT EXISTS form_state (
    team_id   INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    date      TEXT    NOT NULL,            -- YYYY-MM-DD (local)
    worker_id INTEGER NOT NULL REFERENCES workers(id) ON DELETE CASCADE,
    present   INTEGER NOT NULL DEFAULT 0,  -- default = absent; lead ticks who showed up
    PRIMARY KEY (team_id, date, worker_id)
);
