"""Base class and shared types for job search scrapers."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class JobListing:
    platform: str
    title: str
    company: str
    external_id: str = ""
    location: str = ""
    remote: bool = False
    job_type: str = ""
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_text: str = ""
    description: str = ""
    requirements: str = ""
    apply_url: str = ""
    easy_apply: bool = False
    posted_date: str = ""
    match_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "external_id": self.external_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "remote": int(self.remote),
            "job_type": self.job_type,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_text": self.salary_text,
            "description": self.description,
            "requirements": self.requirements,
            "apply_url": self.apply_url,
            "easy_apply": int(self.easy_apply),
            "posted_date": self.posted_date,
            "match_score": self.match_score,
        }


class BaseScraper:
    PLATFORM = "base"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self._session = None

    def _get_session(self):
        if self._session is None:
            import httpx
            self._session = httpx.Client(
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                follow_redirects=True,
            )
        return self._session

    def search(
        self,
        keywords: str,
        location: str = "",
        job_type: str | None = None,
        remote_only: bool = False,
        max_results: int = 50,
    ) -> list[JobListing]:
        raise NotImplementedError

    def close(self):
        if self._session:
            self._session.close()
            self._session = None
