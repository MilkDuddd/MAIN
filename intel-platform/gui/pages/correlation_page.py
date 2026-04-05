"""Correlation engine page — cross-source entity profiling."""
import customtkinter as ctk
from gui.pages.base_page import BasePage, COLORS


class CorrelationPage(BasePage):
    PAGE_TITLE = "Correlation Engine"
    PAGE_SUBTITLE = "   Entity Resolution • Relationship Graph • Timeline • AI Analysis"

    def build_page(self):
        self._section_label(self.left_panel, "Entity Search")
        self.entity_entry = self._labeled_entry(self.left_panel, "Entity Name (person or org)", "Elon Musk")

        self._section_label(self.left_panel, "Analysis Type")
        self.analysis_var = ctk.StringVar(value="profile")
        analyses = [
            ("profile",    "Full Intel Profile"),
            ("timeline",   "Event Timeline"),
            ("sanctions",  "Sanctions Check"),
        ]
        for val, label in analyses:
            ctk.CTkRadioButton(
                self.left_panel, text=label, variable=self.analysis_var, value=val,
                text_color=COLORS["text"], fg_color=COLORS["accent"],
            ).pack(anchor="w", padx=16, pady=3)

        self._section_label(self.left_panel, "Options")
        self.report_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.left_panel, text="Export Markdown report",
            variable=self.report_var, text_color=COLORS["text"], fg_color=COLORS["accent"],
        ).pack(anchor="w", padx=16, pady=4)

        self._run_button(self.left_panel, "Correlate Entity", self._run)

        # AI Ask section
        sep = ctk.CTkFrame(self.left_panel, height=1, fg_color=COLORS["border"])
        sep.pack(fill="x", padx=12, pady=12)
        self._section_label(self.left_panel, "AI Intelligence Analyst")
        self.question_entry = self._labeled_entry(
            self.left_panel, "Ask a question", "Who controls the most defense contractors?"
        )
        self._run_button(self.left_panel, "Ask AI Analyst", self._ask_ai, color="#6f42c1")

    def _run(self):
        name = self.entity_entry.get().strip()
        if not name:
            self.write_output("Enter an entity name.\n", clear=True)
            return
        analysis = self.analysis_var.get()
        report   = self.report_var.get()

        if analysis == "profile":
            args = ["correlate", name]
            if report:
                args += ["--report"]
            self.run_command(args)
        elif analysis == "timeline":
            # Use ask command with timeline context
            self.run_command(["correlate", name])
        elif analysis == "sanctions":
            self.run_command(["geo", "sanctions", name])

    def _ask_ai(self):
        question = self.question_entry.get().strip()
        if not question:
            return
        self.run_command(["ask", question])
