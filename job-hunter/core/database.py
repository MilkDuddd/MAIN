"""SQLite database manager for Job Hunter."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from . import settings
from .exceptions import DatabaseError

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ── Profiles ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS profiles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT,
    location        TEXT,
    linkedin_url    TEXT,
    github_url      TEXT,
    portfolio_url   TEXT,
    headline        TEXT,
    summary         TEXT,
    resume_text     TEXT,
    resume_file     TEXT,
    skills          TEXT,   -- JSON array
    desired_roles   TEXT,   -- JSON array
    desired_salary  TEXT,
    job_type        TEXT,   -- full-time, part-time, contract, etc.
    willing_remote  INTEGER DEFAULT 1,
    willing_relocate INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS work_experience (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id      INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    company         TEXT NOT NULL,
    title           TEXT NOT NULL,
    location        TEXT,
    start_date      TEXT,
    end_date        TEXT,
    current         INTEGER DEFAULT 0,
    description     TEXT,
    achievements    TEXT,   -- JSON array
    technologies    TEXT,   -- JSON array
    sort_order      INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_work_profile ON work_experience(profile_id);

CREATE TABLE IF NOT EXISTS education (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id      INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    institution     TEXT NOT NULL,
    degree          TEXT,
    field_of_study  TEXT,
    start_date      TEXT,
    end_date        TEXT,
    gpa             TEXT,
    activities      TEXT,
    sort_order      INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_edu_profile ON education(profile_id);

CREATE TABLE IF NOT EXISTS certifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id      INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    issuer          TEXT,
    issued_date     TEXT,
    expiry_date     TEXT,
    credential_id   TEXT,
    credential_url  TEXT
);
CREATE INDEX IF NOT EXISTS idx_cert_profile ON certifications(profile_id);

-- ── Job listings ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_listings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id     TEXT,
    platform        TEXT NOT NULL,  -- indeed, linkedin, glassdoor, dice, ziprecruiter, remoteok
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    location        TEXT,
    remote          INTEGER DEFAULT 0,
    job_type        TEXT,           -- full-time, part-time, contract, internship
    salary_min      INTEGER,
    salary_max      INTEGER,
    salary_text     TEXT,
    description     TEXT,
    requirements    TEXT,
    apply_url       TEXT,
    easy_apply      INTEGER DEFAULT 0,
    posted_date     TEXT,
    collected_at    TEXT NOT NULL,
    match_score     REAL DEFAULT 0.0,
    UNIQUE(platform, external_id)
);
CREATE INDEX IF NOT EXISTS idx_jobs_platform ON job_listings(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON job_listings(company);
CREATE INDEX IF NOT EXISTS idx_jobs_posted ON job_listings(posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON job_listings(match_score DESC);

-- ── Applications ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS applications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id      INTEGER NOT NULL REFERENCES profiles(id),
    job_id          INTEGER NOT NULL REFERENCES job_listings(id),
    status          TEXT NOT NULL DEFAULT 'applied',
                    -- applied, viewed, phone_screen, interview, offer, rejected, withdrawn
    cover_letter    TEXT,
    resume_version  TEXT,
    applied_at      TEXT NOT NULL,
    last_updated    TEXT NOT NULL,
    notes           TEXT,
    next_action     TEXT,
    next_action_date TEXT,
    salary_expected INTEGER,
    contact_name    TEXT,
    contact_email   TEXT,
    referral        TEXT,
    auto_applied    INTEGER DEFAULT 0,
    UNIQUE(profile_id, job_id)
);
CREATE INDEX IF NOT EXISTS idx_apps_profile ON applications(profile_id);
CREATE INDEX IF NOT EXISTS idx_apps_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_apps_applied ON applications(applied_at);

CREATE TABLE IF NOT EXISTS application_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id  INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    event_type      TEXT NOT NULL,  -- status_change, note_added, reminder_set, email_received
    old_value       TEXT,
    new_value       TEXT,
    notes           TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_app ON application_events(application_id);

-- ── Cover letters ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cover_letters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id      INTEGER NOT NULL REFERENCES profiles(id),
    job_id          INTEGER REFERENCES job_listings(id),
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    is_template     INTEGER DEFAULT 0,
    ai_generated    INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cl_profile ON cover_letters(profile_id);

-- ── Saved searches ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS saved_searches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    keywords        TEXT NOT NULL,
    location        TEXT,
    platforms       TEXT,           -- JSON array
    filters         TEXT,           -- JSON object
    auto_run        INTEGER DEFAULT 0,
    last_run_at     TEXT,
    created_at      TEXT NOT NULL
);

-- ── Run log ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS run_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    module          TEXT NOT NULL,
    action          TEXT NOT NULL,
    status          TEXT NOT NULL,  -- success, error, partial
    records         INTEGER DEFAULT 0,
    message         TEXT,
    ran_at          TEXT NOT NULL
);
"""


def _conn() -> sqlite3.Connection:
    db = settings.db_path()
    conn = sqlite3.connect(str(db), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    try:
        conn = _conn()
        conn.executescript(_SCHEMA)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise DatabaseError(f"Schema initialization failed: {e}") from e


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = _conn()
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise DatabaseError(str(e)) from e
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()


def execute_write(sql: str, params: tuple = ()) -> int:
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid or 0


def execute_many(sql: str, params_list: list[tuple]) -> int:
    with get_db() as conn:
        cursor = conn.executemany(sql, params_list)
        return cursor.rowcount
