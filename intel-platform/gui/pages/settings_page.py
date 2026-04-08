"""Settings page for Intel Platform GUI."""
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

        # ── Groq AI Section ────────────────────────────────────────────────────
        self._section_label_full(scroll, "AI Engine — Groq")
        self._api_key_row(scroll, "Groq API Key", "groq_api_key", "gsk_...")

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
        # AI model selector
        self._section_label_full(scroll, "AI Model")
        model_frame = ctk.CTkFrame(scroll, fg_color=COLORS["panel_bg"], corner_radius=8)
        model_frame.pack(fill="x", padx=4, pady=4)
        self.model_var = ctk.StringVar(value="llama-3.3-70b-versatile")
        for model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"]:
            ctk.CTkRadioButton(
                model_frame, text=model, variable=self.model_var, value=model,
                text_color=COLORS["text"], fg_color=COLORS["accent"],
                command=lambda m=model: self.run_command(["settings", "set", "model", m], clear=False),
            ).pack(anchor="w", padx=16, pady=4)

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=12)
        ctk.CTkButton(btn_row, text="Show All Settings", fg_color=COLORS["accent"],
                      command=lambda: self.run_command(["settings", "show"])).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Test Groq Connection", fg_color="#27ae60",
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
            "ip-api.com (IP geolocation)        — No key needed\n"
            "abuse.ch URLhaus (threat intel)    — No key needed\n"
            "abuse.ch MalwareBazaar             — No key needed\n"
            "Email pattern guesser + MX check   — No key needed\n"
            "ACLED (conflict data)              — Free registration required\n"
            "SAM.gov (gov contracts)            — Free API key required\n"
            "FEC (political donations)          — Free API key required\n"
            "ProPublica Congress                — Free API key (instant)\n"
            "Groq AI                            — Free: generous limits\n"
            "AlienVault OTX                     — Free: 10,000 req/hour\n"
            "Global Fishing Watch               — Free research account\n"
            "HaveIBeenPwned                     — Domain: free; Email: $3.50/mo\n"
        )
        info.configure(state="disabled")
        info.pack(fill="x", padx=4, pady=4)

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
