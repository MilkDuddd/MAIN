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
                self._record_application(job, cover_letter, auto_applied=True)
                self._applied += 1
                self._log("  ✓ Applied successfully!", "success")
            else:
                self._log("  ✗ Could not auto-apply — recorded as manual.", "warn")
                self._record_application(job, cover_letter, auto_applied=False)

            self._progress(self._applied, len(jobs))

            if i < len(jobs) - 1 and not self._stop():
                time.sleep(self.delay_seconds)

        self._log(f"Done. Applied to {self._applied} jobs.", "success")

    # ── Form Filling Helpers ──────────────────────────────────────────────────

    def _fill_common_fields(self, page, profile: dict) -> None:
        """
        Fill common form fields (name, email, phone, location, etc.).
        Tries multiple selector variants per field; silently skips missing fields.
        """
        name = profile.get("name", "")
        name_parts = name.strip().split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        # Compute years of experience from work history
        years_exp = self._compute_years_experience(profile)

        fill_map = [
            # First name
            (
                ["input[name*='firstName']", "input[id*='firstName']",
                 "input[autocomplete='given-name']", "input[placeholder*='First']"],
                first_name,
            ),
            # Last name
            (
                ["input[name*='lastName']", "input[id*='lastName']",
                 "input[autocomplete='family-name']", "input[placeholder*='Last']"],
                last_name,
            ),
            # Full name (some forms use a single field)
            (
                ["input[name='applicant.name']", "input[name='fullName']",
                 "input[id*='fullName']", "input[autocomplete='name']"],
                name,
            ),
            # Email
            (
                ["input[type='email']", "input[name*='email']", "input[id*='email']",
                 "input[name='applicant.emailAddress']", "input[autocomplete='email']"],
                profile.get("email", ""),
            ),
            # Phone
            (
                ["input[type='tel']", "input[name*='phone']", "input[id*='phone']",
                 "input[name='applicant.phoneNumber']", "input[autocomplete='tel']"],
                profile.get("phone", ""),
            ),
            # Location / City
            (
                ["input[name*='city']", "input[id*='city']",
                 "input[name*='location']", "input[id*='location']",
                 "input[autocomplete='address-level2']", "input[placeholder*='City']"],
                profile.get("location", ""),
            ),
            # LinkedIn URL
            (
                ["input[name*='linkedin']", "input[id*='linkedin']",
                 "input[placeholder*='LinkedIn']", "input[placeholder*='linkedin']"],
                profile.get("linkedin_url", ""),
            ),
            # Years of experience
            (
                ["input[name*='yearsOfExperience']", "input[id*='experience']",
                 "input[placeholder*='years']", "input[name*='experience']"],
                years_exp,
            ),
            # Desired salary
            (
                ["input[name*='salary']", "input[id*='salary']",
                 "input[placeholder*='salary']", "input[placeholder*='compensation']"],
                profile.get("desired_salary", ""),
            ),
        ]

        for selectors, value in fill_map:
            if not value:
                continue
            for sel in selectors:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        el.fill(str(value))
                        break
                except Exception:
                    continue

        # Work authorization radio — click "Yes" / "Authorized" if present
        for auth_sel in [
            "input[type='radio'][value='yes']",
            "input[type='radio'][value='Yes']",
            "input[type='radio'][value='authorized']",
            "input[type='radio'][value='true']",
        ]:
            try:
                el = page.query_selector(auth_sel)
                if el and el.is_visible():
                    el.click()
                    break
            except Exception:
                continue

    def _inject_cover_letter(self, page, cover_letter: str) -> bool:
        """
        Find a cover letter textarea on the current page and fill it.
        Returns True if a field was found and filled.
        """
        if not cover_letter:
            return False

        # Ordered from most-specific to least-specific to avoid false positives
        selectors = [
            "textarea[id*='cover']",
            "textarea[name*='cover']",
            "textarea[aria-label*='cover']",
            "textarea[placeholder*='cover']",
            "textarea[id*='Cover']",
            "textarea[name*='Cover']",
            "textarea[name*='message']",
            "textarea[id*='message']",
            "textarea[placeholder*='message']",
        ]
        for sel in selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.fill(cover_letter)
                    self._log("  Cover letter injected into form.", "info")
                    return True
            except Exception:
                continue
        return False

    def _fill_required_selects(self, page) -> None:
        """Pick the first valid option in any visible required <select> dropdowns."""
        try:
            selects = page.query_selector_all("select[required], select[aria-required='true']")
            for sel_el in selects:
                try:
                    if not sel_el.is_visible():
                        continue
                    options = sel_el.query_selector_all("option")
                    for opt in options:
                        val = opt.get_attribute("value") or ""
                        if val and val.lower() not in ("", "0", "select", "placeholder", "none"):
                            sel_el.select_option(val)
                            break
                except Exception:
                    continue
        except Exception:
            pass

    def _compute_years_experience(self, profile: dict) -> str:
        experience = profile.get("experience") or []
        if not experience:
            return ""
        total_months = 0
        for exp in experience:
            start = exp.get("start_date", "")
            end_raw = exp.get("end_date", "")
            is_current = bool(exp.get("current"))
            if not start:
                continue
            try:
                from dateutil import parser as dparser
                from datetime import datetime as _dt
                s = dparser.parse(start, default=_dt(2000, 1, 1))
                e = dparser.parse(end_raw, default=_dt.utcnow()) if (end_raw and not is_current) else _dt.utcnow()
                total_months += max((e.year - s.year) * 12 + (e.month - s.month), 0)
            except Exception:
                continue
        years = round(total_months / 12)
        return str(max(years, 1)) if total_months else ""

    # ── Platform-specific Apply Methods ──────────────────────────────────────

    def _apply_to_job(self, profile: dict, job: dict, cover_letter: str) -> bool:
        platform = job.get("platform", "")
        apply_url = job.get("apply_url", "")
        if not apply_url:
            return False

        try:
            if platform == "linkedin" and job.get("easy_apply"):
                return self._apply_linkedin(profile, job, cover_letter)
            elif platform == "indeed":
                return self._apply_indeed(profile, job, cover_letter)
            else:
                return False
        except Exception as e:
            self._log(f"  Apply error: {e}", "error")
            return False

    def _apply_linkedin(self, profile: dict, job: dict, cover_letter: str) -> bool:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                page.goto(job["apply_url"], timeout=20000)
                page.wait_for_timeout(2000)

                # Click Easy Apply button
                easy_btn = page.query_selector("button.jobs-apply-button")
                if not easy_btn:
                    browser.close()
                    return False

                easy_btn.click()
                page.wait_for_timeout(1500)

                submitted = False
                for _step in range(10):
                    if self._stop():
                        break

                    # Fill all common fields on this step
                    self._fill_common_fields(page, profile)

                    # Inject cover letter if a textarea is present
                    self._inject_cover_letter(page, cover_letter)

                    # Handle resume file upload if prompted
                    upload_input = page.query_selector("input[type='file']")
                    if upload_input and profile.get("resume_file"):
                        try:
                            upload_input.set_input_files(profile["resume_file"])
                        except Exception:
                            pass

                    # Fill any required select dropdowns
                    self._fill_required_selects(page)

                    # Submit button — final step
                    submit_btn = page.query_selector("button[aria-label='Submit application']")
                    if submit_btn and submit_btn.is_visible():
                        submit_btn.click()
                        page.wait_for_timeout(1500)
                        submitted = True
                        break

                    # Next / Review button
                    next_btn = page.query_selector(
                        "button[aria-label='Continue to next step'], "
                        "button[aria-label='Review your application']"
                    )
                    if next_btn and next_btn.is_visible():
                        next_btn.click()
                        page.wait_for_timeout(1200)
                    else:
                        # No recognisable button — stop iterating
                        break

                browser.close()
                return submitted
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
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                page.goto(job["apply_url"], timeout=20000)
                page.wait_for_timeout(2000)

                apply_btn = page.query_selector(
                    "button#indeedApplyButton, "
                    "a.ia-IndeedApplyButton, "
                    "button[data-tn-element='apply-now-button']"
                )
                if not apply_btn:
                    browser.close()
                    return False

                apply_btn.click()
                page.wait_for_timeout(2000)

                # Indeed uses an iframe for its apply flow
                try:
                    frame = page.frame_locator(
                        "iframe[title*='apply'], iframe[src*='smartapply'], iframe[id*='apply']"
                    ).first
                    # Test if the frame is accessible
                    frame.locator("body").wait_for(timeout=3000)
                    target = frame
                except Exception:
                    target = page

                submitted = False
                for _step in range(8):
                    if self._stop():
                        break

                    self._fill_common_fields(target, profile)
                    self._inject_cover_letter(target, cover_letter)
                    self._fill_required_selects(target)

                    # Look for the final submit button
                    try:
                        submit_btn = target.locator(
                            "button[data-tn-element='submit-application-button'], "
                            "button:has-text('Submit'), button:has-text('Apply now')"
                        ).first
                        if submit_btn.is_visible():
                            submit_text = (submit_btn.inner_text() or "").lower()
                            if any(w in submit_text for w in ("submit", "apply")):
                                submit_btn.click()
                                page.wait_for_timeout(1500)
                                submitted = True
                                break
                    except Exception:
                        pass

                    # Next / Continue button
                    try:
                        next_btn = target.locator(
                            "button[data-tn-element='continue-button'], "
                            "button:has-text('Continue'), button:has-text('Next')"
                        ).first
                        if next_btn.is_visible():
                            next_btn.click()
                            page.wait_for_timeout(1200)
                            continue
                    except Exception:
                        pass

                    break

                browser.close()
                return submitted
        except ImportError:
            self._log("  Playwright not installed.", "warn")
            return False
        except Exception as e:
            self._log(f"  Indeed apply error: {e}", "error")
            return False

    # ── AI & DB helpers ───────────────────────────────────────────────────────

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

    def _record_application(self, job: dict, cover_letter: str, auto_applied: bool = False):
        now = datetime.utcnow().isoformat()
        job_id = job.get("db_id")
        if not job_id:
            return
        try:
            execute_write(
                """INSERT OR IGNORE INTO applications
                   (profile_id, job_id, status, cover_letter, applied_at, last_updated, auto_applied)
                   VALUES (?,?,?,?,?,?,?)""",
                (self.profile_id, job_id, "applied", cover_letter, now, now, int(auto_applied)),
            )
        except Exception:
            pass
