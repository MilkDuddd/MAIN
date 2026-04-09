"""Social media presence detection via username probing."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from core import database, http_client
from models.osint import SocialPresence, SocialResult

# Platform probe configurations: {name: url_template}
_PLATFORMS: dict[str, str] = {
    "GitHub":       "https://github.com/{username}",
    "Twitter/X":    "https://x.com/{username}",
    "Reddit":       "https://www.reddit.com/user/{username}",
    "Instagram":    "https://www.instagram.com/{username}/",
    "LinkedIn":     "https://www.linkedin.com/in/{username}",
    "TikTok":       "https://www.tiktok.com/@{username}",
    "YouTube":      "https://www.youtube.com/@{username}",
    "Telegram":     "https://t.me/{username}",
    "Mastodon":     "https://mastodon.social/@{username}",
    "Keybase":      "https://keybase.io/{username}",
    "HackerNews":   "https://news.ycombinator.com/user?id={username}",
    "Medium":       "https://medium.com/@{username}",
    "GitLab":       "https://gitlab.com/{username}",
    "Bitbucket":    "https://bitbucket.org/{username}",
    "DockerHub":    "https://hub.docker.com/u/{username}",
    "PyPI":         "https://pypi.org/user/{username}/",
}

# Status codes that indicate "found"
_FOUND_CODES = {200, 301, 302}
# Status codes that indicate "not found"
_NOT_FOUND_CODES = {404, 410}


def _probe_platform(username: str, platform: str, url_template: str) -> SocialPresence:
    url = url_template.format(username=username)
    try:
        resp = http_client.get(url, source=f"Social/{platform}", timeout=10)
        exists = resp.status_code in _FOUND_CODES and username.lower() in resp.text.lower()
        return SocialPresence(
            username=username,
            platform=platform,
            profile_url=url if exists else None,
            exists=exists,
            status_code=resp.status_code,
        )
    except Exception:
        return SocialPresence(username=username, platform=platform, exists=False)


def check_username(username: str, platforms: Optional[list[str]] = None) -> SocialResult:
    """Check username presence across platforms (concurrent)."""
    from typing import Optional
    targets = {k: v for k, v in _PLATFORMS.items() if not platforms or k in platforms}
    presences: list[SocialPresence] = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(_probe_platform, username, p, url): p
            for p, url in targets.items()
        }
        for fut in as_completed(futures):
            presences.append(fut.result())

    presences.sort(key=lambda p: (not p.exists, p.platform))
    _save(username, presences)
    return SocialResult(username=username, platforms=presences)


def _save(username: str, presences: list[SocialPresence]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        (p.username, p.platform, p.profile_url, 1 if p.exists else 0, p.status_code, now)
        for p in presences
    ]
    database.execute_many(
        "INSERT INTO social_presence (username, platform, profile_url, is_found, status_code, collected_at) VALUES (?,?,?,?,?,?)",
        rows,
    )
