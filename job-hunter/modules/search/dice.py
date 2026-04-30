"""Dice.com job scraper (tech/IT focused).

Uses the Dice JSON API if DICE_API_KEY is set in the environment,
otherwise falls back to scraping the public HTML search results.
"""

from __future__ import annotations
import os
from urllib.parse import quote_plus

from .base import BaseScraper, JobListing


class DiceScraper(BaseScraper):
    PLATFORM = "dice"
    _API = "https://job-search-api.svc.dhigroupinc.com/v1/dice/jobs/search"
    _API_KEY = os.environ.get("DICE_API_KEY", "")

    def search(
        self,
        keywords: str,
        location: str = "",
        job_type: str | None = None,
        remote_only: bool = False,
        max_results: int = 50,
    ) -> list[JobListing]:
        if self._API_KEY:
            return self._search_api(keywords, location, job_type, remote_only, max_results)
        return self._search_html(keywords, location, remote_only, max_results)

    def _search_api(
        self,
        keywords: str,
        location: str,
        job_type: str | None,
        remote_only: bool,
        max_results: int,
    ) -> list[JobListing]:
        results: list[JobListing] = []
        page = 1
        per_page = 20

        jt_map = {
            "full-time": "FULLTIME",
            "part-time": "PARTTIME",
            "contract": "CONTRACTS",
            "internship": "INTERN",
        }

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

                resp = self._get_session().get(
                    self._API,
                    params=params,
                    headers={"Accept": "application/json", "x-api-key": self._API_KEY},
                )
                resp.raise_for_status()
                data = resp.json()
                jobs_data = data.get("data", [])
                if not jobs_data:
                    break

                for item in jobs_data:
                    results.append(self._parse_api_item(item))

                page += 1
                if len(jobs_data) < per_page:
                    break
            except Exception:
                # API failed — fall back to HTML for any remaining results
                if not results:
                    return self._search_html(keywords, location, remote_only, max_results)
                break

        return results[:max_results]

    def _search_html(
        self,
        keywords: str,
        location: str,
        remote_only: bool,
        max_results: int,
    ) -> list[JobListing]:
        from bs4 import BeautifulSoup

        results: list[JobListing] = []
        try:
            loc_param = "remote" if remote_only else quote_plus(location)
            url = (
                f"https://www.dice.com/jobs"
                f"?q={quote_plus(keywords)}"
                f"&location={loc_param}"
                f"&countryCode=US&radius=30&radiusUnit=mi&page=1&pageSize=20"
            )
            if remote_only:
                url += "&filters.workplaceTypes=Remote"

            resp = self._get_session().get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            for card in soup.select("div[data-cy='card'], dhi-job-card, div.card"):
                try:
                    title_el = card.select_one(
                        "a[data-cy='card-title-link'], h5.card-title, a.card-title-link"
                    )
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    company_el = card.select_one(
                        "a[data-cy='search-result-company-name'], span.employer-name, a.employer-name"
                    )
                    company = company_el.get_text(strip=True) if company_el else ""
                    loc_el = card.select_one(
                        "span[data-cy='search-result-location'], span.location"
                    )
                    location_text = loc_el.get_text(strip=True) if loc_el else ""
                    link = title_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://www.dice.com" + link
                    ext_id = link.rstrip("/").split("/")[-1] if link else ""

                    results.append(JobListing(
                        platform=self.PLATFORM,
                        external_id=ext_id,
                        title=title,
                        company=company,
                        location=location_text,
                        remote="remote" in location_text.lower() or remote_only,
                        apply_url=link,
                    ))
                    if len(results) >= max_results:
                        break
                except Exception:
                    continue
        except Exception:
            pass

        return results

    def _parse_api_item(self, item: dict) -> JobListing:
        salary = item.get("salary", "")
        sal_min = sal_max = None
        if salary:
            import re
            nums = re.findall(r"\d[\d,]*", salary)
            if len(nums) >= 2:
                sal_min = int(nums[0].replace(",", ""))
                sal_max = int(nums[1].replace(",", ""))

        company = item.get("advertiserName", "") or item.get("companyPageUrl", "")

        return JobListing(
            platform=self.PLATFORM,
            external_id=item.get("id", ""),
            title=item.get("title", ""),
            company=company,
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
