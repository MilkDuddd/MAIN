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

        # AI Engine
        self._section_label_full(scroll, "AI Engine")
        self._api_key_row(scroll, "Groq API Key",         "groq_api_key",   "gsk_…  (free at console.groq.com)")

        # AI model selector
        model_frame = ctk.CTkFrame(scroll, fg_color=COLORS["panel_bg"], corner_radius=8)
        model_frame.pack(fill="x", padx=4, pady=4)
        ctk.CTkLabel(model_frame, text="Model", width=200, anchor="w",
                     text_color=COLORS["text_muted"], font=ctk.CTkFont(size=12)).pack(side="left", padx=12)
        from core import settings as cfg
        self.model_var = ctk.StringVar(value=cfg.get("model", "llama-3.3-70b-versatile"))
        model_menu = ctk.CTkOptionMenu(
            model_frame,
            variable=self.model_var,
            values=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
            fg_color=COLORS["input_bg"],
            button_color=COLORS["accent"],
            text_color=COLORS["text"],
            command=lambda m: self._save_key("model", m),
        )
        model_menu.pack(side="left", padx=4, pady=6)

        # Data Collection (all free with registration)
        self._section_label_full(scroll, "Data Collection — Free with Registration")
        self._api_key_row(scroll, "Shodan API Key",       "shodan_api_key", "…  (free at account.shodan.io)")
        self._api_key_row(scroll, "NewsAPI Key",          "newsapi_key",    "…  (free at newsapi.org/register)")
        self._api_key_row(scroll, "AISStream Key",        "aisstream_key",  "…  (free at aisstream.io)")
        self._api_key_row(scroll, "FEC API Key",          "fec_api_key",    "…  (free at api.open.fec.gov)")
        self._api_key_row(scroll, "SAM.gov API Key",      "sam_gov_key",    "…  (free at sam.gov)")

        # Advanced / Threat Intel
        self._section_label_full(scroll, "Advanced — Free with Registration")
        self._api_key_row(scroll, "AlienVault OTX Key",      "otx_key",  "…  (free at otx.alienvault.com)")
        self._api_key_row(scroll, "Global Fishing Watch Key", "gfw_key",  "…  (free research account)")

        # General settings
        self._section_label_full(scroll, "General Settings")
        self._setting_row(scroll, "Analyst Name",   "analyst_name", "Intel Analyst")
        self._setting_row(scroll, "Output Directory", "output_dir", "~/intel-reports")

        # Action buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", pady=12)
        ctk.CTkButton(btn_row, text="Show All Settings", fg_color=COLORS["accent"],
                      command=lambda: self.run_command(["settings", "show"])).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Test Groq Connection", fg_color="#27ae60",
                      command=lambda: self.run_command(["ask", "Say hello and confirm you are connected."])).pack(side="left", padx=4)

        # API registry info
        self._section_label_full(scroll, "No-Key Data Sources (Free & Immediate)")
        info = ctk.CTkTextbox(scroll, height=200, fg_color=COLORS["input_bg"],
                              text_color=COLORS["text_muted"], font=ctk.CTkFont(size=10))
        info.insert("end",
            "OpenSky Network (ADS-B flights)      — No key needed\n"
            "Wikidata SPARQL (leaders, Congress)  — No key needed\n"
            "GDELT Project (events, conflicts)    — No key needed\n"
            "OFAC SDN / UN / EU Sanctions         — No key needed\n"
            "crt.sh (certificate transparency)   — No key needed\n"
            "NUFORC (UAP sightings)               — No key needed\n"
            "FCC ULS (RF licenses)                — No key needed\n"
            "ICIJ Offshore Leaks                  — No key needed\n"
            "SEC EDGAR (US filings)               — No key needed\n"
            "Wayback Machine / Archive.org        — No key needed\n"
            "Wikipedia / MediaWiki                — No key needed\n"
            "FBI Wanted + Interpol Red Notices    — No key needed\n"
            "OpenAlex (250M+ academic papers)     — No key needed\n"
            "ReliefWeb (crisis/conflict reports)  — No key needed\n"
            "ip-api.com (IP geolocation)          — No key needed\n"
            "abuse.ch URLhaus (threat intel)      — No key needed\n"
            "abuse.ch MalwareBazaar (hashes)      — No key needed\n"
            "HIBP (domain breach lookup)          — No key needed\n"
            "OpenCorporates (corporate data)      — No key needed (rate limited)\n"
        )
        info.configure(state="disabled")
        info.pack(fill="x", padx=4, pady=4)

    def _section_label_full(self, parent, text: str):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w", padx=4, pady=(12, 4))

    def _api_key_row(self, parent, label: str, key: str, placeholder: str):
        from core import settings as cfg
        row = ctk.CTkFrame(parent, fg_color=COLORS["panel_bg"], corner_radius=6)
        row.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(row, text=label, width=210, anchor="w",
                     text_color=COLORS["text_muted"], font=ctk.CTkFont(size=12)).pack(side="left", padx=12)
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, fg_color=COLORS["input_bg"],
                             text_color=COLORS["text"], show="*", width=300)
        entry.pack(side="left", padx=4, pady=6)
        current = cfg.get(key, "")
        if current:
            entry.insert(0, current)
        ctk.CTkButton(row, text="Save", width=60, height=28, fg_color=COLORS["accent"],
                      command=lambda e=entry, k=key: self._save_key(k, e.get())).pack(side="left", padx=4)

    def _setting_row(self, parent, label: str, key: str, placeholder: str):
        from core import settings as cfg
        row = ctk.CTkFrame(parent, fg_color=COLORS["panel_bg"], corner_radius=6)
        row.pack(fill="x", padx=4, pady=2)
        ctk.CTkLabel(row, text=label, width=210, anchor="w",
                     text_color=COLORS["text_muted"], font=ctk.CTkFont(size=12)).pack(side="left", padx=12)
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, fg_color=COLORS["input_bg"],
                             text_color=COLORS["text"], width=300)
        entry.pack(side="left", padx=4, pady=6)
        current = cfg.get(key, "")
        if current:
            entry.insert(0, current)
        ctk.CTkButton(row, text="Save", width=60, height=28, fg_color=COLORS["accent"],
                      command=lambda e=entry, k=key: self._save_key(k, e.get())).pack(side="left", padx=4)

    def _save_key(self, key: str, value: str):
        if value:
            from core import settings as cfg
            cfg.set(key, value)
            self.app.set_status(f"Saved: {key}", "success")
