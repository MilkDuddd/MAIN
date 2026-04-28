"""Settings page."""

from tkinter import messagebox

import customtkinter as ctk

from core import settings


class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, colors: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=colors["content_bg"], **kwargs)
        self.colors = colors
        self.nav_callback = nav_callback
        self._cfg = settings.load()
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkLabel(hdr, text="Settings", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.colors["text"]).pack(side="left")

        tabs = ctk.CTkTabview(self, fg_color=self.colors["panel_bg"])
        tabs.pack(fill="both", expand=True, padx=28, pady=8)

        for tab in ("API Keys", "Auto Apply", "Platforms", "Search Defaults", "About"):
            tabs.add(tab)

        self._build_api_tab(tabs.tab("API Keys"))
        self._build_autoapply_tab(tabs.tab("Auto Apply"))
        self._build_platforms_tab(tabs.tab("Platforms"))
        self._build_search_tab(tabs.tab("Search Defaults"))
        self._build_about_tab(tabs.tab("About"))

    def _section(self, parent, title: str):
        ctk.CTkLabel(parent, text=title, font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=(16, 4))
        ctk.CTkFrame(parent, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=8, pady=(0, 8))

    def _field(self, parent, label: str, var: ctk.StringVar, ph: str = "", show: str = ""):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), text_color=self.colors["text"], width=200, anchor="w").pack(side="left")
        ctk.CTkEntry(row, textvariable=var, placeholder_text=ph, show=show, fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=32).pack(side="left", fill="x", expand=True)

    def _build_api_tab(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._section(scroll, "Anthropic (Claude AI)")
        self._ant_key = ctk.StringVar(value=self._cfg.get("anthropic_api_key", ""))
        self._field(scroll, "API Key", self._ant_key, "sk-ant-…")
        ctk.CTkLabel(scroll, text="Used for AI cover letter generation, job matching, and resume tailoring.",
                     font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w", padx=8)

        self._section(scroll, "LinkedIn (Optional)")
        li = self._cfg.get("platforms", {}).get("linkedin", {})
        self._li_key = ctk.StringVar(value=li.get("api_key", ""))
        self._field(scroll, "LinkedIn API Key", self._li_key, "Optional — enables richer search")

        ctk.CTkButton(scroll, text="Save API Keys", fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save_api).pack(anchor="e", padx=8, pady=12)

    def _build_autoapply_tab(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        aa = self._cfg.get("auto_apply", {})

        self._section(scroll, "Auto Apply Limits")

        self._daily_limit = ctk.StringVar(value=str(aa.get("daily_limit", 20)))
        self._delay = ctk.StringVar(value=str(aa.get("delay_seconds", 3)))
        self._field(scroll, "Daily Application Limit", self._daily_limit, "20")
        self._field(scroll, "Delay Between Apps (sec)", self._delay, "3")

        self._section(scroll, "Behaviour")
        self._easy_only = ctk.BooleanVar(value=aa.get("require_easy_apply", True))
        self._skip_dups = ctk.BooleanVar(value=aa.get("skip_if_already_applied", True))

        ctk.CTkCheckBox(scroll, text="Easy Apply only (faster, no redirects)", variable=self._easy_only, text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=6)
        ctk.CTkCheckBox(scroll, text="Skip jobs already in tracker", variable=self._skip_dups, text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=2)

        ctk.CTkButton(scroll, text="Save Auto Apply Settings", fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save_autoapply).pack(anchor="e", padx=8, pady=12)

    def _build_platforms_tab(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        plats = self._cfg.get("platforms", {})

        self._section(scroll, "Enabled Platforms")
        self._plat_vars: dict[str, ctk.BooleanVar] = {}
        platform_info = {
            "indeed": ("Indeed", "Largest job board. No auth required."),
            "linkedin": ("LinkedIn", "Professional network. Requires LinkedIn auth for apply."),
            "glassdoor": ("Glassdoor", "Jobs + company reviews."),
            "dice": ("Dice", "Tech & IT-focused jobs."),
            "ziprecruiter": ("ZipRecruiter", "AI-matching job board."),
            "remoteok": ("RemoteOK", "Remote-first job board."),
        }
        for key, (label, desc) in platform_info.items():
            row = ctk.CTkFrame(scroll, fg_color=self.colors["content_bg"], corner_radius=6)
            row.pack(fill="x", padx=8, pady=4)
            v = ctk.BooleanVar(value=plats.get(key, {}).get("enabled", True))
            self._plat_vars[key] = v
            ctk.CTkCheckBox(row, text=label, variable=v, font=ctk.CTkFont(size=13), text_color=self.colors["text"]).pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(side="left")

        ctk.CTkButton(scroll, text="Save Platform Settings", fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save_platforms).pack(anchor="e", padx=8, pady=12)

    def _build_search_tab(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        sd = self._cfg.get("search_defaults", {})

        self._section(scroll, "Default Search Parameters")
        self._def_location = ctk.StringVar(value=sd.get("location", ""))
        self._def_radius = ctk.StringVar(value=str(sd.get("radius_miles", 25)))
        self._def_job_type = ctk.StringVar(value=sd.get("job_type", "any"))

        self._field(scroll, "Default Location", self._def_location, "San Francisco, CA")
        self._field(scroll, "Search Radius (miles)", self._def_radius, "25")

        f = ctk.CTkFrame(scroll, fg_color="transparent")
        f.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(f, text="Default Job Type", font=ctk.CTkFont(size=12), text_color=self.colors["text"], width=200, anchor="w").pack(side="left")
        ctk.CTkComboBox(f, variable=self._def_job_type, values=["any", "full-time", "part-time", "contract", "internship"],
                        fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=32).pack(side="left")

        self._def_remote = ctk.BooleanVar(value=sd.get("remote", False))
        ctk.CTkCheckBox(scroll, text="Default to remote jobs", variable=self._def_remote, text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=8)

        ctk.CTkButton(scroll, text="Save Search Defaults", fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save_search).pack(anchor="e", padx=8, pady=12)

    def _build_about_tab(self, tab):
        inner = ctk.CTkFrame(tab, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(inner, text="Job Hunter", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.colors["accent"]).pack(pady=(20, 4))
        ctk.CTkLabel(inner, text="Automated Job Application Suite  v1.0", font=ctk.CTkFont(size=14), text_color=self.colors["text_muted"]).pack()
        ctk.CTkFrame(inner, height=1, fg_color=self.colors["border"]).pack(fill="x", pady=20)
        features = [
            "✓  Multi-platform job search (Indeed, LinkedIn, Glassdoor, Dice, ZipRecruiter, RemoteOK)",
            "✓  Playwright-powered browser automation for form-filling and submission",
            "✓  AI cover letter generation via Claude (Anthropic)",
            "✓  Full application lifecycle tracker",
            "✓  Resume builder and profile manager",
            "✓  Match scoring to prioritize the best-fit jobs",
            "✓  CSV export of all applications",
        ]
        for feat in features:
            ctk.CTkLabel(inner, text=feat, font=ctk.CTkFont(size=12), text_color=self.colors["text"], justify="left").pack(anchor="w", pady=2)

    # ── Save methods ──────────────────────────────────────────────────────────
    def _save_api(self):
        cfg = settings.load()
        cfg["anthropic_api_key"] = self._ant_key.get().strip()
        cfg.setdefault("platforms", {}).setdefault("linkedin", {})["api_key"] = self._li_key.get().strip()
        settings.save(cfg)
        self._cfg = cfg
        messagebox.showinfo("Saved", "API keys saved.")

    def _save_autoapply(self):
        cfg = settings.load()
        cfg.setdefault("auto_apply", {}).update({
            "daily_limit": int(self._daily_limit.get() or 20),
            "delay_seconds": float(self._delay.get() or 3),
            "require_easy_apply": self._easy_only.get(),
            "skip_if_already_applied": self._skip_dups.get(),
        })
        settings.save(cfg)
        self._cfg = cfg
        messagebox.showinfo("Saved", "Auto Apply settings saved.")

    def _save_platforms(self):
        cfg = settings.load()
        for key, var in self._plat_vars.items():
            cfg.setdefault("platforms", {}).setdefault(key, {})["enabled"] = var.get()
        settings.save(cfg)
        self._cfg = cfg
        messagebox.showinfo("Saved", "Platform settings saved.")

    def _save_search(self):
        cfg = settings.load()
        cfg.setdefault("search_defaults", {}).update({
            "location": self._def_location.get(),
            "radius_miles": int(self._def_radius.get() or 25),
            "job_type": self._def_job_type.get(),
            "remote": self._def_remote.get(),
        })
        settings.save(cfg)
        self._cfg = cfg
        messagebox.showinfo("Saved", "Search defaults saved.")

    def on_show(self):
        self._cfg = settings.load()
