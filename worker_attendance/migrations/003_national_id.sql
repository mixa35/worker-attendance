-- Optional national ID per worker (e.g. Georgian 11-digit personal number).
-- Used in the Excel report to distinguish workers with identical names.
-- NULL is allowed; uniqueness is only enforced when set.

ALTER TABLE workers ADD COLUMN national_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_workers_national_id
    ON workers(national_id)
    WHERE national_id IS NOT NULL;
