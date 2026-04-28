"""Job Search page — search across multiple platforms."""

import json
import threading
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from core.database import execute, execute_write


PLATFORM_LABELS = {
    "indeed":       "Indeed",
    "linkedin":     "LinkedIn",
    "glassdoor":    "Glassdoor",
    "dice":         "Dice",
    "ziprecruiter": "ZipRecruiter",
    "remoteok":     "RemoteOK",
}


class SearchPage(ctk.CTkFrame):
    def __init__(self, parent, colors: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=colors["content_bg"], **kwargs)
        self.colors = colors
        self.nav_callback = nav_callback
        self._results: list = []
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkLabel(hdr, text="Job Search", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.colors["text"]).pack(side="left")

        # Search bar area
        search_panel = ctk.CTkFrame(self, fg_color=self.colors["panel_bg"], corner_radius=8)
        search_panel.pack(fill="x", padx=28, pady=(0, 12))

        row1 = ctk.CTkFrame(search_panel, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(12, 6))

        self._keywords = ctk.StringVar()
        kw_entry = ctk.CTkEntry(
            row1, textvariable=self._keywords, placeholder_text="Job title, skills, keywords…",
            fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=38, width=320,
        )
        kw_entry.pack(side="left", padx=(0, 8))
        kw_entry.bind("<Return>", lambda e: self._run_search())

        self._location = ctk.StringVar()
        ctk.CTkEntry(
            row1, textvariable=self._location, placeholder_text="Location (city, state, 'remote')…",
            fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=38, width=240,
        ).pack(side="left", padx=(0, 8))

        self._job_type = ctk.StringVar(value="Any")
        ctk.CTkComboBox(
            row1, variable=self._job_type,
            values=["Any", "Full-time", "Part-time", "Contract", "Internship"],
            fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=38, width=140,
        ).pack(side="left", padx=(0, 8))

        self._search_btn = ctk.CTkButton(
            row1, text="Search", width=110, height=38,
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
            command=self._run_search,
        )
        self._search_btn.pack(side="left")

        # Platform toggles
        row2 = ctk.CTkFrame(search_panel, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(row2, text="Platforms:", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(side="left", padx=(0, 8))
        self._platform_vars: dict[str, ctk.BooleanVar] = {}
        for key, label in PLATFORM_LABELS.items():
            var = ctk.BooleanVar(value=True)
            self._platform_vars[key] = var
            ctk.CTkCheckBox(row2, text=label, variable=var, font=ctk.CTkFont(size=11), text_color=self.colors["text"]).pack(side="left", padx=6)

        self._remote_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(row2, text="Remote only", variable=self._remote_var, font=ctk.CTkFont(size=11), text_color=self.colors["text"]).pack(side="left", padx=12)

        # Results area
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=4)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Left: results list
        left = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        list_hdr = ctk.CTkFrame(left, fg_color="transparent")
        list_hdr.pack(fill="x", padx=12, pady=(10, 4))
        self._result_count_label = ctk.CTkLabel(list_hdr, text="Results", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"])
        self._result_count_label.pack(side="left")

        self._sort_var = ctk.StringVar(value="Relevance")
        ctk.CTkComboBox(
            list_hdr, variable=self._sort_var,
            values=["Relevance", "Date (newest)", "Salary (high)", "Company A-Z"],
            width=130, height=26, fg_color=self.colors["content_bg"], border_color=self.colors["border"],
            command=lambda v: self._render_results(),
        ).pack(side="right")

        ctk.CTkFrame(left, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=8)
        self._results_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._results_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Right: detail panel
        right = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew")
        self._detail_panel = right
        self._show_empty_detail()

        # Status bar
        self._status_var = ctk.StringVar(value="Enter keywords and click Search")
        ctk.CTkLabel(self, textvariable=self._status_var, font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w", padx=28, pady=(4, 8))

        self._load_saved_jobs()

    def _run_search(self):
        keywords = self._keywords.get().strip()
        if not keywords:
            messagebox.showwarning("Required", "Enter keywords to search.")
            return
        platforms = [k for k, v in self._platform_vars.items() if v.get()]
        if not platforms:
            messagebox.showwarning("Required", "Select at least one platform.")
            return

        self._search_btn.configure(state="disabled", text="Searching…")
        self._status_var.set("Searching across platforms…")

        def _worker():
            try:
                from modules.search.aggregator import search_all
                results = search_all(
                    keywords=keywords,
                    location=self._location.get().strip(),
                    platforms=platforms,
                    job_type=self._job_type.get().lower() if self._job_type.get() != "Any" else None,
                    remote_only=self._remote_var.get(),
                )
                self._results = results
                self.after(0, self._on_search_done, len(results))
            except Exception as e:
                self.after(0, self._on_search_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_search_done(self, count: int):
        self._search_btn.configure(state="normal", text="Search")
        self._status_var.set(f"Found {count} jobs across selected platforms")
        self._render_results()

    def _on_search_error(self, msg: str):
        self._search_btn.configure(state="normal", text="Search")
        self._status_var.set(f"Error: {msg}")
        messagebox.showerror("Search Error", msg)

    def _render_results(self):
        for w in self._results_scroll.winfo_children():
            w.destroy()

        results = list(self._results)
        sort = self._sort_var.get()
        if sort == "Date (newest)":
            results.sort(key=lambda r: r.get("posted_date") or "", reverse=True)
        elif sort == "Salary (high)":
            results.sort(key=lambda r: r.get("salary_max") or 0, reverse=True)
        elif sort == "Company A-Z":
            results.sort(key=lambda r: r.get("company") or "")
        else:
            results.sort(key=lambda r: r.get("match_score") or 0, reverse=True)

        self._result_count_label.configure(text=f"{len(results)} Results")

        if not results:
            ctk.CTkLabel(self._results_scroll, text="No results.\nTry different keywords or platforms.",
                         font=ctk.CTkFont(size=12), text_color=self.colors["text_muted"], justify="center").pack(expand=True, pady=40)
            return

        for job in results:
            self._result_card(job)

    def _result_card(self, job: dict):
        card = ctk.CTkFrame(self._results_scroll, fg_color=self.colors["content_bg"], corner_radius=6, cursor="hand2")
        card.pack(fill="x", pady=3)
        card.bind("<Button-1>", lambda e, j=job: self._show_detail(j))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=job.get("title", ""), font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"], anchor="w").pack(side="left", fill="x", expand=True)

        if job.get("easy_apply"):
            ctk.CTkLabel(top, text=" Easy Apply ", font=ctk.CTkFont(size=9), fg_color=self.colors["accent"], corner_radius=4, text_color="#ffffff").pack(side="right")

        sub = ctk.CTkFrame(inner, fg_color="transparent")
        sub.pack(fill="x")
        platform_tag = job.get("platform", "")
        location_str = job.get("location") or ("Remote" if job.get("remote") else "")
        meta = f"{job.get('company', '')}  ·  {platform_tag}  ·  {location_str}"
        ctk.CTkLabel(sub, text=meta, font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(side="left")

        if job.get("salary_text"):
            ctk.CTkLabel(inner, text=job["salary_text"], font=ctk.CTkFont(size=11), text_color=self.colors["success"]).pack(anchor="w")

    def _show_detail(self, job: dict):
        for w in self._detail_panel.winfo_children():
            w.destroy()

        scroll = ctk.CTkScrollableFrame(self._detail_panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(scroll, text=job.get("title", ""), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text"], wraplength=400, justify="left").pack(anchor="w")
        ctk.CTkLabel(scroll, text=job.get("company", ""), font=ctk.CTkFont(size=14), text_color=self.colors["text_muted"]).pack(anchor="w", pady=(2, 4))

        tags = ctk.CTkFrame(scroll, fg_color="transparent")
        tags.pack(anchor="w", pady=4)
        for tag, color in [
            (job.get("platform", "").capitalize(), self.colors["tag_bg"]),
            (job.get("location") or ("Remote" if job.get("remote") else ""), self.colors["panel_bg"]),
            (job.get("job_type") or "", self.colors["panel_bg"]),
        ]:
            if tag:
                ctk.CTkLabel(tags, text=f"  {tag}  ", font=ctk.CTkFont(size=11), fg_color=color, corner_radius=4, text_color=self.colors["text"]).pack(side="left", padx=(0, 6))

        if job.get("salary_text"):
            ctk.CTkLabel(scroll, text=job["salary_text"], font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["success"]).pack(anchor="w", pady=4)

        ctk.CTkFrame(scroll, height=1, fg_color=self.colors["border"]).pack(fill="x", pady=8)

        desc = job.get("description") or "No description available."
        ctk.CTkLabel(scroll, text=desc, font=ctk.CTkFont(size=12), text_color=self.colors["text"], wraplength=440, justify="left").pack(anchor="w")

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(anchor="w", pady=12)

        ctk.CTkButton(
            btn_row, text="⚡ Apply Now", width=120, height=34,
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
            command=lambda j=job: self._apply_to_job(j),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="↗ Open URL", width=100, height=34,
            fg_color=self.colors["panel_bg"],
            command=lambda url=job.get("apply_url", ""): self._open_url(url),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="✉ Cover Letter", width=130, height=34,
            fg_color=self.colors["panel_bg"],
            command=lambda j=job: self._gen_cover_letter(j),
        ).pack(side="left")

    def _show_empty_detail(self):
        ctk.CTkLabel(
            self._detail_panel,
            text="Select a job to view details",
            font=ctk.CTkFont(size=14),
            text_color=self.colors["text_muted"],
        ).pack(expand=True)

    def _apply_to_job(self, job: dict):
        from core.settings import get
        profile_id = get("default_profile_id")
        if not profile_id:
            messagebox.showwarning("No Profile", "Set up a profile first.")
            return

        job_id = job.get("db_id")
        if not job_id:
            messagebox.showwarning("Save First", "Job must be searched/saved before applying.")
            return

        try:
            existing = execute("SELECT id FROM applications WHERE profile_id=? AND job_id=?", (profile_id, job_id))
            if existing:
                messagebox.showinfo("Already Applied", "You already have an application for this job.")
                return

            now = datetime.utcnow().isoformat()
            execute_write(
                "INSERT INTO applications (profile_id, job_id, status, applied_at, last_updated) VALUES (?,?,?,?,?)",
                (profile_id, job_id, "applied", now, now),
            )
            messagebox.showinfo("Applied!", f"Application recorded for:\n{job.get('title')} at {job.get('company')}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _open_url(self, url: str):
        if url:
            import webbrowser
            webbrowser.open(url)
        else:
            messagebox.showinfo("No URL", "No apply URL available.")

    def _gen_cover_letter(self, job: dict):
        if self.nav_callback:
            self.nav_callback("cover_letter")

    def _load_saved_jobs(self):
        try:
            rows = execute("SELECT * FROM job_listings ORDER BY collected_at DESC LIMIT 100")
            self._results = [dict(r) | {"db_id": r["id"]} for r in rows]
            self._render_results()
        except Exception:
            pass

    def on_show(self):
        self._load_saved_jobs()
