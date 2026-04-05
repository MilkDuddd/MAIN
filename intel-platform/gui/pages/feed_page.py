"""Live intelligence feed page with auto-refresh."""
import threading
import customtkinter as ctk
from gui.pages.base_page import BasePage, COLORS

POLL_MS = 10000  # refresh every 10 seconds


class FeedPage(BasePage):
    PAGE_TITLE = "Live Intelligence Feed"
    PAGE_SUBTITLE = "   Real-time updates • Alerts • News"

    def build_page(self):
        # Override — full width
        self.left_panel.pack_forget()
        self.right_panel.pack_forget()

        # Controls row
        ctrl = ctk.CTkFrame(self.main_frame, fg_color=COLORS["panel_bg"], corner_radius=8)
        ctrl.pack(fill="x", pady=(0, 8))

        self.category_var = ctk.StringVar(value="all")
        for cat in ["all", "geopolitical", "uap", "general"]:
            ctk.CTkRadioButton(
                ctrl, text=cat.title(), variable=self.category_var, value=cat,
                text_color=COLORS["text"], fg_color=COLORS["accent"],
                command=self._refresh,
            ).pack(side="left", padx=12, pady=6)

        ctk.CTkButton(
            ctrl, text="Refresh", width=90, height=28, fg_color=COLORS["accent"],
            command=self._refresh,
        ).pack(side="right", padx=12, pady=6)

        ctk.CTkButton(
            ctrl, text="Start Daemon", width=110, height=28, fg_color="#27ae60",
            command=lambda: self.run_command(["feed", "start"]),
        ).pack(side="right", padx=4, pady=6)

        # Alerts panel
        self._section_label_full(self.main_frame, "Active Alerts")
        self.alerts_box = ctk.CTkTextbox(
            self.main_frame, height=80, fg_color="#1a0a0a",
            text_color=COLORS["danger"], font=ctk.CTkFont(family="Courier New", size=11),
            state="disabled",
        )
        self.alerts_box.pack(fill="x", pady=(0, 8))

        # Feed items
        self._section_label_full(self.main_frame, "Intelligence Feed")
        self.feed_box = ctk.CTkTextbox(
            self.main_frame,
            fg_color=COLORS["input_bg"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Courier New", size=11),
            state="disabled",
        )
        self.feed_box.pack(fill="both", expand=True)

        # Alert watchlist controls
        self._section_label_full(self.main_frame, "Watchlist")
        kw_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        kw_frame.pack(fill="x", pady=4)
        self.kw_entry = ctk.CTkEntry(kw_frame, placeholder_text="Add keyword/entity to watch...",
                                      fg_color=COLORS["input_bg"], text_color=COLORS["text"])
        self.kw_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(kw_frame, text="+ Keyword", width=90, fg_color=COLORS["accent"],
                      command=self._add_keyword).pack(side="left", padx=2)
        ctk.CTkButton(kw_frame, text="+ Entity", width=80, fg_color="#6f42c1",
                      command=self._add_entity).pack(side="left", padx=2)

        self._refresh()
        self._start_poll()

    def _section_label_full(self, parent, text: str):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w", pady=(8, 2))

    def _refresh(self):
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        try:
            from modules.feed.rss_aggregator import get_recent
            from modules.feed.alert_engine import get_active_alerts

            cat = self.category_var.get()
            items = get_recent(category=None if cat == "all" else cat, days=3, limit=50)
            lines = []
            for item in items:
                pub = (item.published_at or "")[:10]
                cat_tag = f"[{(item.category or 'general')[:6].upper():6}]"
                lines.append(f"{pub} {cat_tag} [{item.source[:18]:18}] {item.title[:65]}")
            feed_text = "\n".join(lines) if lines else "No items. Start the daemon to collect feeds."

            alerts = get_active_alerts(limit=20)
            alert_lines = [f"[{a.severity.upper()}] {a.message}" for a in alerts]
            alert_text = "\n".join(alert_lines) if alert_lines else "No active alerts"

            self.after(0, lambda: self._update_boxes(feed_text, alert_text))
        except Exception as e:
            self.after(0, lambda: self._update_boxes(f"Error: {e}", ""))

    def _update_boxes(self, feed_text: str, alert_text: str):
        for box, text in [(self.feed_box, feed_text), (self.alerts_box, alert_text)]:
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("end", text)
            box.configure(state="disabled")

    def _start_poll(self):
        self.after(POLL_MS, self._poll)

    def _poll(self):
        if self.winfo_exists():
            self._refresh()
            self.after(POLL_MS, self._poll)

    def _add_keyword(self):
        kw = self.kw_entry.get().strip()
        if kw:
            self.run_command(["feed", "alerts", "--add-keyword", kw], clear=False)
            self.kw_entry.delete(0, "end")

    def _add_entity(self):
        ent = self.kw_entry.get().strip()
        if ent:
            self.run_command(["feed", "alerts", "--add-entity", ent], clear=False)
            self.kw_entry.delete(0, "end")
