"""RemoteOK job scraper (remote jobs only)."""

from __future__ import annotations
import json

from .base import BaseScraper, JobListing


class RemoteOKScraper(BaseScraper):
    PLATFORM = "remoteok"
    _API = "https://remoteok.com/api"

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
            resp = self._get_session().get(self._API, headers={"Accept": "application/json"})
            resp.raise_for_status()
            data = resp.json()

            kw_lower = keywords.lower()
            kw_words = set(kw_lower.split())

            for item in data:
                if not isinstance(item, dict) or "id" not in item:
                    continue
                title = item.get("position", "")
                company = item.get("company", "")
                tags = " ".join(item.get("tags", []))
                combined = f"{title} {company} {tags}".lower()

                if not any(w in combined for w in kw_words):
                    continue

                salary_min = item.get("salary_min")
                salary_max = item.get("salary_max")
                salary_text = ""
                if salary_min and salary_max:
                    salary_text = f"${salary_min:,} – ${salary_max:,}"
                elif salary_min:
                    salary_text = f"${salary_min:,}+"

                results.append(JobListing(
                    platform=self.PLATFORM,
                    external_id=str(item.get("id", "")),
                    title=title,
                    company=company,
                    location="Remote",
                    remote=True,
                    job_type=job_type or "full-time",
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_text=salary_text,
                    description=item.get("description", ""),
                    apply_url=item.get("url", "") or item.get("apply_url", ""),
                    posted_date=item.get("date", ""),
                    easy_apply=bool(item.get("apply_url")),
                ))
                if len(results) >= max_results:
                    break
        except Exception:
            pass
        return results
