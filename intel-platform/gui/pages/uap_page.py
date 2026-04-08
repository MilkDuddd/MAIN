"""UAP / Anomalous Phenomena intelligence page."""
import customtkinter as ctk
from gui.pages.base_page import BasePage, COLORS


class UAPPage(BasePage):
    PAGE_TITLE = "UAP / Anomalous Phenomena"
    PAGE_SUBTITLE = "   Sightings • Hearings • Declassified Docs • News"

    def build_page(self):
        self._section_label(self.left_panel, "Module")
        self.module_var = ctk.StringVar(value="sightings")
        modules = [
            ("sightings",  "NUFORC Sightings"),
            ("hearings",   "Congressional Hearings"),
            ("documents",  "Declassified Documents"),
            ("news",       "UAP News Feed"),
        ]
        for val, label in modules:
            ctk.CTkRadioButton(
                self.left_panel, text=label, variable=self.module_var, value=val,
                text_color=COLORS["text"], fg_color=COLORS["accent"],
            ).pack(anchor="w", padx=16, pady=3)

        self._section_label(self.left_panel, "Filters")
        self.state_entry   = self._labeled_entry(self.left_panel, "US State (sightings)", "CA")
        self.keyword_entry = self._labeled_entry(self.left_panel, "Keyword / Witness Name", "Grusch")
        self.days_entry    = self._labeled_entry(self.left_panel, "Days lookback (news)", "7")

        self._section_label(self.left_panel, "Options")
        self.refresh_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.left_panel, text="Refresh news feed",
            variable=self.refresh_var, text_color=COLORS["text"], fg_color=COLORS["accent"],
        ).pack(anchor="w", padx=16, pady=4)

        self._run_button(self.left_panel, "Query UAP Intelligence", self._run)

        # Notable encounters info panel
        self._section_label(self.left_panel, "Notable Cases")
        notable = ctk.CTkTextbox(
            self.left_panel, height=120, fg_color=COLORS["input_bg"],
            text_color=COLORS["text_muted"], font=ctk.CTkFont(size=10), state="normal",
        )
        notable.insert("end", "2004 Nimitz 'Tic Tac'\n2014-15 Roosevelt 'Gimbal'\n2006 O'Hare Airport\n1997 Phoenix Lights\n2023 Grusch Testimony\n2024 Elizondo Hearing")
        notable.configure(state="disabled")
        notable.pack(fill="x", padx=12, pady=4)

    def _run(self):
        mod     = self.module_var.get()
        state   = self.state_entry.get().strip()
        keyword = self.keyword_entry.get().strip()
        days    = self.days_entry.get().strip() or "7"
        refresh = self.refresh_var.get()

        args = ["uap", mod]
        if mod == "sightings":
            if state:
                args += ["--state", state]
            if keyword:
                args += ["--keyword", keyword]
            args += ["--days", days]
        elif mod == "hearings" and keyword:
            args += ["--keyword", keyword]
        elif mod == "documents" and keyword:
            args += ["--keyword", keyword]
        elif mod == "news":
            args += ["--days", days]
            if refresh:
                args += ["--refresh"]
        self.run_command(args)
