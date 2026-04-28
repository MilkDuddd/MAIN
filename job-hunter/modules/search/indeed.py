"""Indeed job scraper via their unofficial JSON API."""

from __future__ import annotations
import json
import re
from urllib.parse import quote_plus

from .base import BaseScraper, JobListing


class IndeedScraper(BaseScraper):
    PLATFORM = "indeed"
    _BASE = "https://www.indeed.com"

    def search(
        self,
        keywords: str,
        location: str = "",
        job_type: str | None = None,
        remote_only: bool = False,
        max_results: int = 50,
    ) -> list[JobListing]:
        results: list[JobListing] = []
        start = 0
        per_page = 15

        jt_map = {"full-time": "fulltime", "part-time": "parttime", "contract": "contract", "internship": "internship"}
        jt_param = jt_map.get(job_type or "", "")

        loc = "remote" if remote_only else location

        while len(results) < max_results:
            try:
                params = {
                    "q": keywords,
                    "l": loc,
                    "start": start,
                    "limit": per_page,
                    "fromage": "14",
                }
                if jt_param:
                    params["jt"] = jt_param
                if remote_only:
                    params["remotejob"] = "032b3046-06a3-4876-8dfd-474eb5e7ed11"

                url = f"{self._BASE}/jobs?" + "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
                resp = self._get_session().get(url)
                resp.raise_for_status()
                html = resp.text
                jobs = self._parse_html(html)
                if not jobs:
                    break
                results.extend(jobs)
                start += per_page
                if start >= max_results:
                    break
            except Exception:
                break

        return results[:max_results]

    def _parse_html(self, html: str) -> list[JobListing]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for card in soup.select("div.job_seen_beacon, div[data-jk]"):
            try:
                job_id = card.get("data-jk", "")
                title_el = card.select_one("h2.jobTitle span, a.jcs-JobTitle")
                title = title_el.get_text(strip=True) if title_el else ""
                company_el = card.select_one("span.companyName, [data-testid='company-name']")
                company = company_el.get_text(strip=True) if company_el else ""
                loc_el = card.select_one("div.companyLocation, [data-testid='text-location']")
                location = loc_el.get_text(strip=True) if loc_el else ""
                salary_el = card.select_one("div.salary-snippet-container, [data-testid='attribute_snippet_testid']")
                salary_text = salary_el.get_text(strip=True) if salary_el else ""
                desc_el = card.select_one("div.job-snippet")
                description = desc_el.get_text(strip=True) if desc_el else ""
                date_el = card.select_one("span.date")
                posted = date_el.get_text(strip=True) if date_el else ""
                apply_url = f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else ""
                remote = "remote" in location.lower()

                if not title or not company:
                    continue

                listings.append(JobListing(
                    platform=self.PLATFORM,
                    external_id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    remote=remote,
                    salary_text=salary_text,
                    description=description,
                    apply_url=apply_url,
                    posted_date=posted,
                ))
            except Exception:
                continue

        return listings
