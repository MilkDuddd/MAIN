"""LinkedIn job scraper via public job search (no auth required)."""

from __future__ import annotations
import re
import time
from urllib.parse import quote_plus

from .base import BaseScraper, JobListing


class LinkedInScraper(BaseScraper):
    PLATFORM = "linkedin"
    _BASE = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    _DETAIL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"

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
        per_page = 25

        jt_map = {
            "full-time": "F",
            "part-time": "P",
            "contract": "C",
            "internship": "I",
        }
        f_jt = jt_map.get(job_type or "")
        f_wt = "2" if remote_only else None  # remote work type

        while len(results) < max_results:
            try:
                params = f"keywords={quote_plus(keywords)}&location={quote_plus(location)}&start={start}"
                if f_jt:
                    params += f"&f_JT={f_jt}"
                if f_wt:
                    params += f"&f_WT={f_wt}"

                url = f"{self._BASE}?{params}"
                resp = self._get_session().get(url)
                resp.raise_for_status()
                jobs = self._parse_list(resp.text)
                if not jobs:
                    break
                results.extend(jobs)
                start += per_page
                if start >= max_results:
                    break
                time.sleep(0.5)
            except Exception:
                break

        return results[:max_results]

    def _parse_list(self, html: str) -> list[JobListing]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        listings = []

        for li in soup.select("li"):
            try:
                job_id = li.select_one("div[data-entity-urn]")
                if job_id:
                    urn = job_id.get("data-entity-urn", "")
                    match = re.search(r":(\d+)$", urn)
                    ext_id = match.group(1) if match else ""
                else:
                    ext_id = ""

                title_el = li.select_one("h3.base-search-card__title")
                title = title_el.get_text(strip=True) if title_el else ""
                company_el = li.select_one("h4.base-search-card__subtitle")
                company = company_el.get_text(strip=True) if company_el else ""
                loc_el = li.select_one("span.job-search-card__location")
                location = loc_el.get_text(strip=True) if loc_el else ""
                date_el = li.select_one("time")
                posted = date_el.get("datetime", "") if date_el else ""
                link_el = li.select_one("a.base-card__full-link")
                apply_url = link_el.get("href", "") if link_el else ""

                if not title:
                    continue

                easy_apply = bool(li.select_one(".job-search-card__easy-apply"))
                remote = "remote" in location.lower()

                listings.append(JobListing(
                    platform=self.PLATFORM,
                    external_id=ext_id,
                    title=title,
                    company=company,
                    location=location,
                    remote=remote,
                    apply_url=apply_url,
                    easy_apply=easy_apply,
                    posted_date=posted,
                ))
            except Exception:
                continue

        return listings
