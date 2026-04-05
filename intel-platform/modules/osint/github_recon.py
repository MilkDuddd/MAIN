"""GitHub/GitLab public API reconnaissance."""

from core import http_client
from models.osint import GitHubProfile

_GITHUB_API = "https://api.github.com"


def fetch_github_profile(username: str) -> GitHubProfile:
    """Fetch GitHub user profile and public repo metadata."""
    try:
        headers = {"Accept": "application/vnd.github+json"}
        resp = http_client.get(f"{_GITHUB_API}/users/{username}", headers=headers, source="GitHub", timeout=20)
        data = resp.json()
        if "message" in data:
            return GitHubProfile(username=username, error=data["message"])

        # Fetch repos
        repos_resp = http_client.get(
            f"{_GITHUB_API}/users/{username}/repos",
            params={"per_page": 30, "sort": "updated"},
            headers=headers,
            source="GitHub",
            timeout=20,
        )
        repos = []
        for r in repos_resp.json():
            if isinstance(r, dict):
                repos.append({
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "language": r.get("language"),
                    "stars": r.get("stargazers_count"),
                    "forks": r.get("forks_count"),
                    "url": r.get("html_url"),
                    "updated_at": r.get("updated_at"),
                })

        # Fetch orgs
        orgs_resp = http_client.get(
            f"{_GITHUB_API}/users/{username}/orgs",
            headers=headers,
            source="GitHub",
            timeout=15,
        )
        orgs = [o.get("login", "") for o in orgs_resp.json() if isinstance(o, dict)]

        return GitHubProfile(
            username=username,
            name=data.get("name"),
            bio=data.get("bio"),
            company=data.get("company"),
            location=data.get("location"),
            email=data.get("email"),
            followers=data.get("followers", 0),
            following=data.get("following", 0),
            public_repos=data.get("public_repos", 0),
            created_at=data.get("created_at"),
            repos=repos,
            organizations=orgs,
        )
    except Exception as e:
        return GitHubProfile(username=username, error=str(e))


def search_github_code(query: str, lang: Optional[str] = None) -> list[dict]:
    """Search GitHub public code (requires no auth for limited results)."""
    from typing import Optional
    params = {"q": query, "per_page": 30}
    if lang:
        params["q"] += f" language:{lang}"
    try:
        resp = http_client.get(
            f"{_GITHUB_API}/search/code",
            params=params,
            headers={"Accept": "application/vnd.github+json"},
            source="GitHub",
            timeout=20,
        )
        items = resp.json().get("items", [])
        return [
            {
                "name": i.get("name"),
                "path": i.get("path"),
                "repo": i.get("repository", {}).get("full_name"),
                "url": i.get("html_url"),
                "score": i.get("score"),
            }
            for i in items
        ]
    except Exception:
        return []
