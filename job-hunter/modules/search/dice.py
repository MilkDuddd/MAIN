"""Dice.com job scraper (tech/IT focused)."""

from __future__ import annotations
import json
from urllib.parse import quote_plus

from .base import BaseScraper, JobListing


class DiceScraper(BaseScraper):
    PLATFORM = "dice"
    _API = "https://job-search-api.svc.dhigroupinc.com/v1/dice/jobs/search"

    def search(
        self,
        keywords: str,
        location: str = "",
        job_type: str | None = None,
        remote_only: bool = False,
        max_results: int = 50,
    ) -> list[JobListing]:
        results: list[JobListing] = []
        page = 1
        per_page = 20

        jt_map = {"full-time": "FULLTIME", "part-time": "PARTTIME", "contract": "CONTRACTS", "internship": "INTERN"}

        while len(results) < max_results:
            try:
                params: dict = {
                    "q": keywords,
                    "countryCode2": "US",
                    "radius": "30",
                    "radiusUnit": "mi",
                    "page": page,
                    "pageSize": per_page,
                    "filters.postedDate": "ONE_WEEK",
                    "language": "en",
                }
                if location and not remote_only:
                    params["location"] = location
                if remote_only:
                    params["filters.workplaceTypes"] = "Remote"
                if job_type and jt_map.get(job_type):
                    params["filters.employmentType"] = jt_map[job_type]

                resp = self._get_session().get(self._API, params=params, headers={"Accept": "application/json", "x-api-key": "1YAt0R9wBg4WfsF9VB2778F5CHLAPMVW3WAZcKd8"})
                resp.raise_for_status()
                data = resp.json()
                jobs_data = data.get("data", [])
                if not jobs_data:
                    break

                for item in jobs_data:
                    results.append(self._parse_item(item))

                page += 1
                if len(jobs_data) < per_page:
                    break
            except Exception:
                break

        return results[:max_results]

    def _parse_item(self, item: dict) -> JobListing:
        salary = item.get("salary", "")
        sal_min = sal_max = None
        if salary:
            import re
            nums = re.findall(r"\d[\d,]*", salary)
            if len(nums) >= 2:
                sal_min = int(nums[0].replace(",", ""))
                sal_max = int(nums[1].replace(",", ""))

        return JobListing(
            platform=self.PLATFORM,
            external_id=item.get("id", ""),
            title=item.get("title", ""),
            company=item.get("companyPageUrl", {}) if isinstance(item.get("companyPageUrl"), str) else item.get("advertiserName", ""),
            location=item.get("location", ""),
            remote=item.get("workplaceTypes", "") == "Remote" or "remote" in item.get("location", "").lower(),
            job_type=item.get("employmentType", ""),
            salary_min=sal_min,
            salary_max=sal_max,
            salary_text=salary,
            description=item.get("jobDescription", ""),
            apply_url=f"https://www.dice.com/job-detail/{item.get('id', '')}",
            easy_apply=bool(item.get("easyApply")),
            posted_date=item.get("postedDate", ""),
        )
