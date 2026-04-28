"""ZipRecruiter job scraper."""

from __future__ import annotations
from urllib.parse import quote_plus

from .base import BaseScraper, JobListing


class ZipRecruiterScraper(BaseScraper):
    PLATFORM = "ziprecruiter"
    _BASE = "https://www.ziprecruiter.com"
    _API = "https://api.ziprecruiter.com/jobs/v1"

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
            loc = "Remote" if remote_only else location
            url = f"{self._BASE}/jobs/search?search={quote_plus(keywords)}&location={quote_plus(loc)}&days=14"
            if job_type:
                url += f"&employment_type={quote_plus(job_type)}"
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

        for article in soup.select("article.job_result, div[data-job-id]"):
            try:
                job_id = article.get("data-job-id", "")
                title_el = article.select_one("h2.job_title, a.job_link")
                title = title_el.get_text(strip=True) if title_el else ""
                company_el = article.select_one("a.company_name, div.hiring_company")
                company = company_el.get_text(strip=True) if company_el else ""
                loc_el = article.select_one("span.location")
                location = loc_el.get_text(strip=True) if loc_el else ""
                salary_el = article.select_one("span.compensation")
                salary_text = salary_el.get_text(strip=True) if salary_el else ""
                link_el = article.select_one("a.job_link, a.jobLink")
                apply_url = link_el.get("href", "") if link_el else ""
                if apply_url and not apply_url.startswith("http"):
                    apply_url = self._BASE + apply_url

                if not title:
                    continue

                listings.append(JobListing(
                    platform=self.PLATFORM,
                    external_id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    remote="remote" in location.lower(),
                    salary_text=salary_text,
                    apply_url=apply_url,
                ))
            except Exception:
                continue

        return listings
