"""SIGINT module page — flight/vessel tracking and RF spectrum."""
import customtkinter as ctk
from gui.pages.base_page import BasePage, COLORS


class SIGINTPage(BasePage):
    PAGE_TITLE = "SIGINT / Tracking"
    PAGE_SUBTITLE = "   ADS-B Flights • AIS Vessels • RF Spectrum"

    def build_page(self):
        self._section_label(self.left_panel, "Data Source")
        self.source_var = ctk.StringVar(value="flights")
        for val, label in [("flights", "ADS-B Flights (OpenSky)"), ("vessels", "AIS Vessels"), ("fcc", "FCC RF License")]:
            ctk.CTkRadioButton(
                self.left_panel, text=label, variable=self.source_var, value=val,
                text_color=COLORS["text"], fg_color=COLORS["accent"],
                command=self._on_source_change,
            ).pack(anchor="w", padx=16, pady=3)

        self._section_label(self.left_panel, "Filters")
        self.callsign_entry = self._labeled_entry(self.left_panel, "Callsign / MMSI / FCC Callsign", "UAL123")
        self.country_entry  = self._labeled_entry(self.left_panel, "Country / Flag", "United States")
        self.bbox_entry     = self._labeled_entry(self.left_panel, "Bounding Box (lat_min,lon_min,lat_max,lon_max)", "37,-122,38,-121")

        self._section_label(self.left_panel, "Mode")
        self.live_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.left_panel, text="Fetch Live Data",
            variable=self.live_var, text_color=COLORS["text"], fg_color=COLORS["accent"],
        ).pack(anchor="w", padx=16, pady=4)

        self._run_button(self.left_panel, "Query", self._run)

    def _on_source_change(self):
        src = self.source_var.get()
        self.bbox_entry.configure(state="normal" if src == "flights" else "disabled")

    def _run(self):
        src = self.source_var.get()
        callsign = self.callsign_entry.get().strip()
        country  = self.country_entry.get().strip()
        bbox     = self.bbox_entry.get().strip()
        live     = self.live_var.get()
        args = ["sigint", src]
        if callsign:
            args += ["--callsign" if src == "flights" else "--mmsi", callsign]
        if country:
            args += ["--country", country]
        if bbox and src == "flights":
            args += ["--bbox", bbox]
        if live:
            args += ["--live"]
        if src == "fcc" and callsign:
            args = ["sigint", "fcc", callsign]
        self.run_command(args)
