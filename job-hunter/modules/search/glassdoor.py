"""Glassdoor job scraper."""

from __future__ import annotations
import json
import re
from urllib.parse import quote_plus

from .base import BaseScraper, JobListing


class GlassdoorScraper(BaseScraper):
    PLATFORM = "glassdoor"
    _BASE = "https://www.glassdoor.com"

    def search(
        self,
        keywords: str,
        location: str = "",
        job_type: str | None = None,
        remote_only: bool = False,
        max_results: int = 50,
    ) -> list[JobListing]:
        results: list[JobListing] = []
        try:
            loc_part = f"jobs/{quote_plus(location.replace(' ', '-').lower())}" if location and not remote_only else "jobs/remote"
            url = f"{self._BASE}/{loc_part}/{quote_plus(keywords.replace(' ', '-').lower())}-jobs-SRCH_IL.0,0_KO0,20.htm"
            resp = self._get_session().get(url)
            resp.raise_for_status()
            results = self._parse(resp.text)
        except Exception:
            pass
        return results[:max_results]

    def _parse(self, html: str) -> list[JobListing]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for card in soup.select("li.JobsList_jobListItem__wjTHv, li[data-id]"):
            try:
                job_id = card.get("data-id", card.get("data-job-id", ""))
                title_el = card.select_one("a.JobCard_seoLink__WdqHZ, a[data-test='job-title']")
                title = title_el.get_text(strip=True) if title_el else ""
                company_el = card.select_one("div.EmployerProfile_employerName__Xemli, span.EmployerProfile_compactEmployerName__LE242")
                company = company_el.get_text(strip=True) if company_el else ""
                loc_el = card.select_one("div.JobCard_location__Ds1fM")
                location = loc_el.get_text(strip=True) if loc_el else ""
                salary_el = card.select_one("div.JobCard_salaryEstimate___m9kY")
                salary_text = salary_el.get_text(strip=True) if salary_el else ""
                apply_url = self._BASE + title_el.get("href", "") if title_el and title_el.get("href") else ""
                remote = "remote" in location.lower()

                if not title:
                    continue

                listings.append(JobListing(
                    platform=self.PLATFORM,
                    external_id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    remote=remote,
                    salary_text=salary_text,
                    apply_url=apply_url,
                ))
            except Exception:
                continue

        return listings
