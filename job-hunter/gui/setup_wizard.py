"""First-run setup wizard for Job Hunter."""

import tkinter as tk
from tkinter import messagebox
from datetime import datetime

import customtkinter as ctk

from core import settings, database
from core.exceptions import DatabaseError

COLORS = {
    "bg":       "#0d1117",
    "panel":    "#161b22",
    "accent":   "#238636",
    "text":     "#c9d1d9",
    "muted":    "#8b949e",
    "border":   "#30363d",
    "input_bg": "#21262d",
}


class SetupWizard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Job Hunter — First-Run Setup")
        self.geometry("680x620")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])

        self._step = 0
        self._frames: list[ctk.CTkFrame] = []

        # Shared data
        self._name = ctk.StringVar()
        self._email = ctk.StringVar()
        self._phone = ctk.StringVar()
        self._location = ctk.StringVar()
        self._linkedin = ctk.StringVar()
        self._github = ctk.StringVar()
        self._headline = ctk.StringVar()
        self._summary = ctk.StringVar()
        self._skills = ctk.StringVar()
        self._desired_roles = ctk.StringVar()
        self._anthropic_key = ctk.StringVar()

        self._build()
        self._show_step(0)

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="JOB HUNTER  —  Setup Wizard",
            font=ctk.CTkFont(family="Helvetica", size=16, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=20, pady=14)

        # Step indicator
        self._step_label = ctk.CTkLabel(
            header,
            text="Step 1 of 3",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
        )
        self._step_label.pack(side="right", padx=20)

        # Body
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=28, pady=20)

        # Steps
        self._frames = [
            self._build_step_profile(),
            self._build_step_details(),
            self._build_step_api(),
        ]

        # Navigation
        nav = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=0)
        nav.pack(fill="x", side="bottom")
        self._back_btn = ctk.CTkButton(
            nav, text="← Back", width=100, fg_color="#30363d", hover_color="#3d444d",
            command=self._prev_step,
        )
        self._back_btn.pack(side="left", padx=16, pady=12)
        self._next_btn = ctk.CTkButton(
            nav, text="Next →", width=120, fg_color=COLORS["accent"],
            hover_color="#2ea043", command=self._next_step,
        )
        self._next_btn.pack(side="right", padx=16, pady=12)

    def _field(self, parent, label: str, var: ctk.StringVar, placeholder: str = "", show: str = ""):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text"]).pack(anchor="w", pady=(8, 2))
        entry = ctk.CTkEntry(
            parent, textvariable=var, placeholder_text=placeholder,
            fg_color=COLORS["input_bg"], border_color=COLORS["border"],
            show=show, height=36,
        )
        entry.pack(fill="x")
        return entry

    def _build_step_profile(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._body, fg_color="transparent")
        ctk.CTkLabel(f, text="Your Identity", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(f, text="This creates your primary job-seeker profile.", font=ctk.CTkFont(size=12), text_color=COLORS["muted"]).pack(anchor="w", pady=(0, 16))
        self._field(f, "Full Name *", self._name, "Jane Doe")
        self._field(f, "Email *", self._email, "jane@example.com")
        self._field(f, "Phone", self._phone, "+1 (555) 000-0000")
        self._field(f, "City / Location", self._location, "San Francisco, CA")
        self._field(f, "LinkedIn URL", self._linkedin, "https://linkedin.com/in/...")
        self._field(f, "GitHub URL", self._github, "https://github.com/...")
        return f

    def _build_step_details(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._body, fg_color="transparent")
        ctk.CTkLabel(f, text="Professional Profile", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(f, text="Describe what you do and what you're looking for.", font=ctk.CTkFont(size=12), text_color=COLORS["muted"]).pack(anchor="w", pady=(0, 16))
        self._field(f, "Professional Headline", self._headline, "Senior Software Engineer | Python & Cloud")
        self._field(f, "Desired Roles (comma-separated)", self._desired_roles, "Software Engineer, Backend Developer")
        ctk.CTkLabel(f, text="Skills (comma-separated)", font=ctk.CTkFont(size=12), text_color=COLORS["text"]).pack(anchor="w", pady=(8, 2))
        self._field(f, "", self._skills, "Python, AWS, Docker, PostgreSQL, React")
        ctk.CTkLabel(f, text="Professional Summary", font=ctk.CTkFont(size=12), text_color=COLORS["text"]).pack(anchor="w", pady=(8, 2))
        self._summary_box = ctk.CTkTextbox(
            f, height=90, fg_color=COLORS["input_bg"], border_color=COLORS["border"], border_width=1,
        )
        self._summary_box.pack(fill="x")
        self._summary_box.insert("1.0", "Experienced software engineer with a passion for building scalable systems...")
        return f

    def _build_step_api(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._body, fg_color="transparent")
        ctk.CTkLabel(f, text="AI Integration (Optional)", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            f,
            text="Provide an Anthropic API key to enable AI-powered cover letter generation,\njob matching, and resume tailoring.",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["muted"],
            justify="left",
        ).pack(anchor="w", pady=(0, 16))
        self._field(f, "Anthropic API Key", self._anthropic_key, "sk-ant-...", show="")

        ctk.CTkLabel(f, text="You can add this later in Settings → API Keys.", font=ctk.CTkFont(size=11), text_color=COLORS["muted"]).pack(anchor="w", pady=(8, 0))

        ctk.CTkFrame(f, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=20)

        summary = ctk.CTkFrame(f, fg_color=COLORS["panel"], corner_radius=8)
        summary.pack(fill="x", pady=4)
        ctk.CTkLabel(
            summary,
            text="  What Job Hunter can do for you:\n"
                 "  ✓  Search jobs across Indeed, LinkedIn, Glassdoor, Dice, ZipRecruiter, RemoteOK\n"
                 "  ✓  Auto-apply with Playwright browser automation\n"
                 "  ✓  AI-tailored cover letters and resume snippets\n"
                 "  ✓  Track all your applications in one place\n"
                 "  ✓  Match scores so you apply to the best fits first",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            justify="left",
        ).pack(padx=16, pady=12)
        return f

    def _show_step(self, step: int):
        for f in self._frames:
            f.pack_forget()
        self._frames[step].pack(fill="both", expand=True)
        self._step_label.configure(text=f"Step {step + 1} of {len(self._frames)}")
        self._back_btn.configure(state="normal" if step > 0 else "disabled")
        self._next_btn.configure(text="Finish →" if step == len(self._frames) - 1 else "Next →")

    def _prev_step(self):
        if self._step > 0:
            self._step -= 1
            self._show_step(self._step)

    def _next_step(self):
        if self._step == 0:
            if not self._name.get().strip() or not self._email.get().strip():
                messagebox.showerror("Required", "Name and Email are required.")
                return
        if self._step < len(self._frames) - 1:
            self._step += 1
            self._show_step(self._step)
        else:
            self._finish()

    def _finish(self):
        try:
            database.init_db()
            now = datetime.utcnow().isoformat()
            import json
            skills = [s.strip() for s in self._skills.get().split(",") if s.strip()]
            roles = [r.strip() for r in self._desired_roles.get().split(",") if r.strip()]
            summary_text = self._summary_box.get("1.0", "end").strip()

            profile_id = database.execute_write(
                """INSERT INTO profiles
                   (name, email, phone, location, linkedin_url, github_url,
                    headline, summary, skills, desired_roles, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    self._name.get().strip(),
                    self._email.get().strip(),
                    self._phone.get().strip(),
                    self._location.get().strip(),
                    self._linkedin.get().strip(),
                    self._github.get().strip(),
                    self._headline.get().strip(),
                    summary_text,
                    json.dumps(skills),
                    json.dumps(roles),
                    now, now,
                ),
            )

            cfg = settings.load()
            cfg["default_profile_id"] = profile_id
            if self._anthropic_key.get().strip():
                cfg["anthropic_api_key"] = self._anthropic_key.get().strip()
            settings.save(cfg)

            self.destroy()
            from gui.app_window import launch
            launch()
        except Exception as e:
            messagebox.showerror("Error", f"Setup failed:\n{e}")
