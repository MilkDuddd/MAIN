"""Auto Apply page — mass application engine."""

import json
import threading
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from core.database import execute, execute_write
from core.settings import load as load_settings


class ApplyPage(ctk.CTkFrame):
    def __init__(self, parent, colors: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=colors["content_bg"], **kwargs)
        self.colors = colors
        self.nav_callback = nav_callback
        self._running = False
        self._applied_count = 0
        self._log_lines: list[str] = []
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkLabel(hdr, text="Auto Apply", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.colors["text"]).pack(side="left")

        # Config panel
        config_panel = ctk.CTkFrame(self, fg_color=self.colors["panel_bg"], corner_radius=8)
        config_panel.pack(fill="x", padx=28, pady=(0, 12))

        cfg_scroll = ctk.CTkScrollableFrame(config_panel, fg_color="transparent", height=200)
        cfg_scroll.pack(fill="x", padx=12, pady=12)
        cfg_scroll.columnconfigure(0, weight=1)
        cfg_scroll.columnconfigure(1, weight=1)
        cfg_scroll.columnconfigure(2, weight=1)

        # Row 1: keywords, location, job type
        self._kw_var = ctk.StringVar()
        self._loc_var = ctk.StringVar()
        self._jt_var = ctk.StringVar(value="Any")

        def labeled_entry(parent, row, col, label, var, ph=""):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=col, sticky="ew", padx=6, pady=4)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w")
            ctk.CTkEntry(f, textvariable=var, placeholder_text=ph, fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=34).pack(fill="x")

        labeled_entry(cfg_scroll, 0, 0, "Keywords", self._kw_var, "Software Engineer, Python…")
        labeled_entry(cfg_scroll, 0, 1, "Location", self._loc_var, "Remote / San Francisco…")

        f_jt = ctk.CTkFrame(cfg_scroll, fg_color="transparent")
        f_jt.grid(row=0, column=2, sticky="ew", padx=6, pady=4)
        ctk.CTkLabel(f_jt, text="Job Type", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w")
        ctk.CTkComboBox(f_jt, variable=self._jt_var, values=["Any", "Full-time", "Part-time", "Contract", "Internship"],
                        fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=34).pack(fill="x")

        # Row 2: limits, delay
        self._daily_limit = ctk.StringVar(value="20")
        self._delay = ctk.StringVar(value="3")
        labeled_entry(cfg_scroll, 1, 0, "Daily Application Limit", self._daily_limit, "20")
        labeled_entry(cfg_scroll, 1, 1, "Delay Between Apps (sec)", self._delay, "3")

        # Row 3: options
        opts = ctk.CTkFrame(cfg_scroll, fg_color="transparent")
        opts.grid(row=2, column=0, columnspan=3, sticky="ew", padx=6, pady=6)

        self._easy_only = ctk.BooleanVar(value=True)
        self._skip_dups = ctk.BooleanVar(value=True)
        self._remote_only = ctk.BooleanVar(value=False)
        self._gen_cover = ctk.BooleanVar(value=True)

        for var, label in [
            (self._easy_only, "Easy Apply only"),
            (self._skip_dups, "Skip already applied"),
            (self._remote_only, "Remote only"),
            (self._gen_cover, "AI cover letters"),
        ]:
            ctk.CTkCheckBox(opts, text=label, variable=var, font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(side="left", padx=12)

        # Platform toggles
        plat_row = ctk.CTkFrame(cfg_scroll, fg_color="transparent")
        plat_row.grid(row=3, column=0, columnspan=3, sticky="ew", padx=6, pady=4)
        ctk.CTkLabel(plat_row, text="Platforms:", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(side="left", padx=(0, 8))
        self._plat_vars: dict[str, ctk.BooleanVar] = {}
        for key, label in [("indeed", "Indeed"), ("linkedin", "LinkedIn"), ("glassdoor", "Glassdoor"), ("dice", "Dice"), ("ziprecruiter", "ZipRecruiter")]:
            v = ctk.BooleanVar(value=True)
            self._plat_vars[key] = v
            ctk.CTkCheckBox(plat_row, text=label, variable=v, font=ctk.CTkFont(size=11), text_color=self.colors["text"]).pack(side="left", padx=6)

        # Control buttons
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=28, pady=(0, 8))

        self._start_btn = ctk.CTkButton(
            ctrl, text="⚡ Start Auto Apply", width=180, height=38,
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_applying,
        )
        self._start_btn.pack(side="left", padx=(0, 10))

        self._stop_btn = ctk.CTkButton(
            ctrl, text="■ Stop", width=100, height=38,
            fg_color=self.colors["danger"], state="disabled",
            command=self._stop_applying,
        )
        self._stop_btn.pack(side="left", padx=(0, 20))

        self._progress_label = ctk.CTkLabel(ctrl, text="Ready", font=ctk.CTkFont(size=13), text_color=self.colors["text_muted"])
        self._progress_label.pack(side="left")

        # Progress bar
        self._progress = ctk.CTkProgressBar(self, height=6, fg_color=self.colors["border"], progress_color=self.colors["accent"])
        self._progress.pack(fill="x", padx=28, pady=(0, 12))
        self._progress.set(0)

        # Activity log
        log_panel = ctk.CTkFrame(self, fg_color=self.colors["panel_bg"], corner_radius=8)
        log_panel.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        log_hdr = ctk.CTkFrame(log_panel, fg_color="transparent")
        log_hdr.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(log_hdr, text="Activity Log", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(side="left")
        ctk.CTkButton(log_hdr, text="Clear", width=60, height=24, fg_color=self.colors["panel_bg"], command=self._clear_log).pack(side="right")

        ctk.CTkFrame(log_panel, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=8)
        self._log_box = ctk.CTkTextbox(log_panel, fg_color=self.colors["content_bg"], border_width=0, state="disabled", font=ctk.CTkFont(family="Courier", size=12))
        self._log_box.pack(fill="both", expand=True, padx=8, pady=8)

    def _log(self, msg: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = {"info": "  ", "success": "✓ ", "error": "✗ ", "warn": "⚠ "}.get(level, "  ")
        line = f"[{ts}]  {prefix}{msg}\n"
        self._log_lines.append(line)
        self._log_box.configure(state="normal")
        self._log_box.insert("end", line)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _clear_log(self):
        self._log_lines.clear()
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    def _start_applying(self):
        if not self._kw_var.get().strip():
            messagebox.showwarning("Required", "Enter keywords for what jobs to apply to.")
            return

        from core.settings import get
        profile_id = get("default_profile_id")
        if not profile_id:
            messagebox.showwarning("No Profile", "Create a profile in My Profiles first.")
            return

        self._running = True
        self._applied_count = 0
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._progress.set(0)
        self._log(f"Starting auto-apply session — keywords: '{self._kw_var.get()}'", "info")

        def _worker():
            try:
                from modules.apply.auto_apply import AutoApplyEngine
                engine = AutoApplyEngine(
                    profile_id=profile_id,
                    keywords=self._kw_var.get(),
                    location=self._loc_var.get(),
                    platforms=[k for k, v in self._plat_vars.items() if v.get()],
                    job_type=self._jt_var.get().lower() if self._jt_var.get() != "Any" else None,
                    remote_only=self._remote_only.get(),
                    easy_apply_only=self._easy_only.get(),
                    skip_duplicates=self._skip_dups.get(),
                    generate_cover_letter=self._gen_cover.get(),
                    daily_limit=int(self._daily_limit.get() or 20),
                    delay_seconds=float(self._delay.get() or 3),
                    log_callback=lambda msg, lvl="info": self.after(0, self._log, msg, lvl),
                    progress_callback=lambda applied, total: self.after(0, self._update_progress, applied, total),
                    stop_check=lambda: not self._running,
                )
                engine.run()
            except Exception as e:
                self.after(0, self._log, f"Fatal error: {e}", "error")
            finally:
                self.after(0, self._on_apply_done)

        threading.Thread(target=_worker, daemon=True).start()

    def _update_progress(self, applied: int, total: int):
        self._applied_count = applied
        pct = applied / max(total, 1)
        self._progress.set(min(pct, 1.0))
        self._progress_label.configure(text=f"Applied: {applied} / {total}")

    def _stop_applying(self):
        self._running = False
        self._log("Stop requested — finishing current application…", "warn")

    def _on_apply_done(self):
        self._running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._log(f"Session complete. Total applied: {self._applied_count}", "success")

    def on_show(self):
        cfg = load_settings()
        self._daily_limit.set(str(cfg.get("auto_apply", {}).get("daily_limit", 20)))
        self._delay.set(str(cfg.get("auto_apply", {}).get("delay_seconds", 3)))
