"""Main application window for Job Hunter."""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from gui.pages.dashboard import DashboardPage
from gui.pages.profile_page import ProfilePage
from gui.pages.search_page import SearchPage
from gui.pages.apply_page import ApplyPage
from gui.pages.tracker_page import TrackerPage
from gui.pages.cover_letter_page import CoverLetterPage
from gui.pages.settings_page import SettingsPage

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "sidebar_bg":   "#0d1117",
    "content_bg":   "#161b22",
    "accent":       "#238636",
    "accent_hover": "#2ea043",
    "text":         "#c9d1d9",
    "text_muted":   "#8b949e",
    "selected":     "#ffffff",
    "border":       "#30363d",
    "success":      "#3fb950",
    "warning":      "#d29922",
    "danger":       "#f85149",
    "panel_bg":     "#21262d",
    "tag_bg":       "#1f6feb",
}

NAV_ITEMS = [
    ("Dashboard",         "dashboard",    DashboardPage),
    ("My Profiles",       "profiles",     ProfilePage),
    ("Job Search",        "search",       SearchPage),
    ("Auto Apply",        "apply",        ApplyPage),
    ("Applications",      "tracker",      TrackerPage),
    ("Cover Letters",     "cover_letter", CoverLetterPage),
    ("Settings",          "settings",     SettingsPage),
]

NAV_ICONS = {
    "dashboard":    "⊞",
    "profiles":     "◉",
    "search":       "⌕",
    "apply":        "⚡",
    "tracker":      "▤",
    "cover_letter": "✉",
    "settings":     "⚙",
}


class JobHunterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Job Hunter — Automated Job Application Suite v1.0")
        self.geometry("1440x900")
        self.minsize(1200, 720)
        self.configure(fg_color=COLORS["content_bg"])

        self._current_page = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._pages: dict[str, ctk.CTkFrame] = {}

        self._build_layout()
        self._navigate("dashboard")

    def _build_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=228, corner_radius=0, fg_color=COLORS["sidebar_bg"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo area
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(20, 8), padx=16)
        ctk.CTkLabel(
            logo_frame,
            text="JOB HUNTER",
            font=ctk.CTkFont(family="Helvetica", size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo_frame,
            text="Automated Application Suite",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        # Separator
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=(8, 12))

        # Nav section label
        ctk.CTkLabel(
            self.sidebar,
            text="NAVIGATION",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", padx=16, pady=(0, 6))

        # Nav buttons
        for label, key, _ in NAV_ITEMS:
            icon = NAV_ICONS.get(key, "•")
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                height=36,
                corner_radius=6,
                fg_color="transparent",
                hover_color=COLORS["panel_bg"],
                text_color=COLORS["text_muted"],
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[key] = btn

        # Bottom: stats summary
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=(16, 8))
        self._stats_label = ctk.CTkLabel(
            self.sidebar,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
            justify="left",
        )
        self._stats_label.pack(anchor="w", padx=16, pady=(0, 16))
        self._refresh_sidebar_stats()

        # Content area
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["content_bg"])
        self.content.pack(side="left", fill="both", expand=True)

    def _navigate(self, key: str):
        # Deselect all buttons
        for k, btn in self._nav_buttons.items():
            btn.configure(
                fg_color=COLORS["accent"] if k == key else "transparent",
                text_color=COLORS["selected"] if k == key else COLORS["text_muted"],
            )

        # Hide current page
        if self._current_page:
            self._current_page.pack_forget()

        # Show or create target page
        if key not in self._pages:
            page_class = next(pc for _, k, pc in NAV_ITEMS if k == key)
            page = page_class(self.content, colors=COLORS, nav_callback=self._navigate)
            self._pages[key] = page

        self._current_page = self._pages[key]
        self._current_page.pack(fill="both", expand=True)

        if hasattr(self._current_page, "on_show"):
            self._current_page.on_show()

        self._refresh_sidebar_stats()

    def _refresh_sidebar_stats(self):
        try:
            from core.database import execute
            total = execute("SELECT COUNT(*) as c FROM applications")[0]["c"]
            active = execute(
                "SELECT COUNT(*) as c FROM applications WHERE status NOT IN ('rejected','withdrawn')"
            )[0]["c"]
            interviews = execute(
                "SELECT COUNT(*) as c FROM applications WHERE status='interview'"
            )[0]["c"]
            self._stats_label.configure(
                text=f"Total applied:  {total}\nActive:         {active}\nInterviews:     {interviews}"
            )
        except Exception:
            self._stats_label.configure(text="No data yet")


def launch():
    app = JobHunterApp()
    app.mainloop()
