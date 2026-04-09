"""SQLite database manager with full schema initialization."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from . import settings
from .exceptions import DatabaseError

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ── Core entity tables ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS entities (
    entity_id       TEXT PRIMARY KEY,
    canonical_name  TEXT NOT NULL,
    entity_type     TEXT NOT NULL,  -- person, organization, location, vessel, aircraft
    aliases         TEXT,           -- JSON array
    tags            TEXT,           -- JSON array
    source_modules  TEXT,           -- JSON array of originating modules
    notes           TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(canonical_name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);

CREATE TABLE IF NOT EXISTS relationships (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       TEXT NOT NULL REFERENCES entities(entity_id),
    target_id       TEXT NOT NULL REFERENCES entities(entity_id),
    rel_type        TEXT NOT NULL,  -- controls, donates_to, board_member, sanctioned_by, mentioned_with, etc.
    confidence      REAL DEFAULT 0.5,
    source_module   TEXT,
    evidence        TEXT,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id);

-- ── OSINT tables ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS whois_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    domain          TEXT NOT NULL,
    registrar       TEXT,
    registrant_name TEXT,
    registrant_org  TEXT,
    registrant_email TEXT,
    registrant_country TEXT,
    created_date    TEXT,
    expiry_date     TEXT,
    updated_date    TEXT,
    name_servers    TEXT,  -- JSON array
    raw_text        TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_whois_domain ON whois_records(domain);

CREATE TABLE IF NOT EXISTS dns_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    domain          TEXT NOT NULL,
    record_type     TEXT NOT NULL,  -- A, AAAA, MX, TXT, NS, CNAME, SOA
    value           TEXT NOT NULL,
    ttl             INTEGER,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dns_domain ON dns_records(domain);

CREATE TABLE IF NOT EXISTS cert_transparency (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    domain          TEXT NOT NULL,
    cert_id         TEXT,
    issuer          TEXT,
    common_name     TEXT,
    san_names       TEXT,  -- JSON array
    not_before      TEXT,
    not_after       TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cert_domain ON cert_transparency(domain);

CREATE TABLE IF NOT EXISTS social_presence (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL,
    platform        TEXT NOT NULL,
    profile_url     TEXT,
    is_found        INTEGER NOT NULL,  -- 1=found, 0=not found
    status_code     INTEGER,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_social_username ON social_presence(username);

-- ── SIGINT tables ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS flight_tracks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    icao24          TEXT NOT NULL,
    callsign        TEXT,
    origin_country  TEXT,
    latitude        REAL,
    longitude       REAL,
    altitude_m      REAL,
    velocity_ms     REAL,
    true_track      REAL,  -- degrees
    vertical_rate   REAL,
    on_ground       INTEGER,
    squawk          TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_flight_icao ON flight_tracks(icao24);
CREATE INDEX IF NOT EXISTS idx_flight_callsign ON flight_tracks(callsign);

CREATE TABLE IF NOT EXISTS vessel_tracks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    mmsi            TEXT NOT NULL,
    imo             TEXT,
    name            TEXT,
    callsign        TEXT,
    vessel_type     INTEGER,
    flag            TEXT,
    latitude        REAL,
    longitude       REAL,
    sog             REAL,  -- speed over ground, knots
    cog             REAL,  -- course over ground, degrees
    heading         REAL,
    destination     TEXT,
    eta             TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vessel_mmsi ON vessel_tracks(mmsi);

CREATE TABLE IF NOT EXISTS rf_allocations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    callsign        TEXT,
    license_name    TEXT,
    entity_name     TEXT,
    frequency_mhz   REAL,
    service_type    TEXT,
    state           TEXT,
    county          TEXT,
    status          TEXT,
    grant_date      TEXT,
    expiry_date     TEXT,
    source          TEXT,  -- FCC, ITU
    collected_at    TEXT NOT NULL
);

-- ── Geopolitical tables ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS world_leaders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    wikidata_id     TEXT UNIQUE,
    name            TEXT NOT NULL,
    role            TEXT NOT NULL,
    country         TEXT NOT NULL,
    country_code    TEXT,
    party           TEXT,
    in_office_since TEXT,
    date_of_birth   TEXT,
    nationality     TEXT,
    image_url       TEXT,
    wikipedia_url   TEXT,
    entity_id       TEXT REFERENCES entities(entity_id),
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leaders_country ON world_leaders(country_code);

CREATE TABLE IF NOT EXISTS political_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT UNIQUE,
    source          TEXT,
    event_date      TEXT,
    actor1          TEXT,
    actor1_country  TEXT,
    actor2          TEXT,
    actor2_country  TEXT,
    event_description TEXT,
    action_type     TEXT,
    goldstein_scale REAL,
    source_url      TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pol_events_date ON political_events(event_date);
CREATE INDEX IF NOT EXISTS idx_pol_events_country ON political_events(actor1_country);

CREATE TABLE IF NOT EXISTS sanctions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    sanction_id     TEXT UNIQUE,
    list_source     TEXT NOT NULL,  -- OFAC, EU, UN
    entity_type     TEXT,           -- Individual, Entity, Vessel, Aircraft
    name            TEXT NOT NULL,
    aliases         TEXT,           -- JSON array
    nationality     TEXT,
    date_of_birth   TEXT,
    reason          TEXT,
    programs        TEXT,           -- JSON array
    effective_date  TEXT,
    entity_id       TEXT REFERENCES entities(entity_id),
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sanctions_name ON sanctions(name);
CREATE INDEX IF NOT EXISTS idx_sanctions_source ON sanctions(list_source);

CREATE TABLE IF NOT EXISTS conflict_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT UNIQUE,
    source          TEXT,
    event_date      TEXT,
    country         TEXT,
    region          TEXT,
    location        TEXT,
    latitude        REAL,
    longitude       REAL,
    event_type      TEXT,
    actor1          TEXT,
    actor2          TEXT,
    fatalities      INTEGER,
    notes           TEXT,
    source_url      TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conflict_country ON conflict_events(country);
CREATE INDEX IF NOT EXISTS idx_conflict_date ON conflict_events(event_date);

CREATE TABLE IF NOT EXISTS government_tenders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tender_id       TEXT UNIQUE,
    source          TEXT,
    title           TEXT,
    description     TEXT,
    agency          TEXT,
    country         TEXT,
    published_date  TEXT,
    deadline_date   TEXT,
    estimated_value_usd REAL,
    award_status    TEXT,
    awardee         TEXT,
    naics_code      TEXT,
    url             TEXT,
    collected_at    TEXT NOT NULL
);

-- ── Power structure tables ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS billionaires (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_rank     INTEGER,
    name            TEXT NOT NULL,
    net_worth_usd   REAL,
    source          TEXT,
    country         TEXT,
    industry        TEXT,
    age             INTEGER,
    primary_company TEXT,
    wikidata_id     TEXT,
    entity_id       TEXT REFERENCES entities(entity_id),
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_billionaires_name ON billionaires(name);

CREATE TABLE IF NOT EXISTS corporations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      TEXT UNIQUE,
    name            TEXT NOT NULL,
    jurisdiction    TEXT,
    company_type    TEXT,
    incorporation_date TEXT,
    registered_address TEXT,
    status          TEXT,
    parent_company_id TEXT,
    officers        TEXT,  -- JSON array
    source          TEXT,
    entity_id       TEXT REFERENCES entities(entity_id),
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_corps_name ON corporations(name);

CREATE TABLE IF NOT EXISTS board_memberships (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    person_name     TEXT NOT NULL,
    company_name    TEXT NOT NULL,
    role            TEXT,
    start_date      TEXT,
    end_date        TEXT,
    source          TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_board_person ON board_memberships(person_name);
CREATE INDEX IF NOT EXISTS idx_board_company ON board_memberships(company_name);

CREATE TABLE IF NOT EXISTS political_donations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_name      TEXT NOT NULL,
    donor_employer  TEXT,
    donor_occupation TEXT,
    recipient_name  TEXT NOT NULL,
    recipient_party TEXT,
    amount_usd      REAL,
    transaction_date TEXT,
    election_cycle  TEXT,
    source          TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_donations_donor ON political_donations(donor_name);
CREATE INDEX IF NOT EXISTS idx_donations_recipient ON political_donations(recipient_name);

-- ── UAP / Anomalous phenomena tables ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS uap_sightings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id       TEXT,
    source          TEXT NOT NULL,  -- NUFORC, MUFON, FAA
    occurred_date   TEXT,
    reported_date   TEXT,
    city            TEXT,
    state           TEXT,
    country         TEXT,
    shape           TEXT,
    duration_sec    INTEGER,
    description     TEXT,
    posted_url      TEXT,
    lat             REAL,
    lon             REAL,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_uap_state ON uap_sightings(state);
CREATE INDEX IF NOT EXISTS idx_uap_date ON uap_sightings(occurred_date);
CREATE INDEX IF NOT EXISTS idx_uap_source ON uap_sightings(source);

CREATE TABLE IF NOT EXISTS uap_reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id       TEXT UNIQUE,
    source          TEXT NOT NULL,  -- Congressional, DIA, Navy, AARO, BlackVault
    title           TEXT NOT NULL,
    report_date     TEXT,
    classification  TEXT,           -- Unclassified, Declassified, etc.
    summary         TEXT,
    full_text       TEXT,
    document_url    TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_uap_reports_source ON uap_reports(source);

CREATE TABLE IF NOT EXISTS hearing_transcripts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hearing_id      TEXT UNIQUE,
    title           TEXT NOT NULL,
    date            TEXT,
    committee       TEXT,
    chamber         TEXT,  -- Senate, House
    witnesses       TEXT,  -- JSON array
    summary         TEXT,
    key_quotes      TEXT,  -- JSON array
    document_url    TEXT,
    collected_at    TEXT NOT NULL
);

-- ── Live feed tables ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feed_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id         TEXT UNIQUE,
    source          TEXT NOT NULL,
    title           TEXT NOT NULL,
    url             TEXT,
    published_at    TEXT,
    summary         TEXT,
    full_text       TEXT,
    category        TEXT,  -- geopolitical, uap, power, osint, etc.
    matched_keywords TEXT, -- JSON array
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feed_category ON feed_items(category);
CREATE INDEX IF NOT EXISTS idx_feed_published ON feed_items(published_at);

CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id        TEXT UNIQUE,
    keyword         TEXT,
    entity_name     TEXT,
    triggered_by    TEXT,  -- feed_item id, or module name
    message         TEXT NOT NULL,
    severity        TEXT DEFAULT 'info',
    acknowledged    INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL
);

-- ── v2.0 New tables ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS offshore_entities (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    icij_node_id    TEXT UNIQUE,
    name            TEXT NOT NULL,
    entity_type     TEXT,
    jurisdiction    TEXT,
    country_codes   TEXT,
    linked_to       TEXT,
    data_source     TEXT,
    valid_until     TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_offshore_name ON offshore_entities(name);
CREATE INDEX IF NOT EXISTS idx_offshore_source ON offshore_entities(data_source);

CREATE TABLE IF NOT EXISTS offshore_relationships (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node_id  TEXT NOT NULL,
    target_node_id  TEXT NOT NULL,
    rel_type        TEXT,
    start_date      TEXT,
    end_date        TEXT,
    collected_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sec_filings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    accession_no    TEXT UNIQUE,
    cik             TEXT,
    company_name    TEXT,
    form_type       TEXT,
    filed_date      TEXT,
    period_of_report TEXT,
    description     TEXT,
    document_url    TEXT,
    full_text_snippet TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sec_company ON sec_filings(company_name);
CREATE INDEX IF NOT EXISTS idx_sec_form ON sec_filings(form_type);
CREATE INDEX IF NOT EXISTS idx_sec_date ON sec_filings(filed_date);

CREATE TABLE IF NOT EXISTS wayback_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    url             TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    status_code     TEXT,
    mime_type       TEXT,
    digest          TEXT,
    snapshot_url    TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wayback_url ON wayback_snapshots(url);

CREATE TABLE IF NOT EXISTS academic_papers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id        TEXT UNIQUE,
    title           TEXT NOT NULL,
    authors         TEXT,
    institutions    TEXT,
    publication_year INTEGER,
    journal         TEXT,
    doi             TEXT,
    abstract        TEXT,
    cited_by_count  INTEGER,
    funding_sources TEXT,
    open_access_url TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_papers_title ON academic_papers(title);
CREATE INDEX IF NOT EXISTS idx_papers_year ON academic_papers(publication_year);

CREATE TABLE IF NOT EXISTS wanted_persons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    list_source     TEXT NOT NULL,
    notice_id       TEXT UNIQUE,
    full_name       TEXT NOT NULL,
    aliases         TEXT,
    nationality     TEXT,
    date_of_birth   TEXT,
    sex             TEXT,
    charges         TEXT,
    reward_text     TEXT,
    image_url       TEXT,
    details_url     TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wanted_name ON wanted_persons(full_name);
CREATE INDEX IF NOT EXISTS idx_wanted_source ON wanted_persons(list_source);

CREATE TABLE IF NOT EXISTS congress_members (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id       TEXT UNIQUE,
    full_name       TEXT NOT NULL,
    party           TEXT,
    state           TEXT,
    chamber         TEXT,
    district        TEXT,
    in_office       INTEGER,
    dw_nominate     REAL,
    twitter_account TEXT,
    url             TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_congress_name ON congress_members(full_name);
CREATE INDEX IF NOT EXISTS idx_congress_state ON congress_members(state);

CREATE TABLE IF NOT EXISTS congress_votes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vote_id         TEXT UNIQUE,
    member_id       TEXT NOT NULL,
    member_name     TEXT,
    congress        INTEGER,
    bill_id         TEXT,
    bill_title      TEXT,
    vote_date       TEXT,
    vote_position   TEXT,
    result          TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_votes_member ON congress_votes(member_id);
CREATE INDEX IF NOT EXISTS idx_votes_bill ON congress_votes(bill_id);

CREATE TABLE IF NOT EXISTS threat_intel (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator       TEXT NOT NULL,
    indicator_type  TEXT NOT NULL,
    source          TEXT NOT NULL,
    malicious_votes INTEGER DEFAULT 0,
    suspicious_votes INTEGER DEFAULT 0,
    clean_votes     INTEGER DEFAULT 0,
    categories      TEXT,
    last_analysis   TEXT,
    reputation_score INTEGER,
    raw_data        TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_threat_indicator ON threat_intel(indicator);
CREATE INDEX IF NOT EXISTS idx_threat_type ON threat_intel(indicator_type);

CREATE TABLE IF NOT EXISTS ip_enrichment (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address      TEXT NOT NULL,
    hostname        TEXT,
    city            TEXT,
    region          TEXT,
    country         TEXT,
    loc             TEXT,
    org             TEXT,
    asn             TEXT,
    postal          TEXT,
    timezone        TEXT,
    is_vpn          INTEGER,
    is_proxy        INTEGER,
    is_tor          INTEGER,
    is_hosting      INTEGER,
    abuse_score     INTEGER,
    abuse_reports   INTEGER,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ip_address ON ip_enrichment(ip_address);

CREATE TABLE IF NOT EXISTS breach_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    target          TEXT NOT NULL,
    breach_name     TEXT NOT NULL,
    breach_date     TEXT,
    pwn_count       INTEGER,
    data_classes    TEXT,
    description     TEXT,
    is_verified     INTEGER,
    is_sensitive    INTEGER,
    source          TEXT,
    collected_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_breach_target ON breach_records(target);

CREATE TABLE IF NOT EXISTS module_run_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    module          TEXT NOT NULL,
    last_run_at     TEXT NOT NULL,
    record_count    INTEGER,
    status          TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_module_run ON module_run_log(module);
"""


def _conn() -> sqlite3.Connection:
    db = settings.db_path()
    conn = sqlite3.connect(str(db), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    try:
        conn = _conn()
        conn.executescript(_SCHEMA)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise DatabaseError(f"Schema initialization failed: {e}") from e


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager providing a database connection."""
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
    """Run a SELECT query and return all rows."""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        return cursor.fetchall()


def execute_write(sql: str, params: tuple = ()) -> int:
    """Run an INSERT/UPDATE/DELETE and return lastrowid."""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid or 0


def execute_many(sql: str, params_list: list[tuple]) -> int:
    """Run executemany and return rowcount."""
    with get_db() as conn:
        cursor = conn.executemany(sql, params_list)
        return cursor.rowcount
