"""Auto-apply engine using Playwright for browser automation."""

from __future__ import annotations
import time
from datetime import datetime
from typing import Callable, Optional

from core.database import execute, execute_write
from modules.profile.profile_manager import get_profile
from modules.search.aggregator import search_all


class AutoApplyEngine:
    """
    Searches for jobs, scores them, and auto-fills application forms
    using Playwright browser automation.
    """

    def __init__(
        self,
        profile_id: int,
        keywords: str,
        location: str = "",
        platforms: list[str] | None = None,
        job_type: str | None = None,
        remote_only: bool = False,
        easy_apply_only: bool = True,
        skip_duplicates: bool = True,
        generate_cover_letter: bool = True,
        daily_limit: int = 20,
        delay_seconds: float = 3.0,
        log_callback: Callable[[str, str], None] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        stop_check: Callable[[], bool] | None = None,
    ):
        self.profile_id = profile_id
        self.keywords = keywords
        self.location = location
        self.platforms = platforms or ["indeed", "linkedin", "dice", "ziprecruiter"]
        self.job_type = job_type
        self.remote_only = remote_only
        self.easy_apply_only = easy_apply_only
        self.skip_duplicates = skip_duplicates
        self.generate_cover_letter = generate_cover_letter
        self.daily_limit = daily_limit
        self.delay_seconds = delay_seconds
        self._log = log_callback or (lambda msg, lvl="info": None)
        self._progress = progress_callback or (lambda a, t: None)
        self._stop = stop_check or (lambda: False)
        self._applied = 0

    def run(self):
        self._log("Loading profile…", "info")
        profile = get_profile(self.profile_id)
        if not profile:
            self._log("Profile not found — aborting.", "error")
            return

        self._log(f"Profile loaded: {profile.get('name')}", "success")
        self._log(f"Searching {', '.join(self.platforms)} for: '{self.keywords}'…", "info")

        jobs = search_all(
            keywords=self.keywords,
            location=self.location,
            platforms=self.platforms,
            job_type=self.job_type,
            remote_only=self.remote_only,
            max_per_platform=40,
        )
        self._log(f"Found {len(jobs)} matching jobs.", "info")

        if self.easy_apply_only:
            jobs = [j for j in jobs if j.get("easy_apply")]
            self._log(f"After easy-apply filter: {len(jobs)} jobs.", "info")

        if self.skip_duplicates:
            existing_ids = {
                row["job_id"]
                for row in execute("SELECT job_id FROM applications WHERE profile_id=?", (self.profile_id,))
            }
            jobs = [j for j in jobs if j.get("db_id") not in existing_ids]
            self._log(f"After duplicate filter: {len(jobs)} jobs.", "info")

        jobs = jobs[:self.daily_limit]
        self._log(f"Will apply to {len(jobs)} jobs (limit: {self.daily_limit}).", "info")
        self._progress(0, len(jobs))

        for i, job in enumerate(jobs):
            if self._stop():
                self._log("Stopped by user.", "warn")
                break

            self._log(f"[{i+1}/{len(jobs)}] Applying to: {job.get('title')} at {job.get('company')}…", "info")

            cover_letter = ""
            if self.generate_cover_letter:
                cover_letter = self._gen_cover_letter(profile, job)

            success = self._apply_to_job(profile, job, cover_letter)

            if success:
                self._record_application(job, cover_letter)
                self._applied += 1
                self._log(f"  ✓ Applied successfully!", "success")
            else:
                self._log(f"  ✗ Could not auto-apply — recorded as manual.", "warn")
                self._record_application(job, cover_letter, manual=True)

            self._progress(self._applied, len(jobs))

            if i < len(jobs) - 1 and not self._stop():
                time.sleep(self.delay_seconds)

        self._log(f"Done. Applied to {self._applied} jobs.", "success")

    def _apply_to_job(self, profile: dict, job: dict, cover_letter: str) -> bool:
        platform = job.get("platform", "")
        apply_url = job.get("apply_url", "")
        if not apply_url:
            return False

        try:
            if platform == "linkedin" and job.get("easy_apply"):
                return self._apply_linkedin(profile, job, cover_letter)
            elif platform == "indeed" and job.get("easy_apply"):
                return self._apply_indeed(profile, job, cover_letter)
            else:
                return self._apply_generic(profile, job, cover_letter)
        except Exception as e:
            self._log(f"  Apply error: {e}", "error")
            return False

    def _apply_linkedin(self, profile: dict, job: dict, cover_letter: str) -> bool:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(job["apply_url"], timeout=20000)
                page.wait_for_timeout(2000)

                # Click Easy Apply button
                easy_btn = page.query_selector("button.jobs-apply-button")
                if easy_btn:
                    easy_btn.click()
                    page.wait_for_timeout(1500)

                    # Fill phone if asked
                    phone_input = page.query_selector("input[id*='phone']")
                    if phone_input and profile.get("phone"):
                        phone_input.fill(profile["phone"])

                    # Continue through modal steps
                    for _ in range(5):
                        next_btn = page.query_selector("button[aria-label='Continue to next step'], button[aria-label='Review your application'], button[aria-label='Submit application']")
                        if not next_btn:
                            break
                        label = next_btn.get_attribute("aria-label") or ""
                        next_btn.click()
                        page.wait_for_timeout(1000)
                        if "Submit" in label:
                            browser.close()
                            return True

                browser.close()
                return False
        except ImportError:
            self._log("  Playwright not installed. Run: pip install playwright && playwright install chromium", "warn")
            return False
        except Exception as e:
            self._log(f"  LinkedIn apply error: {e}", "error")
            return False

    def _apply_indeed(self, profile: dict, job: dict, cover_letter: str) -> bool:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(job["apply_url"], timeout=20000)
                page.wait_for_timeout(2000)

                apply_btn = page.query_selector("button#indeedApplyButton, a.ia-IndeedApplyButton")
                if not apply_btn:
                    browser.close()
                    return False

                apply_btn.click()
                page.wait_for_timeout(2000)

                # Fill basic fields
                for selector, value in [
                    ("input[name='applicant.name']", profile.get("name", "")),
                    ("input[name='applicant.emailAddress']", profile.get("email", "")),
                    ("input[name='applicant.phoneNumber']", profile.get("phone", "")),
                ]:
                    el = page.query_selector(selector)
                    if el and value:
                        el.fill(value)

                # Submit
                submit_btn = page.query_selector("button[type='submit']")
                if submit_btn:
                    submit_btn.click()
                    page.wait_for_timeout(1500)
                    browser.close()
                    return True

                browser.close()
                return False
        except ImportError:
            self._log("  Playwright not installed.", "warn")
            return False
        except Exception as e:
            self._log(f"  Indeed apply error: {e}", "error")
            return False

    def _apply_generic(self, profile: dict, job: dict, cover_letter: str) -> bool:
        # For non-easy-apply, record the URL was visited and mark as manual
        return False

    def _gen_cover_letter(self, profile: dict, job: dict) -> str:
        from core.settings import get
        api_key = get("anthropic_api_key")
        if not api_key:
            return ""
        try:
            from modules.ai.cover_letter import generate_cover_letter
            return generate_cover_letter(
                api_key=api_key,
                profile=profile,
                role=job.get("title", ""),
                company=job.get("company", ""),
                tone="Professional",
                length="Short (1 paragraph)",
                job_description=job.get("description", ""),
            )
        except Exception:
            return ""

    def _record_application(self, job: dict, cover_letter: str, manual: bool = False):
        now = datetime.utcnow().isoformat()
        job_id = job.get("db_id")
        if not job_id:
            return
        try:
            execute_write(
                """INSERT OR IGNORE INTO applications
                   (profile_id, job_id, status, cover_letter, applied_at, last_updated, auto_applied)
                   VALUES (?,?,?,?,?,?,?)""",
                (self.profile_id, job_id, "applied", cover_letter, now, now, int(not manual)),
            )
        except Exception:
            pass
