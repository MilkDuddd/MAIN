"""Rate-limited HTTP client with retry logic."""

import random
import time
from collections import defaultdict
from threading import Lock
from typing import Any, Optional

import httpx

from .config import DEFAULT_TIMEOUT, MAX_RETRIES, RETRY_BACKOFF, USER_AGENTS
from .exceptions import APIError, RateLimitError


class _RateLimiter:
    """Simple token bucket rate limiter per domain."""
    def __init__(self):
        self._locks: dict[str, Lock] = defaultdict(Lock)
        self._last: dict[str, float] = {}
        self._min_interval: dict[str, float] = {}

    def configure(self, domain: str, min_interval_sec: float) -> None:
        self._min_interval[domain] = min_interval_sec

    def wait(self, domain: str) -> None:
        interval = self._min_interval.get(domain, 0.5)
        with self._locks[domain]:
            now = time.monotonic()
            last = self._last.get(domain, 0.0)
            wait_time = interval - (now - last)
            if wait_time > 0:
                time.sleep(wait_time)
            self._last[domain] = time.monotonic()


_rate_limiter = _RateLimiter()

# Configure per-domain rate limits
_rate_limiter.configure("query.wikidata.org", 1.0)
_rate_limiter.configure("api.gdeltproject.org", 2.0)
_rate_limiter.configure("crt.sh", 1.0)
_rate_limiter.configure("opensky-network.org", 5.0)
_rate_limiter.configure("nuforc.org", 2.0)
_rate_limiter.configure("api.shodan.io", 1.0)
_rate_limiter.configure("newsapi.org", 0.5)
_rate_limiter.configure("api.opencorporates.com", 2.0)
_rate_limiter.configure("api.open.fec.gov", 1.0)
_rate_limiter.configure("api.sam.gov", 1.0)
_rate_limiter.configure("api.acleddata.com", 1.0)
_rate_limiter.configure("api.reliefweb.int", 1.0)
_rate_limiter.configure("data.fcc.gov", 0.5)


def _extract_domain(url: str) -> str:
    try:
        return url.split("//")[1].split("/")[0]
    except IndexError:
        return url


def get(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
    source: str = "",
) -> httpx.Response:
    """Rate-limited GET with exponential backoff retry."""
    domain = _extract_domain(url)
    _rate_limiter.wait(domain)

    base_headers = {"User-Agent": random.choice(USER_AGENTS)}
    if headers:
        base_headers.update(headers)

    last_err: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = httpx.get(url, params=params, headers=base_headers, timeout=timeout, follow_redirects=True)
            if resp.status_code == 429:
                wait = RETRY_BACKOFF ** (attempt + 1)
                time.sleep(wait)
                raise RateLimitError(source or domain, "Rate limited", 429)
            if resp.status_code >= 500:
                wait = RETRY_BACKOFF ** attempt
                time.sleep(wait)
                last_err = APIError(source or domain, resp.text[:200], resp.status_code)
                continue
            resp.raise_for_status()
            return resp
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            wait = RETRY_BACKOFF ** attempt
            time.sleep(wait)
            last_err = e
            continue
        except RateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            raise APIError(source or domain, str(e), e.response.status_code) from e

    raise APIError(source or domain, f"Failed after {MAX_RETRIES} attempts: {last_err}")


def post(
    url: str,
    json: Optional[dict] = None,
    data: Optional[Any] = None,
    headers: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT,
    source: str = "",
) -> httpx.Response:
    """Rate-limited POST with retry."""
    domain = _extract_domain(url)
    _rate_limiter.wait(domain)

    base_headers = {"User-Agent": random.choice(USER_AGENTS)}
    if headers:
        base_headers.update(headers)

    last_err: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = httpx.post(url, json=json, data=data, headers=base_headers, timeout=timeout)
            if resp.status_code == 429:
                time.sleep(RETRY_BACKOFF ** (attempt + 1))
                continue
            if resp.status_code >= 500:
                time.sleep(RETRY_BACKOFF ** attempt)
                last_err = APIError(source or domain, resp.text[:200], resp.status_code)
                continue
            resp.raise_for_status()
            return resp
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            time.sleep(RETRY_BACKOFF ** attempt)
            last_err = e
            continue
        except httpx.HTTPStatusError as e:
            raise APIError(source or domain, str(e), e.response.status_code) from e

    raise APIError(source or domain, f"Failed after {MAX_RETRIES} attempts: {last_err}")
