"""Power structure intelligence page."""
import customtkinter as ctk
from gui.pages.base_page import BasePage, COLORS


class PowerPage(BasePage):
    PAGE_TITLE = "Power Structures"
    PAGE_SUBTITLE = "   Billionaires • Corporations • Donations • Boards"

    def build_page(self):
        self._section_label(self.left_panel, "Module")
        self.module_var = ctk.StringVar(value="billionaires")
        modules = [
            ("billionaires", "Billionaire List"),
            ("corp",         "Corporation Lookup"),
            ("donations",    "Political Donations"),
            ("board",        "Board Memberships"),
        ]
        for val, label in modules:
            ctk.CTkRadioButton(
                self.left_panel, text=label, variable=self.module_var, value=val,
                text_color=COLORS["text"], fg_color=COLORS["accent"],
            ).pack(anchor="w", padx=16, pady=3)

        self._section_label(self.left_panel, "Parameters")
        self.name_entry    = self._labeled_entry(self.left_panel, "Name / Company", "Rothschild")
        self.country_entry = self._labeled_entry(self.left_panel, "Country (billionaires)", "United States")
        self.top_entry     = self._labeled_entry(self.left_panel, "Top N (billionaires)", "50")

        self._section_label(self.left_panel, "Options")
        self.live_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.left_panel, text="Fetch live data",
            variable=self.live_var, text_color=COLORS["text"], fg_color=COLORS["accent"],
        ).pack(anchor="w", padx=16, pady=4)
        self.refresh_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.left_panel, text="Force refresh",
            variable=self.refresh_var, text_color=COLORS["text"], fg_color=COLORS["accent"],
        ).pack(anchor="w", padx=16, pady=2)

        self._run_button(self.left_panel, "Run Query", self._run)

    def _run(self):
        mod     = self.module_var.get()
        name    = self.name_entry.get().strip()
        country = self.country_entry.get().strip()
        top_n   = self.top_entry.get().strip() or "50"
        live    = self.live_var.get()
        refresh = self.refresh_var.get()

        args = ["power", mod]
        if mod == "billionaires":
            if country:
                args += ["--country", country]
            args += ["--top", top_n]
            if refresh:
                args += ["--refresh"]
        elif mod in ("corp", "donations", "board"):
            if name:
                args += [name]
            if live:
                args += ["--live"]
        self.run_command(args)
