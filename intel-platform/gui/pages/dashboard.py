"""Dashboard — live overview of intel platform status."""

import threading
from datetime import datetime, timezone

import customtkinter as ctk

from gui.pages.base_page import BasePage, COLORS


class DashboardPage(BasePage):
    PAGE_TITLE = "Intelligence Dashboard"
    PAGE_SUBTITLE = "   Live overview"

    def build_page(self):
        # Override layout — full width content
        self.left_panel.pack_forget()
        self.right_panel.pack_forget()

        scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color=COLORS["content_bg"])
        scroll.pack(fill="both", expand=True)

        # Stats row
        stats_row = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_row.pack(fill="x", pady=(8, 0))

        self._stat_labels: dict[str, ctk.CTkLabel] = {}

        stat_configs = [
            ("OSINT Records",   "osint",   COLORS["accent"],  "SELECT COUNT(*) FROM whois_records"),
            ("SIGINT Tracks",   "sigint",  "#f39c12",         "SELECT COUNT(*) FROM flight_tracks"),
            ("Geopolitical",    "geo",     "#27ae60",         "SELECT COUNT(*) FROM political_events"),
            ("Power Structure", "power",   "#9b59b6",         "SELECT COUNT(*) FROM billionaires"),
            ("UAP Sightings",   "uap",     "#e74c3c",         "SELECT COUNT(*) FROM uap_sightings"),
            ("Active Alerts",   "alerts",  "#e74c3c",         "SELECT COUNT(*) FROM alerts WHERE acknowledged=0"),
        ]
        self._stat_queries = {k: q for _, k, _, q in stat_configs}

        for label, key, color, _ in stat_configs:
            card = ctk.CTkFrame(stats_row, fg_color=COLORS["panel_bg"], corner_radius=8, width=165, height=88)
            card.pack(side="left", padx=6, pady=4)
            card.pack_propagate(False)
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=12, pady=(10, 0))
            val_label = ctk.CTkLabel(card, text="…", font=ctk.CTkFont(size=24, weight="bold"), text_color=color)
            val_label.pack(anchor="w", padx=12)
            self._stat_labels[key] = val_label

        # Quick launch row
        self._section_label_full(scroll, "Quick Actions")
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=4)

        quick_actions = [
            ("Refresh Leaders",    ["geo", "leaders", "--refresh"]),
            ("Update Sanctions",   ["geo", "sanctions", "—", "--refresh"]),
            ("Latest UAP News",    ["uap", "news", "--refresh"]),
            ("Live Flights",       ["sigint", "flights", "--live"]),
            ("Feed Status",        ["feed", "status"]),
            ("AI Analyst",         ["ask", "Summarize the latest geopolitical developments."]),
        ]
        for label, cmd in quick_actions:
            ctk.CTkButton(
                btn_row,
                text=label,
                fg_color=COLORS["panel_bg"],
                hover_color=COLORS["accent"],
                text_color=COLORS["text"],
                corner_radius=6,
                height=32,
                width=140,
                command=lambda c=cmd: self._quick_run(c),
            ).pack(side="left", padx=4)

        # Recent feed section
        self._section_label_full(scroll, "Recent Intelligence Feed")
        self.feed_box = ctk.CTkTextbox(
            scroll,
            height=200,
            fg_color=COLORS["input_bg"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Courier New", size=11),
            state="disabled",
        )
        self.feed_box.pack(fill="x", padx=4, pady=4)

        # Platform info
        self._section_label_full(scroll, "Platform Status")
        info = ctk.CTkFrame(scroll, fg_color=COLORS["panel_bg"], corner_radius=8)
        info.pack(fill="x", padx=4, pady=4)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        ctk.CTkLabel(
            info,
            text=f"Intel Platform v2.0  |  Initialized: {now}\n"
                 "Data sources: Wikidata • GDELT • OFAC • OpenSky • NUFORC • FEC • ICIJ • SEC EDGAR • FBI • Interpol • OpenAlex\n"
                 "Threat intel: abuse.ch URLhaus • MalwareBazaar • ip-api.com • AlienVault OTX • HIBP (no keys required)\n"
                 "AI: Groq LLaMA-3.3-70B  |  Storage: SQLite (WAL mode)  |  GUI: CustomTkinter",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
            justify="left",
        ).pack(anchor="w", padx=16, pady=12)

        # Load data
        self.after(500, self._load_recent_feed)
        self.after(800, self._load_stats)

    def _section_label_full(self, parent, text: str):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w", padx=4, pady=(12, 4))

    def _quick_run(self, cmd: list):
        self.run_command(cmd)

    def _load_stats(self):
        """Background thread: query DB counts and update stat labels."""
        def _fetch():
            try:
                from core import database
                results = {}
                for key, query in self._stat_queries.items():
                    try:
                        rows = database.execute(query)
                        results[key] = rows[0][0] if rows else 0
                    except Exception:
                        results[key] = "?"
                self.after(0, lambda r=results: self._update_stat_labels(r))
            except Exception:
                pass
            # Auto-refresh every 30s
            if self.winfo_exists():
                self.after(30000, self._load_stats)

        threading.Thread(target=_fetch, daemon=True).start()

    def _update_stat_labels(self, results: dict):
        for key, val in results.items():
            if key in self._stat_labels and self._stat_labels[key].winfo_exists():
                self._stat_labels[key].configure(text=str(val))

    def _load_recent_feed(self):
        def _fetch():
            try:
                from modules.feed.rss_aggregator import get_recent
                items = get_recent(days=3, limit=20)
                lines = []
                for item in items:
                    pub = (item.published_at or "")[:10]
                    lines.append(f"[{pub}] [{item.source[:15]:15}] {item.title[:70]}")
                text = "\n".join(lines) if lines else "No recent feed items. Run 'intel feed start' to begin collection."
                self.after(0, lambda: self._update_feed_box(text))
            except Exception as e:
                self.after(0, lambda: self._update_feed_box(f"Feed unavailable: {e}"))
        threading.Thread(target=_fetch, daemon=True).start()

    def _update_feed_box(self, text: str):
        self.feed_box.configure(state="normal")
        self.feed_box.delete("1.0", "end")
        self.feed_box.insert("end", text)
        self.feed_box.configure(state="disabled")
