"""GUI application window for Intel Platform."""

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

from gui.pages.dashboard import DashboardPage
from gui.pages.osint_page import OSINTPage
from gui.pages.sigint_page import SIGINTPage
from gui.pages.geo_page import GeoPage
from gui.pages.power_page import PowerPage
from gui.pages.uap_page import UAPPage
from gui.pages.correlation_page import CorrelationPage
from gui.pages.feed_page import FeedPage
from gui.pages.settings_page import SettingsPage
from gui.pages.search_page import SearchPage
from gui.pages.graph_page import GraphPage
from gui.pages.map_page import MapPage

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Color scheme (GitHub dark)
COLORS = {
    "sidebar_bg":   "#0d1117",
    "content_bg":   "#161b22",
    "accent":       "#1f6feb",
    "accent_hover": "#388bfd",
    "text":         "#c9d1d9",
    "text_muted":   "#8b949e",
    "selected":     "#ffffff",
    "border":       "#30363d",
    "success":      "#3fb950",
    "warning":      "#d29922",
    "danger":       "#f85149",
    "panel_bg":     "#21262d",
}

NAV_ITEMS = [
    ("Dashboard",          "dashboard",     DashboardPage),
    ("Universal Search",   "search",        SearchPage),
    ("OSINT",              "osint",         OSINTPage),
    ("SIGINT / Tracking",  "sigint",        SIGINTPage),
    ("Geopolitical",       "geo",           GeoPage),
    ("Power Structures",   "power",         PowerPage),
    ("UAP / Anomalous",    "uap",           UAPPage),
    ("Correlation",        "correlation",   CorrelationPage),
    ("Graph View",         "graph",         GraphPage),
    ("Intelligence Map",   "map",           MapPage),
    ("Live Feed",          "feed",          FeedPage),
    ("Settings",           "settings",      SettingsPage),
]


class IntelPlatformApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Intel Platform — OSINT/SIGINT Intelligence v2.0")
        self.geometry("1440x900")
        self.minsize(1200, 720)
        self.configure(fg_color=COLORS["content_bg"])

        self._current_page = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._pages: dict[str, ctk.CTkFrame] = {}

        self._build_layout()
        self._navigate("dashboard")

        # Start toast notification manager
        try:
            from gui.widgets.alert_toast import ToastManager
            self.toast_manager = ToastManager(self)
            self.toast_manager.start_polling()
        except Exception:
            pass

    def _build_layout(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=228, corner_radius=0, fg_color=COLORS["sidebar_bg"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo / title
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(fill="x", pady=(20, 8), padx=16)
        ctk.CTkLabel(
            title_frame,
            text="INTEL PLATFORM",
            font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame,
            text="Intelligence Suite v2.0",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        # Separator
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=12, pady=6)

        # Navigation buttons
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=8)

        # Group separators
        separators_before = {"search", "correlation", "feed", "settings"}

        for label, key, _ in NAV_ITEMS:
            if key in separators_before:
                ctk.CTkFrame(nav_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=4, pady=4)
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                anchor="w",
                corner_radius=6,
                height=34,
                fg_color="transparent",
                hover_color=COLORS["accent"],
                text_color=COLORS["text_muted"],
                font=ctk.CTkFont(size=12),
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x", pady=1)
            self._nav_buttons[key] = btn

        # Bottom status bar
        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(side="bottom", fill="x", padx=12, pady=0)
        status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_frame.pack(side="bottom", fill="x", padx=12, pady=12)
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["success"],
        )
        self.status_label.pack(anchor="w")

        # Content area
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["content_bg"])
        self.content_frame.pack(side="left", fill="both", expand=True)

    def _navigate(self, key: str):
        # Update button styles
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=COLORS["accent"], text_color=COLORS["selected"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_muted"])

        # Hide current page
        if self._current_page and self._current_page.winfo_exists():
            self._current_page.pack_forget()

        # Show or create page
        if key not in self._pages:
            page_class = next(pc for label, k, pc in NAV_ITEMS if k == key)
            self._pages[key] = page_class(self.content_frame, self)
        self._current_page = self._pages[key]
        self._current_page.pack(fill="both", expand=True)

    def set_status(self, msg: str, color: str = "success"):
        self.status_label.configure(text=msg, text_color=COLORS.get(color, COLORS["success"]))


def launch():
    from core import database
    database.init_db()
    app = IntelPlatformApp()
    app.mainloop()
