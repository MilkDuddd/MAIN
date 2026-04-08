"""Search engine dorking via DuckDuckGo HTML (no API key required)."""

import re
from typing import Optional

from bs4 import BeautifulSoup

from core import http_client
from models.osint import DorkResult

_DDG_URL = "https://html.duckduckgo.com/html/"

# Predefined intelligence-focused dork templates
DORK_TEMPLATES = {
    "site_docs":        'site:{target} filetype:pdf OR filetype:doc OR filetype:xls',
    "email_leak":       '"{target}" "@gmail.com" OR "@yahoo.com" OR "@protonmail.com"',
    "pastebin":         'site:pastebin.com "{target}"',
    "linkedin":         'site:linkedin.com "{target}"',
    "github_mentions":  'site:github.com "{target}"',
    "news":             '"{target}" site:reuters.com OR site:bbc.com OR site:nytimes.com',
    "court_records":    '"{target}" site:courtlistener.com OR site:pacer.gov OR site:unicourt.com',
    "leaked_data":      '"{target}" site:haveibeenpwned.com OR "data breach" OR "data leak"',
    "govt_mentions":    '"{target}" site:.gov OR site:.mil',
    "crypto_wallets":   '"{target}" "bitcoin" OR "ethereum" OR "wallet address"',
}


def dork(query: str, max_results: int = 10) -> DorkResult:
    """Execute a search query via DuckDuckGo HTML."""
    try:
        resp = http_client.post(
            _DDG_URL,
            data={"q": query},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://duckduckgo.com/",
            },
            source="DuckDuckGo",
            timeout=20,
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for result in soup.select(".result")[:max_results]:
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            url_el = result.select_one(".result__url")
            if title_el:
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": title_el.get("href", ""),
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    "display_url": url_el.get_text(strip=True) if url_el else "",
                })
        return DorkResult(query=query, engine="DuckDuckGo", results=results)
    except Exception as e:
        return DorkResult(query=query, engine="DuckDuckGo", error=str(e))


def dork_target(target: str, dork_type: str = "news") -> DorkResult:
    """Run a predefined dork template against a target."""
    template = DORK_TEMPLATES.get(dork_type, '"{target}"')
    query = template.replace("{target}", target)
    return dork(query)


def run_all_dorks(target: str) -> dict[str, DorkResult]:
    """Run all predefined dork templates against a target."""
    return {name: dork_target(target, name) for name in DORK_TEMPLATES}
