"""First-run setup wizard for Intel Platform."""
import subprocess
import threading
import platform
import shutil
import sys
from pathlib import Path

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg":         "#0d1117",
    "sidebar":    "#161b22",
    "content":    "#1c2128",
    "panel":      "#21262d",
    "accent":     "#238636",
    "accent2":    "#1f6feb",
    "text":       "#e6edf3",
    "muted":      "#8b949e",
    "border":     "#30363d",
    "success":    "#238636",
    "warning":    "#d29922",
    "error":      "#da3633",
    "input":      "#0d1117",
}

STEPS = ["Welcome", "AI Engine", "API Keys", "Done"]

_OPTIONAL_KEYS = [
    # (label, settings_key, signup_url, description)
    ("─── Government Data (All Free) ───", None, None, None),
    ("FEC API Key", "fec_api_key", "https://api.open.fec.gov/developers/", "US political donations"),
    ("SAM.gov Key", "sam_gov_key", "https://sam.gov/content/entity-information", "US government contracts"),
    ("ProPublica Key", "propublica_key", "https://www.propublica.org/datastore/api/propublica-congress-api", "Congress votes & bills"),
    ("ACLED Email", "acled_email", "https://developer.acleddata.com/", "Conflict event data"),
    ("ACLED API Key", "acled_key", "https://developer.acleddata.com/", "Conflict event data"),
    ("─── Research & Threat Intel (All Free) ───", None, None, None),
    ("AlienVault OTX Key", "otx_key", "https://otx.alienvault.com/accounts/signup", "Indicators of compromise"),
    ("Global Fishing Watch Key", "gfw_key", "https://globalfishingwatch.org/our-apis/", "Vessel / IUU fishing intel"),
    ("HaveIBeenPwned Key", "hibp_key", "https://haveibeenpwned.com/API/Key", "Data breach lookup"),
    ("─── Infrastructure (Free Tier) ───", None, None, None),
    ("Shodan Key", "shodan_api_key", "https://account.shodan.io/", "Internet device scanning"),
    ("NewsAPI Key", "newsapi_key", "https://newsapi.org/register", "News aggregation"),
    ("AISStream Key", "aisstream_key", "https://aisstream.io/", "Vessel AIS tracking"),
    ("OpenCorporates Key", "opencorp_key", "https://opencorporates.com/api_accounts/new", "Corporate registry"),
]


