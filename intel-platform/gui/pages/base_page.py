"""Base page class for all Intel Platform GUI pages."""

import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from gui.app_window import IntelPlatformApp

COLORS = {
    "sidebar_bg":   "#0d1117",
    "content_bg":   "#161b22",
    "accent":       "#1f6feb",
    "accent_hover": "#388bfd",
    "text":         "#c9d1d9",
    "text_muted":   "#8b949e",
    "selected":     "#ffffff",
    "border":       "#30363d",
    "success":      "#3fb950",
    "warning":      "#d29922",
    "danger":       "#f85149",
    "panel_bg":     "#21262d",
    "input_bg":     "#0d1117",
}


class BasePage(ctk.CTkFrame):
    """
    Base class for all pages. Provides:
    - Standard header with title
    - Input panel (left) + output panel (right)
    - run_command() helper that executes CLI commands and streams output
    """

    PAGE_TITLE = "Intel Page"
    PAGE_SUBTITLE = ""

    def __init__(self, parent, app: "IntelPlatformApp"):
        super().__init__(parent, corner_radius=0, fg_color=COLORS["content_bg"])
        self.app = app
        self._running = False
        self._build_base()
        self.build_page()

    def _build_base(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["panel_bg"], corner_radius=0, height=56)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=self.PAGE_TITLE,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["selected"],
        ).pack(side="left", padx=20, pady=8)
        if self.PAGE_SUBTITLE:
            ctk.CTkLabel(
                header,
                text=self.PAGE_SUBTITLE,
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_muted"],
            ).pack(side="left", padx=0, pady=8)

        # Export buttons (right-aligned in header)
        for fmt, color in [("MD", "#27ae60"), ("CSV", "#f39c12"), ("JSON", COLORS["accent"])]:
            ctk.CTkButton(
                header, text=fmt, width=44, height=26,
                fg_color=color, hover_color=color,
                text_color="white", font=ctk.CTkFont(size=11),
                corner_radius=4,
                command=lambda f=fmt.lower(): self._export(f),
            ).pack(side="right", padx=4, pady=14)

        # Main content split
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS["content_bg"])
        self.main_frame.pack(fill="both", expand=True, padx=12, pady=8)

        # Left panel (inputs)
        self.left_panel = ctk.CTkFrame(self.main_frame, fg_color=COLORS["panel_bg"], corner_radius=8, width=320)
        self.left_panel.pack(side="left", fill="y", padx=(0, 8))
        self.left_panel.pack_propagate(False)

        # Right panel (output)
        self.right_panel = ctk.CTkFrame(self.main_frame, fg_color=COLORS["input_bg"], corner_radius=8)
        self.right_panel.pack(side="left", fill="both", expand=True)

        # Output textbox
        self.output_box = ctk.CTkTextbox(
            self.right_panel,
            corner_radius=0,
            fg_color=COLORS["input_bg"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(family="Courier New", size=12),
            wrap="none",
            state="disabled",
        )
        self.output_box.pack(fill="both", expand=True, padx=4, pady=4)

    def build_page(self):
        """Override in subclass to add page-specific input controls."""
        pass

    def _labeled_entry(self, parent, label: str, placeholder: str = "", row: int = 0) -> ctk.CTkEntry:
        """Create a labeled entry widget."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=12, pady=(8, 2))
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(anchor="w")
        entry = ctk.CTkEntry(
            frame,
            placeholder_text=placeholder,
            fg_color=COLORS["input_bg"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=12),
        )
        entry.pack(fill="x", pady=(2, 0))
        return entry

    def _run_button(self, parent, text: str, command, color: Optional[str] = None) -> ctk.CTkButton:
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            fg_color=color or COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#ffffff",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            corner_radius=6,
        )
        btn.pack(fill="x", padx=12, pady=(12, 4))
        return btn

    def _section_label(self, parent, text: str):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w", padx=12, pady=(16, 2))

    def _export(self, fmt: str):
        """Export current output panel content to a file."""
        try:
            from pathlib import Path
            from datetime import datetime, timezone
            from core import settings as cfg
            text = self.output_box.get("1.0", "end").strip()
            if not text:
                return
            out_dir = cfg.output_dir()
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            page_name = self.PAGE_TITLE.lower().replace(" ", "_")
            filename = f"{page_name}_{ts}.{fmt}"
            path = out_dir / filename
            path.write_text(text, encoding="utf-8")
            self.app.set_status(f"Exported: {filename}", "success")
        except Exception as e:
            self.app.set_status(f"Export failed: {e}", "danger")

    def write_output(self, text: str, clear: bool = False):
        """Write text to the output panel."""
        self.output_box.configure(state="normal")
        if clear:
            self.output_box.delete("1.0", "end")
        self.output_box.insert("end", text)
        self.output_box.see("end")
        self.output_box.configure(state="disabled")

    def clear_output(self):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")

    def run_command(self, args: list[str], clear: bool = True):
        """
        Execute a main.py CLI command in a background thread,
        streaming output to the output panel.
        """
        if self._running:
            self.write_output("\n[Already running — please wait]\n")
            return
        self._running = True
        if clear:
            self.clear_output()

        def _run():
            cmd = [sys.executable, "main.py"] + args
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=str(Path(__file__).parent.parent.parent),
                )
                for line in iter(proc.stdout.readline, ""):
                    self.after(0, lambda l=line: self.write_output(l))
                proc.wait()
            except Exception as e:
                self.after(0, lambda: self.write_output(f"\nError: {e}\n"))
            finally:
                self._running = False
                self.after(0, lambda: self.app.set_status("Ready", "success"))

        self.app.set_status("Running...", "warning")
        threading.Thread(target=_run, daemon=True).start()
