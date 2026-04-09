"""Universal Search page — cross-module full-platform search."""
import threading

import customtkinter as ctk

from gui.pages.base_page import BasePage, COLORS


class SearchPage(BasePage):
    PAGE_TITLE = "Universal Search"
    PAGE_SUBTITLE = "   Cross-module intelligence search"

    def build_page(self):
        self.left_panel.pack_forget()
        self.right_panel.pack_forget()

        # Search bar
        search_bar = ctk.CTkFrame(self.main_frame, fg_color=COLORS["panel_bg"], corner_radius=8)
        search_bar.pack(fill="x", pady=(0, 8))

        self.search_entry = ctk.CTkEntry(
            search_bar,
            placeholder_text="Search across all intelligence databases…",
            fg_color=COLORS["input_bg"],
            border_color=COLORS["accent"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=16),
            height=48,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=12, pady=8)
        self.search_entry.bind("<Return>", lambda e: self._search_all())

        ctk.CTkButton(
            search_bar, text="Search All", width=110, height=36,
            fg_color=COLORS["accent"], hover_color="#388bfd",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._search_all,
        ).pack(side="right", padx=12, pady=8)

        # Results tabs
        self.tabs = ctk.CTkTabview(
            self.main_frame,
            fg_color=COLORS["panel_bg"],
            segmented_button_fg_color=COLORS["input_bg"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_unselected_color=COLORS["input_bg"],
            text_color=COLORS["text"],
        )
        self.tabs.pack(fill="both", expand=True)

        self._tab_boxes = {}
        tab_names = [
            ("Entities",     "entities"),
            ("Sanctions",    "sanctions"),
            ("Wanted",       "wanted"),
            ("Breaches",     "breaches"),
            ("Threat Intel", "threats"),
            ("Feed",         "feed"),
            ("OSINT",        "osint"),
        ]
        for label, key in tab_names:
            self.tabs.add(label)
            tab = self.tabs.tab(label)
            box = ctk.CTkTextbox(
                tab,
                fg_color=COLORS["input_bg"],
                text_color=COLORS["text"],
                font=ctk.CTkFont(family="Courier New", size=12),
                state="disabled",
            )
            box.pack(fill="both", expand=True, padx=4, pady=4)
            self._tab_boxes[key] = box

        # Status
        self.search_status = ctk.CTkLabel(
            self.main_frame,
            text="Enter a name, domain, IP, or keyword and press Search All",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self.search_status.pack(pady=(4, 0))

    def _search_all(self):
        query = self.search_entry.get().strip()
        if not query:
            return
        self.search_status.configure(text=f"Searching for: {query}…")
        # Clear all tabs
        for box in self._tab_boxes.values():
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.insert("end", f"Searching for '{query}'…\n")
            box.configure(state="disabled")
        threading.Thread(target=self._run_searches, args=(query,), daemon=True).start()

    def _run_searches(self, query: str):
        results_summary = []
        searches = [
            ("entities",   self._search_entities),
            ("sanctions",  self._search_sanctions),
            ("wanted",     self._search_wanted),
            ("breaches",   self._search_breaches),
            ("threats",    self._search_threats),
            ("feed",       self._search_feed),
            ("osint",      self._search_osint),
        ]
        for key, fn in searches:
            try:
                text = fn(query)
                count_line = text.split("\n")[0] if text else "0 results"
                results_summary.append(count_line)
                self.after(0, lambda k=key, t=text: self._update_tab(k, t))
            except Exception as e:
                self.after(0, lambda k=key, err=e: self._update_tab(k, f"Error: {err}"))

        total_hint = " | ".join(results_summary[:4])
        self.after(0, lambda: self.search_status.configure(text=f"Results: {total_hint}"))

    def _update_tab(self, key: str, text: str):
        box = self._tab_boxes.get(key)
        if not box:
            return
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("end", text)
        box.configure(state="disabled")

    def _search_entities(self, query: str) -> str:
        from modules.correlation.entity_resolver import fuzzy_search_entities
        results = fuzzy_search_entities(query, threshold=60)
        if not results:
            return "0 entities found\n"
        lines = [f"{len(results)} entities found\n", "-" * 60]
        for r in results[:30]:
            # fuzzy_search_entities returns Entity dataclass objects
            name = getattr(r, "canonical_name", "") or ""
            etype = getattr(r, "entity_type", "") or ""
            sources = ", ".join(getattr(r, "source_modules", []) or [])
            lines.append(f"[{etype:12}] {name:40} Sources: {sources}")
        return "\n".join(lines)

    def _search_sanctions(self, query: str) -> str:
        from core import database
        rows = database.execute(
            "SELECT name, list_source, entity_type, nationality, programs FROM sanctions "
            "WHERE name LIKE ? ORDER BY list_source LIMIT 50",
            (f"%{query}%",),
        )
        if not rows:
            return "0 sanctions matches\n"
        lines = [f"{len(rows)} sanctions matches\n", "-" * 60]
        for r in rows:
            lines.append(f"[{r['list_source']:6}] [{r['entity_type'] or '?':12}] {r['name']:40} {r['nationality'] or '—'}")
        return "\n".join(lines)

    def _search_wanted(self, query: str) -> str:
        from core import database
        rows = database.execute(
            "SELECT full_name, list_source, nationality, charges FROM wanted_persons "
            "WHERE full_name LIKE ? OR aliases LIKE ? ORDER BY list_source LIMIT 50",
            (f"%{query}%", f"%{query}%"),
        )
        if not rows:
            return "0 wanted persons found\n"
        lines = [f"{len(rows)} wanted persons found\n", "-" * 60]
        for r in rows:
            lines.append(f"[{r['list_source']:10}] {r['full_name']:40} {r['nationality'] or '—'}")
        return "\n".join(lines)

    def _search_breaches(self, query: str) -> str:
        from core import database
        rows = database.execute(
            "SELECT target, breach_name, breach_date, pwn_count FROM breach_records "
            "WHERE target LIKE ? ORDER BY breach_date DESC LIMIT 50",
            (f"%{query}%",),
        )
        if not rows:
            return "0 breach records found\n"
        lines = [f"{len(rows)} breach records\n", "-" * 60]
        for r in rows:
            lines.append(f"{r['breach_date'] or '—':12} [{r['breach_name']:30}] {r['target']:30} {r['pwn_count'] or 0:,} records")
        return "\n".join(lines)

    def _search_threats(self, query: str) -> str:
        from core import database
        rows = database.execute(
            "SELECT indicator, indicator_type, source, malicious_votes, reputation_score FROM threat_intel "
            "WHERE indicator LIKE ? ORDER BY collected_at DESC LIMIT 50",
            (f"%{query}%",),
        )
        if not rows:
            return "0 threat intel entries\n"
        lines = [f"{len(rows)} threat intel entries\n", "-" * 60]
        for r in rows:
            lines.append(f"[{r['indicator_type']:8}] [{r['source']:15}] {r['indicator']:40} "
                         f"Malicious:{r['malicious_votes']} Score:{r['reputation_score']}")
        return "\n".join(lines)

    def _search_feed(self, query: str) -> str:
        from core import database
        rows = database.execute(
            "SELECT title, source, published_at, category FROM feed_items "
            "WHERE title LIKE ? OR summary LIKE ? ORDER BY published_at DESC LIMIT 50",
            (f"%{query}%", f"%{query}%"),
        )
        if not rows:
            return "0 feed items found\n"
        lines = [f"{len(rows)} feed items\n", "-" * 60]
        for r in rows:
            lines.append(f"{(r['published_at'] or '')[:10]} [{r['source'][:18]:18}] {r['title'][:70]}")
        return "\n".join(lines)

    def _search_osint(self, query: str) -> str:
        from core import database
        lines = []
        # WHOIS
        rows = database.execute(
            "SELECT domain, registrant_name, registrant_org FROM whois_records WHERE domain LIKE ? OR registrant_name LIKE ? LIMIT 10",
            (f"%{query}%", f"%{query}%"),
        )
        if rows:
            lines.append(f"WHOIS ({len(rows)} matches):")
            for r in rows:
                lines.append(f"  {r['domain']:35} {r['registrant_org'] or r['registrant_name'] or '—'}")
        # Certs
        rows2 = database.execute(
            "SELECT domain, common_name, issuer FROM cert_transparency WHERE domain LIKE ? OR common_name LIKE ? LIMIT 10",
            (f"%{query}%", f"%{query}%"),
        )
        if rows2:
            lines.append(f"\nCert Transparency ({len(rows2)} matches):")
            for r in rows2:
                lines.append(f"  {r['domain']:35} {r['common_name'] or '—'}")
        if not lines:
            return "0 OSINT records found\n"
        return f"{len(rows) + len(rows2)} OSINT records\n" + "-" * 60 + "\n" + "\n".join(lines)
