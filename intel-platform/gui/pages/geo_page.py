"""Geopolitical intelligence page."""
import customtkinter as ctk
from gui.pages.base_page import BasePage, COLORS


class GeoPage(BasePage):
    PAGE_TITLE = "Geopolitical Intel"
    PAGE_SUBTITLE = "   Leaders • Sanctions • Events • Conflicts • Contracts"

    def build_page(self):
        self._section_label(self.left_panel, "Module")
        self.module_var = ctk.StringVar(value="leaders")
        modules = [
            ("leaders",   "World Leaders"),
            ("sanctions", "Sanctions Search"),
            ("events",    "Political Events (GDELT)"),
            ("conflicts", "Conflict Monitor"),
        ]
        for val, label in modules:
            ctk.CTkRadioButton(
                self.left_panel, text=label, variable=self.module_var, value=val,
                text_color=COLORS["text"], fg_color=COLORS["accent"],
            ).pack(anchor="w", padx=16, pady=3)

        self._section_label(self.left_panel, "Parameters")
        self.name_entry    = self._labeled_entry(self.left_panel, "Name / Search Query", "Putin")
        self.country_entry = self._labeled_entry(self.left_panel, "Country (optional)", "Russia")
        self.days_entry    = self._labeled_entry(self.left_panel, "Days lookback", "7")

        self._section_label(self.left_panel, "Options")
        self.refresh_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.left_panel, text="Force refresh from API",
            variable=self.refresh_var, text_color=COLORS["text"], fg_color=COLORS["accent"],
        ).pack(anchor="w", padx=16, pady=4)

        self.live_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.left_panel, text="Fetch live data",
            variable=self.live_var, text_color=COLORS["text"], fg_color=COLORS["accent"],
        ).pack(anchor="w", padx=16, pady=2)

        self._run_button(self.left_panel, "Run Query", self._run)

    def _run(self):
        mod     = self.module_var.get()
        name    = self.name_entry.get().strip()
        country = self.country_entry.get().strip()
        days    = self.days_entry.get().strip() or "7"
        refresh = self.refresh_var.get()
        live    = self.live_var.get()

        args = ["geo", mod]
        if mod == "sanctions" and name:
            args += [name]
        if mod == "leaders":
            if country:
                args += ["--country", country]
            if refresh:
                args += ["--refresh"]
        elif mod in ("events", "conflicts"):
            if country:
                args += ["--country", country]
            if days:
                args += ["--days", days]
            if live:
                args += ["--live"]
        self.run_command(args)
