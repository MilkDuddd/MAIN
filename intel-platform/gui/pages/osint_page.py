"""OSINT module page."""
import customtkinter as ctk
from gui.pages.base_page import BasePage, COLORS


class OSINTPage(BasePage):
    PAGE_TITLE = "OSINT"
    PAGE_SUBTITLE = "   Open Source Intelligence"

    def build_page(self):
        self._section_label(self.left_panel, "Target")
        self.domain_entry = self._labeled_entry(self.left_panel, "Domain / IP / Username", "example.com")

        self._section_label(self.left_panel, "Module")
        self.module_var = ctk.StringVar(value="whois")
        modules = ["whois", "dns", "certs", "social", "github", "dork"]
        for mod in modules:
            ctk.CTkRadioButton(
                self.left_panel, text=mod.upper(), variable=self.module_var, value=mod,
                text_color=COLORS["text"], fg_color=COLORS["accent"],
            ).pack(anchor="w", padx=16, pady=2)

        self._section_label(self.left_panel, "Options")
        self.dork_type_entry = self._labeled_entry(self.left_panel, "Dork type (if dork)", "news")
        self.dns_types_entry = self._labeled_entry(self.left_panel, "DNS types (if dns)", "A,MX,TXT,NS")

        self._run_button(self.left_panel, "Run OSINT Module", self._run)
        self._run_button(self.left_panel, "Run All Modules", self._run_all, color="#6f42c1")

    def _run(self):
        target = self.domain_entry.get().strip()
        if not target:
            self.write_output("Enter a target first.\n", clear=True)
            return
        mod = self.module_var.get()
        if mod == "dork":
            dtype = self.dork_type_entry.get().strip() or "news"
            self.run_command(["osint", "dork", target, "--type", dtype])
        elif mod == "dns":
            types = self.dns_types_entry.get().strip() or "A,MX,TXT,NS"
            self.run_command(["osint", "dns", target, "--types", types])
        else:
            self.run_command(["osint", mod, target])

    def _run_all(self):
        target = self.domain_entry.get().strip()
        if not target:
            self.write_output("Enter a target first.\n", clear=True)
            return
        self.clear_output()
        for mod in ["whois", "dns", "certs", "social", "github"]:
            self.run_command(["osint", mod, target], clear=False)
