"""Dashboard page — overview stats and recent activity."""

import json
from datetime import datetime, timedelta

import customtkinter as ctk

from core.database import execute


class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, colors: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=colors["content_bg"], **kwargs)
        self.colors = colors
        self.nav_callback = nav_callback
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkLabel(hdr, text="Dashboard", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.colors["text"]).pack(side="left")
        ctk.CTkButton(
            hdr, text="+ Search Jobs", width=130, height=32,
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
            command=lambda: self.nav_callback("search") if self.nav_callback else None,
        ).pack(side="right")

        # Stats row
        self._stats_row = ctk.CTkFrame(self, fg_color="transparent")
        self._stats_row.pack(fill="x", padx=28, pady=(8, 0))

        # Recent activity + pipeline
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=16)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self._activity_frame = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        self._activity_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._pipeline_frame = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        self._pipeline_frame.grid(row=0, column=1, sticky="nsew")

        self._load_data()

    def _stat_card(self, parent, label: str, value: str, color: str):
        card = ctk.CTkFrame(parent, fg_color=self.colors["panel_bg"], corner_radius=8)
        card.pack(side="left", padx=(0, 12), pady=4, ipadx=16, ipady=10)
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=28, weight="bold"), text_color=color).pack()
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack()

    def _load_data(self):
        # Clear old stats
        for w in self._stats_row.winfo_children():
            w.destroy()

        try:
            total = execute("SELECT COUNT(*) as c FROM applications")[0]["c"]
            active = execute("SELECT COUNT(*) as c FROM applications WHERE status NOT IN ('rejected','withdrawn')")[0]["c"]
            interviews = execute("SELECT COUNT(*) as c FROM applications WHERE status='interview'")[0]["c"]
            offers = execute("SELECT COUNT(*) as c FROM applications WHERE status='offer'")[0]["c"]
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            this_week = execute("SELECT COUNT(*) as c FROM applications WHERE applied_at >= ?", (week_ago,))[0]["c"]
        except Exception:
            total = active = interviews = offers = this_week = 0

        self._stat_card(self._stats_row, "Total Applied", str(total), self.colors["text"])
        self._stat_card(self._stats_row, "Active", str(active), self.colors["accent"])
        self._stat_card(self._stats_row, "Interviews", str(interviews), self.colors["warning"])
        self._stat_card(self._stats_row, "Offers", str(offers), self.colors["success"])
        self._stat_card(self._stats_row, "This Week", str(this_week), self.colors["tag_bg"])

        self._load_activity()
        self._load_pipeline()

    def _load_activity(self):
        for w in self._activity_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self._activity_frame, text="Recent Applications",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["text"],
        ).pack(anchor="w", padx=16, pady=(14, 6))
        ctk.CTkFrame(self._activity_frame, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=12)

        scroll = ctk.CTkScrollableFrame(self._activity_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        STATUS_COLORS = {
            "applied":      self.colors["tag_bg"],
            "viewed":       self.colors["text_muted"],
            "phone_screen": self.colors["warning"],
            "interview":    self.colors["warning"],
            "offer":        self.colors["success"],
            "rejected":     self.colors["danger"],
            "withdrawn":    self.colors["text_muted"],
        }

        try:
            rows = execute(
                """SELECT a.*, j.title, j.company, j.platform
                   FROM applications a
                   JOIN job_listings j ON a.job_id = j.id
                   ORDER BY a.applied_at DESC LIMIT 20""",
            )
        except Exception:
            rows = []

        if not rows:
            ctk.CTkLabel(
                scroll, text="No applications yet.\nSearch for jobs and start applying!",
                font=ctk.CTkFont(size=12), text_color=self.colors["text_muted"],
                justify="center",
            ).pack(expand=True, pady=40)
            return

        for row in rows:
            item = ctk.CTkFrame(scroll, fg_color=self.colors["content_bg"], corner_radius=6)
            item.pack(fill="x", pady=3)
            left = ctk.CTkFrame(item, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=12, pady=8)
            ctk.CTkLabel(left, text=row["title"], font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{row['company']}  ·  {row['platform']}", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w")

            status = row["status"]
            color = STATUS_COLORS.get(status, self.colors["text_muted"])
            ctk.CTkLabel(
                item, text=f"  {status.replace('_', ' ').title()}  ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=color, corner_radius=4, text_color="#ffffff",
            ).pack(side="right", padx=12, pady=10)

    def _load_pipeline(self):
        for w in self._pipeline_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self._pipeline_frame, text="Application Pipeline",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["text"],
        ).pack(anchor="w", padx=16, pady=(14, 6))
        ctk.CTkFrame(self._pipeline_frame, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=12)

        stages = [
            ("Applied",       "applied",       self.colors["tag_bg"]),
            ("Viewed",        "viewed",         self.colors["text_muted"]),
            ("Phone Screen",  "phone_screen",   self.colors["warning"]),
            ("Interview",     "interview",      self.colors["warning"]),
            ("Offer",         "offer",          self.colors["success"]),
            ("Rejected",      "rejected",       self.colors["danger"]),
            ("Withdrawn",     "withdrawn",      self.colors["text_muted"]),
        ]

        inner = ctk.CTkFrame(self._pipeline_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=12)

        try:
            counts = {
                row["status"]: row["c"]
                for row in execute("SELECT status, COUNT(*) as c FROM applications GROUP BY status")
            }
        except Exception:
            counts = {}

        for label, key, color in stages:
            count = counts.get(key, 0)
            row_frame = ctk.CTkFrame(inner, fg_color="transparent")
            row_frame.pack(fill="x", pady=4)
            ctk.CTkLabel(row_frame, text=label, font=ctk.CTkFont(size=12), text_color=self.colors["text"], width=110, anchor="w").pack(side="left")

            total = sum(counts.values()) or 1
            pct = count / total

            bar_bg = ctk.CTkFrame(row_frame, height=14, corner_radius=4, fg_color=self.colors["border"])
            bar_bg.pack(side="left", fill="x", expand=True, padx=8)
            if pct > 0:
                bar_fill = ctk.CTkFrame(bar_bg, height=14, corner_radius=4, fg_color=color)
                bar_fill.place(relx=0, rely=0, relwidth=max(pct, 0.02), relheight=1)

            ctk.CTkLabel(row_frame, text=str(count), font=ctk.CTkFont(size=11, weight="bold"), text_color=color, width=30).pack(side="right")

    def on_show(self):
        self._load_data()