class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Intel Platform — First-Time Setup")
        self.geometry("920x660")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])

        self._current_step = 0
        self._key_entries: dict = {}
        self._ollama_status = False

        self._build_layout()
        self._show_step(0)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        # Sidebar
        self._sidebar = ctk.CTkFrame(self, width=200, fg_color=COLORS["sidebar"], corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        ctk.CTkLabel(self._sidebar, text="Intel Platform", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["accent"]).pack(pady=(24, 4), padx=16, anchor="w")
        ctk.CTkLabel(self._sidebar, text="Setup Wizard", font=ctk.CTkFont(size=11),
                     text_color=COLORS["muted"]).pack(padx=16, anchor="w")

        ctk.CTkFrame(self._sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=16)

        self._step_labels = []
        for i, name in enumerate(STEPS):
            lbl = ctk.CTkLabel(self._sidebar, text=f"  {i+1}. {name}",
                               font=ctk.CTkFont(size=12),
                               text_color=COLORS["muted"], anchor="w", width=180)
            lbl.pack(padx=8, pady=3, anchor="w")
            self._step_labels.append(lbl)

        # Main content area
        self._content = ctk.CTkFrame(self, fg_color=COLORS["content"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        self._step_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self._step_frame.pack(fill="both", expand=True, padx=32, pady=24)

        # Bottom nav
        nav = ctk.CTkFrame(self._content, fg_color=COLORS["panel"], height=56, corner_radius=0)
        nav.pack(fill="x", side="bottom")
        nav.pack_propagate(False)
        self._btn_back = ctk.CTkButton(nav, text="← Back", width=100, height=34,
                                       fg_color=COLORS["panel"], border_width=1,
                                       border_color=COLORS["border"], text_color=COLORS["text"],
                                       command=self._prev_step)
        self._btn_back.pack(side="left", padx=16, pady=11)
        self._btn_next = ctk.CTkButton(nav, text="Next →", width=120, height=34,
                                       fg_color=COLORS["accent2"],
                                       command=self._next_step)
        self._btn_next.pack(side="right", padx=16, pady=11)

    def _clear_step_frame(self):
        for w in self._step_frame.winfo_children():
            w.destroy()

    def _update_sidebar(self):
        for i, lbl in enumerate(self._step_labels):
            if i == self._current_step:
                lbl.configure(text_color=COLORS["accent"], font=ctk.CTkFont(size=12, weight="bold"))
            elif i < self._current_step:
                lbl.configure(text_color=COLORS["success"], font=ctk.CTkFont(size=12))
            else:
                lbl.configure(text_color=COLORS["muted"], font=ctk.CTkFont(size=12))

    def _show_step(self, step: int):
        self._current_step = step
        self._clear_step_frame()
        self._update_sidebar()
        self._btn_back.configure(state="normal" if step > 0 else "disabled")

        if step == 0:
            self._build_welcome()
        elif step == 1:
            self._build_ollama()
        elif step == 2:
            self._build_api_keys()
        elif step == 3:
            self._build_done()
            self._btn_next.configure(text="Launch  ", state="disabled")

    def _next_step(self):
        if self._current_step < len(STEPS) - 1:
            self._show_step(self._current_step + 1)

    def _prev_step(self):
        if self._current_step > 0:
            self._show_step(self._current_step - 1)

    # ── Step 1: Welcome ───────────────────────────────────────────────────────

    def _build_welcome(self):
        f = self._step_frame
        ctk.CTkLabel(f, text="Welcome to Intel Platform",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(f, text="OSINT · SIGINT · Geopolitical Intelligence Suite",
                     font=ctk.CTkFont(size=13), text_color=COLORS["muted"]).pack(anchor="w", pady=(0, 20))

        badge = ctk.CTkFrame(f, fg_color=COLORS["success"], corner_radius=6)
        badge.pack(anchor="w", pady=(0, 20))
        ctk.CTkLabel(badge, text="  100% Open Source — Zero API keys required for core functionality  ",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="white").pack(padx=8, pady=6)

        info_frame = ctk.CTkFrame(f, fg_color=COLORS["panel"], corner_radius=8)
        info_frame.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(info_frame, text="System Information",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w", padx=16, pady=(12, 6))

        sysinfo = [
            ("Python", sys.version.split()[0]),
            ("Platform", platform.system() + " " + platform.release()),
            ("Free Disk", self._free_disk()),
            ("Install Path", str(Path(__file__).parent.parent)),
        ]
        for label, value in sysinfo:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(row, text=f"{label}:", width=120, anchor="w",
                         text_color=COLORS["muted"], font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkLabel(row, text=value, anchor="w",
                         text_color=COLORS["text"], font=ctk.CTkFont(size=11)).pack(side="left")
        ctk.CTkFrame(info_frame, height=12, fg_color="transparent").pack()

        ctk.CTkLabel(f, text="This wizard will guide you through:\n"
                     "  • Setting up the AI engine (Ollama — runs locally, no cloud)\n"
                     "  • Entering optional API keys for extended data sources\n\n"
                     "All keys are stored locally at ~/.intel-platform/settings.json",
                     font=ctk.CTkFont(size=12), text_color=COLORS["muted"],
                     justify="left").pack(anchor="w")

    def _free_disk(self) -> str:
        try:
            total, used, free = shutil.disk_usage("/")
            return f"{free // (1024**3)} GB free"
        except Exception:
            return "Unknown"

    # ── Step 2: Ollama ────────────────────────────────────────────────────────

    def _build_ollama(self):
        f = self._step_frame
        ctk.CTkLabel(f, text="AI Engine — Ollama",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(f, text="Local LLM — runs on your machine, no API key, no data sent to cloud",
                     font=ctk.CTkFont(size=12), text_color=COLORS["muted"]).pack(anchor="w", pady=(0, 20))

        # Status panel
        status_frame = ctk.CTkFrame(f, fg_color=COLORS["panel"], corner_radius=8)
        status_frame.pack(fill="x", pady=(0, 16))

        status_row = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(status_row, text="Ollama Status:", width=120, anchor="w",
                     text_color=COLORS["muted"]).pack(side="left")
        self._ollama_status_lbl = ctk.CTkLabel(status_row, text="Checking...",
                                                text_color=COLORS["warning"])
        self._ollama_status_lbl.pack(side="left")
        ctk.CTkButton(status_row, text="Refresh", width=80, height=28,
                      fg_color=COLORS["panel"], border_width=1,
                      border_color=COLORS["border"], text_color=COLORS["text"],
                      command=self._check_ollama).pack(side="right")

        # Model controls
        model_row = ctk.CTkFrame(status_frame, fg_color="transparent")
        model_row.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(model_row, text="Model:", width=120, anchor="w",
                     text_color=COLORS["muted"]).pack(side="left")
        self._model_var = ctk.StringVar(value="llama3.2")
        self._model_dropdown = ctk.CTkOptionMenu(model_row, variable=self._model_var,
                                                  values=["llama3.2", "llama3.1:8b", "mistral",
                                                          "deepseek-r1:7b", "gemma2:9b"],
                                                  fg_color=COLORS["input"],
                                                  button_color=COLORS["accent2"],
                                                  width=200)
        self._model_dropdown.pack(side="left", padx=8)

        pull_row = ctk.CTkFrame(status_frame, fg_color="transparent")
        pull_row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(pull_row, text="Pull Model", width=120, height=32,
                      fg_color=COLORS["accent"],
                      command=self._pull_model).pack(side="left")
        self._pull_status = ctk.CTkLabel(pull_row, text="", text_color=COLORS["muted"],
                                          font=ctk.CTkFont(size=11))
        self._pull_status.pack(side="left", padx=12)

        # Instructions
        inst_frame = ctk.CTkFrame(f, fg_color=COLORS["panel"], corner_radius=8)
        inst_frame.pack(fill="x")
        ctk.CTkLabel(inst_frame, text="Don't have Ollama?",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=COLORS["accent"]).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(inst_frame,
                     text="1. Download from: https://ollama.com/download\n"
                          "2. Install and run — it starts automatically in the background\n"
                          "3. Click 'Refresh' above, then 'Pull Model' to download llama3.2\n\n"
                          "Without Ollama, all other platform features still work fully.\n"
                          "You can install it later — click Next to continue.",
                     font=ctk.CTkFont(size=11), text_color=COLORS["muted"],
                     justify="left").pack(anchor="w", padx=16, pady=(0, 16))

        self._check_ollama()

    def _check_ollama(self):
        def _check():
            try:
                import httpx
                from core import settings
                url = settings.get("ollama_url", "http://localhost:11434")
                r = httpx.get(f"{url}/api/tags", timeout=3)
                ok = r.status_code == 200
                if ok:
                    import ollama
                    client = ollama.Client(host=url)
                    result = client.list()
                    models = result.get("models", []) if isinstance(result, dict) else list(result)
                    names = [m.get("name", "") if isinstance(m, dict) else str(m) for m in models]
                    if names:
                        self.after(0, lambda: self._model_dropdown.configure(values=names))
                        self.after(0, lambda: self._model_var.set(names[0]))
            except Exception:
                ok = False
            self._ollama_status = ok
            color = COLORS["success"] if ok else COLORS["error"]
            text = "Running" if ok else "Not detected"
            self.after(0, lambda: self._ollama_status_lbl.configure(text=text, text_color=color))

        threading.Thread(target=_check, daemon=True).start()

    def _pull_model(self):
        model = self._model_var.get()
        self._pull_status.configure(text=f"Pulling {model}... (may take a few minutes)", text_color=COLORS["warning"])

        def _pull():
            try:
                result = subprocess.run(
                    ["ollama", "pull", model],
                    capture_output=True, text=True, timeout=600
                )
                if result.returncode == 0:
                    self.after(0, lambda: self._pull_status.configure(
                        text=f"{model} ready!", text_color=COLORS["success"]))
                    self._check_ollama()
                else:
                    err = result.stderr[:80] if result.stderr else "Failed"
                    self.after(0, lambda: self._pull_status.configure(
                        text=f"Error: {err}", text_color=COLORS["error"]))
            except FileNotFoundError:
                self.after(0, lambda: self._pull_status.configure(
                    text="Ollama not installed — see instructions below", text_color=COLORS["error"]))
            except Exception as e:
                self.after(0, lambda: self._pull_status.configure(
                    text=str(e)[:80], text_color=COLORS["error"]))

        threading.Thread(target=_pull, daemon=True).start()

    # ── Step 3: API Keys ──────────────────────────────────────────────────────

    def _build_api_keys(self):
        f = self._step_frame
        ctk.CTkLabel(f, text="Optional API Keys",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(f,
                     text="All keys are optional — the platform works without any.\n"
                          "They unlock additional data sources (all free to register).",
                     font=ctk.CTkFont(size=12), text_color=COLORS["muted"]).pack(anchor="w", pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(f, fg_color=COLORS["panel"], corner_radius=8)
        scroll.pack(fill="both", expand=True)

        from core import settings as cfg

        for item in _OPTIONAL_KEYS:
            label, key, url, desc = item
            if key is None:
                # Section header
                ctk.CTkLabel(scroll, text=label,
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=COLORS["accent2"]).pack(anchor="w", padx=16, pady=(12, 4))
                continue

            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)

            # Label + description
            info = ctk.CTkFrame(row, fg_color="transparent", width=200)
            info.pack(side="left")
            info.pack_propagate(False)
            ctk.CTkLabel(info, text=label, anchor="w",
                         text_color=COLORS["text"], font=ctk.CTkFont(size=11)).pack(anchor="w")
            if desc:
                ctk.CTkLabel(info, text=desc, anchor="w",
                             text_color=COLORS["muted"], font=ctk.CTkFont(size=10)).pack(anchor="w")

            entry = ctk.CTkEntry(row, placeholder_text="paste key here",
                                 fg_color=COLORS["input"], text_color=COLORS["text"],
                                 show="*", width=220, height=28)
            existing = cfg.get(key, "")
            if existing:
                entry.insert(0, existing)
            entry.pack(side="left", padx=8)
            self._key_entries[key] = entry

            if url:
                ctk.CTkButton(row, text="Sign Up", width=72, height=28,
                              fg_color=COLORS["panel"], border_width=1,
                              border_color=COLORS["border"], text_color=COLORS["accent2"],
                              command=lambda u=url: self._open_url(u)).pack(side="left", padx=2)

        ctk.CTkFrame(scroll, height=8, fg_color="transparent").pack()

    def _open_url(self, url: str):
        import webbrowser
        webbrowser.open(url)

    # ── Step 4: Done ──────────────────────────────────────────────────────────

    def _build_done(self):
        f = self._step_frame

        # Save all entered keys before showing summary
        self._save_all_keys()

        ctk.CTkLabel(f, text="You're all set!",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 6))

        # Summary
        from core import settings as cfg
        all_s = cfg.all_settings()
        keys_set = sum(1 for k, v in all_s.items()
                       if k not in ("ollama_model", "ollama_url", "analyst_name", "output_dir",
                                    "auto_update", "alert_keywords", "tracked_entities")
                       and v)

        summary_frame = ctk.CTkFrame(f, fg_color=COLORS["panel"], corner_radius=8)
        summary_frame.pack(fill="x", pady=(0, 20))

        status_items = [
            ("AI Engine (Ollama)", "Ready" if self._ollama_status else "Install when ready",
             COLORS["success"] if self._ollama_status else COLORS["warning"]),
            ("Model", cfg.get("ollama_model", "llama3.2"), COLORS["text"]),
            ("API Keys Configured", str(keys_set), COLORS["text"]),
            ("No-key data sources", "22 sources active", COLORS["success"]),
        ]
        for label, value, color in status_items:
            row = ctk.CTkFrame(summary_frame, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row, text=label + ":", width=200, anchor="w",
                         text_color=COLORS["muted"]).pack(side="left")
            ctk.CTkLabel(row, text=value, anchor="w",
                         text_color=color).pack(side="left")
        ctk.CTkFrame(summary_frame, height=12, fg_color="transparent").pack()

        # Analyst name
        name_frame = ctk.CTkFrame(f, fg_color=COLORS["panel"], corner_radius=8)
        name_frame.pack(fill="x", pady=(0, 20))
        row = ctk.CTkFrame(name_frame, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(row, text="Analyst Name:", width=140, anchor="w",
                     text_color=COLORS["muted"]).pack(side="left")
        self._name_entry = ctk.CTkEntry(row, placeholder_text="Intel Analyst",
                                         fg_color=COLORS["input"], text_color=COLORS["text"],
                                         width=220, height=32)
        self._name_entry.insert(0, cfg.get("analyst_name", "Intel Analyst"))
        self._name_entry.pack(side="left", padx=8)

        ctk.CTkButton(f, text="Launch Intel Platform",
                      height=48, font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=COLORS["success"],
                      command=self._launch).pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(f,
                     text="You can change all settings later in Settings → API Keys",
                     font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack()

    def _save_all_keys(self):
        """Save entered API keys and Ollama model to settings."""
        from core import settings as cfg

        # Save optional API keys
        for key, entry in self._key_entries.items():
            value = entry.get().strip()
            if value:
                cfg.set(key, value)

        # Save selected Ollama model
        if hasattr(self, "_model_var"):
            cfg.set("ollama_model", self._model_var.get())

    def _launch(self):
        """Save final settings and launch main app."""
        from core import settings as cfg

        self._save_all_keys()

        # Save analyst name
        if hasattr(self, "_name_entry"):
            name = self._name_entry.get().strip()
            if name:
                cfg.set("analyst_name", name)

        self.destroy()

        from gui.app_window import launch
        launch()
