"""Search aggregator — runs all scrapers in parallel and deduplicates results."""

from __future__ import annotations
import concurrent.futures
from datetime import datetime

from core.database import execute_write, execute
from .base import JobListing
from .indeed import IndeedScraper
from .linkedin import LinkedInScraper
from .glassdoor import GlassdoorScraper
from .dice import DiceScraper
from .ziprecruiter import ZipRecruiterScraper
from .remoteok import RemoteOKScraper

SCRAPERS = {
    "indeed": IndeedScraper,
    "linkedin": LinkedInScraper,
    "glassdoor": GlassdoorScraper,
    "dice": DiceScraper,
    "ziprecruiter": ZipRecruiterScraper,
    "remoteok": RemoteOKScraper,
}


def search_all(
    keywords: str,
    location: str = "",
    platforms: list[str] | None = None,
    job_type: str | None = None,
    remote_only: bool = False,
    max_per_platform: int = 30,
) -> list[dict]:
    if platforms is None:
        platforms = list(SCRAPERS.keys())

    def _scrape(platform: str) -> list[JobListing]:
        cls = SCRAPERS.get(platform)
        if not cls:
            return []
        scraper = cls()
        try:
            return scraper.search(
                keywords=keywords,
                location=location,
                job_type=job_type,
                remote_only=remote_only,
                max_results=max_per_platform,
            )
        except Exception:
            return []
        finally:
            scraper.close()

    all_jobs: list[JobListing] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(platforms)) as pool:
        futures = {pool.submit(_scrape, p): p for p in platforms}
        for fut in concurrent.futures.as_completed(futures):
            all_jobs.extend(fut.result())

    # Score and save to DB, return as dicts with db_id
    now = datetime.utcnow().isoformat()
    results = []
    seen = set()

    for job in all_jobs:
        key = (job.platform, job.external_id or job.title + job.company)
        if key in seen:
            continue
        seen.add(key)

        score = _match_score(job, keywords)
        job.match_score = score

        db_id = _upsert_job(job, now)
        d = job.to_dict()
        d["db_id"] = db_id
        results.append(d)

    results.sort(key=lambda r: r.get("match_score", 0), reverse=True)
    return results


def _match_score(job: JobListing, keywords: str) -> float:
    kws = [w.lower() for w in keywords.split() if len(w) > 2]
    if not kws:
        return 0.5
    text = f"{job.title} {job.description}".lower()
    hits = sum(1 for kw in kws if kw in text)
    score = hits / len(kws)
    if job.easy_apply:
        score += 0.1
    if job.remote:
        score += 0.05
    return min(score, 1.0)


def _upsert_job(job: JobListing, now: str) -> int:
    existing = execute(
        "SELECT id FROM job_listings WHERE platform=? AND external_id=?",
        (job.platform, job.external_id),
    )
    if existing:
        execute_write(
            """UPDATE job_listings SET title=?, company=?, location=?, remote=?, job_type=?,
               salary_min=?, salary_max=?, salary_text=?, description=?, apply_url=?,
               easy_apply=?, match_score=?, collected_at=? WHERE platform=? AND external_id=?""",
            (job.title, job.company, job.location, int(job.remote), job.job_type,
             job.salary_min, job.salary_max, job.salary_text, job.description, job.apply_url,
             int(job.easy_apply), job.match_score, now, job.platform, job.external_id),
        )
        return existing[0]["id"]

    return execute_write(
        """INSERT INTO job_listings
           (platform, external_id, title, company, location, remote, job_type,
            salary_min, salary_max, salary_text, description, apply_url,
            easy_apply, posted_date, match_score, collected_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (job.platform, job.external_id, job.title, job.company, job.location,
         int(job.remote), job.job_type, job.salary_min, job.salary_max, job.salary_text,
         job.description, job.apply_url, int(job.easy_apply),
         job.posted_date, job.match_score, now),
    )
