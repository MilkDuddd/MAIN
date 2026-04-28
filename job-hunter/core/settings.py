"""Settings management for Job Hunter."""

import json
from pathlib import Path
from typing import Any

APP_DIR = Path.home() / ".job-hunter"
SETTINGS_PATH = APP_DIR / "settings.json"
DB_PATH = APP_DIR / "job_hunter.db"
LOGS_DIR = APP_DIR / "logs"
RESUMES_DIR = APP_DIR / "resumes"
EXPORTS_DIR = APP_DIR / "exports"

_DEFAULTS: dict[str, Any] = {
    "anthropic_api_key": "",
    "default_profile_id": None,
    "search_defaults": {
        "location": "",
        "radius_miles": 25,
        "job_type": "any",
        "experience_level": "any",
        "remote": False,
    },
    "auto_apply": {
        "enabled": False,
        "daily_limit": 20,
        "delay_seconds": 3,
        "skip_if_already_applied": True,
        "require_easy_apply": True,
    },
    "platforms": {
        "indeed": {"enabled": True},
        "linkedin": {"enabled": True, "api_key": ""},
        "glassdoor": {"enabled": True},
        "dice": {"enabled": True},
        "ziprecruiter": {"enabled": True},
        "remoteok": {"enabled": True},
    },
    "notifications": {
        "desktop": True,
        "daily_summary": True,
    },
    "theme": "dark",
    "version": "1.0.0",
}


def _ensure_dirs() -> None:
    for d in (APP_DIR, LOGS_DIR, RESUMES_DIR, EXPORTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def db_path() -> Path:
    _ensure_dirs()
    return DB_PATH


def load() -> dict[str, Any]:
    _ensure_dirs()
    if not SETTINGS_PATH.exists():
        return dict(_DEFAULTS)
    try:
        data = json.loads(SETTINGS_PATH.read_text())
        merged = dict(_DEFAULTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULTS)


def save(settings: dict[str, Any]) -> None:
    _ensure_dirs()
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2))


def get(key: str, default: Any = None) -> Any:
    return load().get(key, default)


def set_key(key: str, value: Any) -> None:
    s = load()
    s[key] = value
    save(s)
