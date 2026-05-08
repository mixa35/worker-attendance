-- Users who DM'd the bot but aren't yet assigned to a team or registered as owner.
-- Owner sees them in the admin's "Pending invites" section and assigns them to a team.

CREATE TABLE IF NOT EXISTS pending_leads (
    telegram_chat_id        INTEGER PRIMARY KEY,
    first_name              TEXT,
    last_name               TEXT,
    username                TEXT,
    first_seen_at           TEXT NOT NULL,
    last_seen_at            TEXT NOT NULL,
    last_owner_notified_at  TEXT
);
