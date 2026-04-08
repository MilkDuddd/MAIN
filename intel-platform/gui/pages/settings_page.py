"""Settings page for Intel Platform GUI."""
import threading
import customtkinter as ctk
from gui.pages.base_page import BasePage, COLORS


class SettingsPage(BasePage):
    PAGE_TITLE = "Settings"
    PAGE_SUBTITLE = "   API Keys & Configuration"

    def build_page(self):
        self.left_panel.pack_forget()
        self.right_panel.pack_forget()

        scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color=COLORS["content_bg"])
        scroll.pack(fill="both", expand=True)

        # ── Ollama AI Section ──────────────────────────────────────────────────
        self._section_label_full(scroll, "AI Engine — Ollama (Local, No API Key Required)")

        ol_frame = ctk.CTkFrame(scroll, fg_color=COLORS["panel_bg"], corner_radius=8)
        ol_frame.pack(fill="x", padx=4, pady=4)

        # Status row
        status_row = ctk.CTkFrame(ol_frame, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(status_row, text="Ollama Status:", width=160, anchor="w",
                     text_color=COLORS["text_muted"]).pack(side="left")
        self._ol_status_lbl = ctk.CTkLabel(status_row, text="Checking...",
                                            text_color="#d29922")
        self._ol_status_lbl.pack(side="left")
        ctk.CTkButton(status_row, text="Test Connection", width=120, height=28,
                      fg_color=COLORS["accent"],
                      command=self._test_ollama).pack(side="right", padx=4)

        # URL row
        url_row = ctk.CTkFrame(ol_frame, fg_color="transparent")
        url_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(url_row, text="Ollama URL:", width=160, anchor="w",
                     text_color=COLORS["text_muted"]).pack(side="left")
        self._ol_url_entry = ctk.CTkEntry(url_row, fg_color=COLORS["input_bg"],
                                           text_color=COLORS["text"], width=240)
        from core import settings as cfg
        self._ol_url_entry.insert(0, cfg.get("ollama_url", "http://localhost:11434"))
        self._ol_url_entry.pack(side="left", padx=4)
        ctk.CTkButton(url_row, text="Save", width=60, height=28, fg_color=COLORS["accent"],
                      command=lambda: self._save_key("ollama_url", self._ol_url_entry.get())).pack(side="left", padx=4)

        # Model row
        model_row = ctk.CTkFrame(ol_frame, fg_color="transparent")
        model_row.pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkLabel(model_row, text="Model:", width=160, anchor="w",
                     text_color=COLORS["text_muted"]).pack(side="left")
        self._ol_model_var = ctk.StringVar(value=cfg.get("ollama_model", "llama3.2"))
        self._ol_model_menu = ctk.CTkOptionMenu(
            model_row, variable=self._ol_model_var,
            values=["llama3.2", "llama3.1:8b", "mistral", "deepseek-r1:7b", "gemma2:9b"],
            fg_color=COLORS["input_bg"], button_color=COLORS["accent"],
            width=200,
            command=lambda m: self._save_key("ollama_model", m),
        )
        self._ol_model_menu.pack(side="left", padx=4)
        ctk.CTkButton(model_row, text="Setup Wizard", width=110, height=28,
                      fg_color=COLORS["panel_bg"], border_width=1,
                      border_color=COLORS["text_muted"], text_color=COLORS["text"],
                      command=self._open_wizard).pack(side="right", padx=4)

        self._test_ollama()

        # ── Optional API Keys ──────────────────────────────────────────────────
        self._section_label_full(scroll, "Government Data (All Free with Registration)")
        self._api_key_row(scroll, "FEC API Key",         "fec_api_key",    "...")
        self._api_key_row(scroll, "SAM.gov Key",         "sam_gov_key",    "...")
        self._api_key_row(scroll, "ProPublica Key",      "propublica_key", "abc123...")
        self._api_key_row(scroll, "ACLED Email",         "acled_email",    "you@email.com")
        self._api_key_row(scroll, "ACLED API Key",       "acled_key",      "...")

        self._section_label_full(scroll, "Research & Threat Intel (All Free)")
        self._api_key_row(scroll, "AlienVault OTX Key",  "otx_key",         "abc123...")
        self._api_key_row(scroll, "Global Fishing Watch", "gfw_key",         "abc123...")
        self._api_key_row(scroll, "HaveIBeenPwned Key",  "hibp_key",        "abc123...")

        self._section_label_full(scroll, "Infrastructure (Free Tier)")
        self._api_key_row(scroll, "Shodan Key",           "shodan_api_key", "ABC123...")
        self._api_key_row(scroll, "NewsAPI Key",          "newsapi_key",    "abcdef...")
        self._api_key_row(scroll, "aisstream.io Key",     "aisstream_key",  "...")
        self._api_key_row(scroll, "OpenCorporates Key",   "opencorp_key",   "...")

        # ── General ────────────────────────────────────────────────────────────
        self._section_label_full(scroll, "General Settings")
        self._setting_row(scroll, "Analyst Name",     "analyst_name", "Intel Analyst")
        self._setting_row(scroll, "Output Directory", "output_dir",   "~/intel-reports")

        # ── Action Buttons ─────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=12)
        ctk.CTkButton(btn_row, text="Show All Settings", fg_color=COLORS["accent"],
                      command=lambda: self.run_command(["settings", "show"])).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Test AI Connection", fg_color="#27ae60",
                      command=lambda: self.run_command(["ask", "Say hello and confirm you are connected."])).pack(side="left", padx=4)

        # ── No-key sources info ────────────────────────────────────────────────
        self._section_label_full(scroll, "No-Key Sources — Always Active (22 Sources)")
        info = ctk.CTkTextbox(scroll, height=160, fg_color=COLORS["input_bg"],
                              text_color=COLORS["text_muted"], font=ctk.CTkFont(size=10))
        info.insert("end",
            "OpenSky Network (ADS-B flights)    — No key needed\n"
            "Wikidata SPARQL (world leaders)    — No key needed\n"
            "GDELT Project (political events)   — No key needed\n"
            "OFAC SDN List (US sanctions)       — No key needed\n"
            "UN / EU Consolidated Sanctions     — No key needed\n"
            "crt.sh (certificate transparency)  — No key needed\n"
            "NUFORC (UAP sightings)             — No key needed\n"
            "FCC ULS (RF licenses)              — No key needed\n"
            "ICIJ Offshore Leaks               — No key needed\n"
            "SEC EDGAR (US filings)             — No key needed\n"
            "Wayback Machine / Archive.org      — No key needed\n"
            "Wikipedia / MediaWiki              — No key needed\n"
            "FBI Wanted + Interpol Red Notices  — No key needed\n"
            "OpenAlex (250M+ papers)            — No key needed\n"
            "ip-api.com (IP geolocation)        — No key needed  ← replaces IPinfo+AbuseIPDB\n"
            "abuse.ch URLhaus (threat intel)    — No key needed  ← replaces VirusTotal\n"
            "abuse.ch MalwareBazaar             — No key needed  ← replaces VirusTotal\n"
            "Ollama (local AI)                  — No key needed  ← replaces Groq\n"
            "Email pattern guesser + MX check   — No key needed  ← replaces Hunter.io\n"
        )
        info.configure(state="disabled")
        info.pack(fill="x", padx=4, pady=4)

    def _test_ollama(self):
        def _check():
            try:
                import httpx
                from core import settings as cfg
                url = cfg.get("ollama_url", "http://localhost:11434")
                r = httpx.get(f"{url}/api/tags", timeout=3)
                ok = r.status_code == 200
                if ok:
                    try:
                        import ollama
                        client = ollama.Client(host=url)
                        result = client.list()
                        models = result.get("models", []) if isinstance(result, dict) else list(result)
                        names = [m.get("name", "") if isinstance(m, dict) else str(m)
                                 for m in models if m]
                        if names:
                            self.after(0, lambda: self._ol_model_menu.configure(values=names))
                    except Exception:
                        pass
            except Exception:
                ok = False
            color = "#238636" if ok else "#da3633"
            text = "Running" if ok else "Not detected — install from ollama.com/download"
            self.after(0, lambda: self._ol_status_lbl.configure(text=text, text_color=color))

        threading.Thread(target=_check, daemon=True).start()

    def _open_wizard(self):
        from gui.setup_wizard import SetupWizard
        wizard = SetupWizard()
        wizard.mainloop()

    def _section_label_full(self, parent, text: str):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w", padx=4, pady=(12, 4))

    def _api_key_row(self, parent, label: str, key: str, placeholder: str):
        row = ctk.CTkFrame(parent, fg_color=COLORS["panel_bg"], corner_radius=6)
        row.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(row, text=label, width=200, anchor="w",
                     text_color=COLORS["text_muted"], font=ctk.CTkFont(size=12)).pack(side="left", padx=12)
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, fg_color=COLORS["input_bg"],
                             text_color=COLORS["text"], show="*", width=280)
        entry.pack(side="left", padx=4, pady=6)
        ctk.CTkButton(row, text="Save", width=60, height=28, fg_color=COLORS["accent"],
                      command=lambda e=entry, k=key: self._save_key(k, e.get())).pack(side="left", padx=4)

    def _setting_row(self, parent, label: str, key: str, placeholder: str):
        row = ctk.CTkFrame(parent, fg_color=COLORS["panel_bg"], corner_radius=6)
        row.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(row, text=label, width=200, anchor="w",
                     text_color=COLORS["text_muted"], font=ctk.CTkFont(size=12)).pack(side="left", padx=12)
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, fg_color=COLORS["input_bg"],
                             text_color=COLORS["text"], width=280)
        entry.pack(side="left", padx=4, pady=6)
        ctk.CTkButton(row, text="Save", width=60, height=28, fg_color=COLORS["accent"],
                      command=lambda e=entry, k=key: self._save_key(k, e.get())).pack(side="left", padx=4)

    def _save_key(self, key: str, value: str):
        if value:
            self.run_command(["settings", "set", key, value], clear=False)
