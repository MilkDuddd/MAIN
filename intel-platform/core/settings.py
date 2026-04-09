"""Persistent settings management for Intel Platform."""

import json
import os
from pathlib import Path
from typing import Any, Optional

from .config import SETTINGS_DIR, DB_FILENAME, DEFAULT_MODEL

SETTINGS_PATH = Path(SETTINGS_DIR).expanduser() / "settings.json"
DB_PATH       = Path(SETTINGS_DIR).expanduser() / DB_FILENAME

_DEFAULTS: dict[str, Any] = {
    "groq_api_key":          "",
    "shodan_api_key":        "",
    "newsapi_key":           "",
    "aisstream_key":         "",
    "fec_api_key":           "",
    "sam_gov_key":           "",
    "otx_key":               "",
    "gfw_key":               "",
    "model":                 DEFAULT_MODEL,
    "analyst_name":          "Intel Analyst",
    "output_dir":            str(Path("~/intel-reports").expanduser()),
    "auto_update":           True,
    "alert_keywords":        [],
    "tracked_entities":      [],
}


def _load() -> dict[str, Any]:
    if SETTINGS_PATH.exists():
        try:
            return {**_DEFAULTS, **json.loads(SETTINGS_PATH.read_text())}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(_DEFAULTS)


def _save(data: dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2))


def get(key: str, default: Any = None) -> Any:
    return _load().get(key, default)


def set(key: str, value: Any) -> None:
    data = _load()
    data[key] = value
    _save(data)


def all_settings() -> dict[str, Any]:
    return _load()


def db_path() -> Path:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH


def require_key(name: str, env_var: str) -> str:
    """Return API key from settings or environment, raise if missing."""
    val = get(name) or os.environ.get(env_var, "")
    if not val:
        raise ValueError(
            f"Missing API key '{name}'. Set via `intel settings set {name} <key>` "
            f"or export {env_var}=<key>"
        )
    return val


def output_dir() -> Path:
    path = Path(get("output_dir", "~/intel-reports")).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path
