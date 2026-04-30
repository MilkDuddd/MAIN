"""Profile Builder page — manage job seeker profiles."""

import json
from datetime import datetime
from tkinter import messagebox, filedialog

import customtkinter as ctk

from core.database import execute, execute_write, get_db


class ProfilePage(ctk.CTkFrame):
    def __init__(self, parent, colors: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=colors["content_bg"], **kwargs)
        self.colors = colors
        self.nav_callback = nav_callback
        self._current_profile_id: int | None = None
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkLabel(hdr, text="My Profiles", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.colors["text"]).pack(side="left")
        ctk.CTkButton(
            hdr, text="+ New Profile", width=130, height=32,
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
            command=self._new_profile,
        ).pack(side="right")

        # Main split layout
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # Left: profile list
        left = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(left, text="Profiles", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", padx=14, pady=(12, 6))
        ctk.CTkFrame(left, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=10)
        self._profile_list = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._profile_list.pack(fill="both", expand=True, padx=4, pady=4)

        # Right: editor tabs
        right = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew")

        self._tab_bar = ctk.CTkTabview(right, fg_color=self.colors["panel_bg"])
        self._tab_bar.pack(fill="both", expand=True, padx=8, pady=8)
        for tab in ("Basic Info", "Experience", "Education", "Skills & Goals", "Resume"):
            self._tab_bar.add(tab)

        self._build_basic_tab()
        self._build_experience_tab()
        self._build_education_tab()
        self._build_skills_tab()
        self._build_resume_tab()

        self._load_profile_list()

    # ── Basic Info Tab ────────────────────────────────────────────────────────
    def _build_basic_tab(self):
        tab = self._tab_bar.tab("Basic Info")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._v = {}
        fields = [
            ("name", "Full Name *", "Jane Doe", False),
            ("email", "Email *", "jane@example.com", False),
            ("phone", "Phone", "+1 (555) 000-0000", False),
            ("location", "Location", "San Francisco, CA", False),
            ("linkedin_url", "LinkedIn URL", "https://linkedin.com/in/...", False),
            ("github_url", "GitHub URL", "https://github.com/...", False),
            ("portfolio_url", "Portfolio URL", "https://...", False),
            ("headline", "Professional Headline", "Senior Software Engineer", False),
        ]
        for key, label, ph, secret in fields:
            self._v[key] = ctk.StringVar()
            ctk.CTkLabel(scroll, text=label, font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=(8, 2))
            ctk.CTkEntry(scroll, textvariable=self._v[key], placeholder_text=ph, fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=34).pack(fill="x", padx=8)

        ctk.CTkLabel(scroll, text="Professional Summary", font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=(10, 2))
        self._summary_box = ctk.CTkTextbox(scroll, height=100, fg_color=self.colors["content_bg"], border_color=self.colors["border"], border_width=1)
        self._summary_box.pack(fill="x", padx=8)

        ctk.CTkButton(scroll, text="Save Basic Info", fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save_basic).pack(anchor="e", padx=8, pady=12)

    # ── Experience Tab ────────────────────────────────────────────────────────
    def _build_experience_tab(self):
        tab = self._tab_bar.tab("Experience")
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(top, text="Work Experience", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(side="left")
        ctk.CTkButton(top, text="+ Add", width=80, height=28, fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._add_experience_dialog).pack(side="right")
        ctk.CTkFrame(tab, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=8)
        self._exp_list = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self._exp_list.pack(fill="both", expand=True, padx=4, pady=4)

    def _add_experience_dialog(self):
        if not self._current_profile_id:
            messagebox.showwarning("No Profile", "Select or create a profile first.")
            return
        dlg = _ExperienceDialog(self, self.colors, profile_id=self._current_profile_id, on_save=self._load_experience)
        dlg.grab_set()

    def _load_experience(self):
        for w in self._exp_list.winfo_children():
            w.destroy()
        if not self._current_profile_id:
            return
        rows = execute("SELECT * FROM work_experience WHERE profile_id=? ORDER BY sort_order, id DESC", (self._current_profile_id,))
        for row in rows:
            self._exp_card(row)

    def _exp_card(self, row):
        card = ctk.CTkFrame(self._exp_list, fg_color=self.colors["content_bg"], corner_radius=6)
        card.pack(fill="x", pady=4)
        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        end = "Present" if row["current"] else (row["end_date"] or "")
        ctk.CTkLabel(left, text=row["title"], font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(left, text=f"{row['company']}  ·  {row['start_date'] or ''}  –  {end}", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w")
        if row["description"]:
            ctk.CTkLabel(left, text=row["description"][:100] + "…" if len(row["description"] or "") > 100 else row["description"], font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"], wraplength=400, justify="left").pack(anchor="w")
        ctk.CTkButton(card, text="✕", width=28, height=28, fg_color="transparent", hover_color=self.colors["danger"], text_color=self.colors["danger"], command=lambda rid=row["id"]: self._del_experience(rid)).pack(side="right", padx=8)

    def _del_experience(self, row_id: int):
        execute_write("DELETE FROM work_experience WHERE id=?", (row_id,))
        self._load_experience()

    # ── Education Tab ─────────────────────────────────────────────────────────
    def _build_education_tab(self):
        tab = self._tab_bar.tab("Education")
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(top, text="Education", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(side="left")
        ctk.CTkButton(top, text="+ Add", width=80, height=28, fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._add_education_dialog).pack(side="right")
        ctk.CTkFrame(tab, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=8)
        self._edu_list = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self._edu_list.pack(fill="both", expand=True, padx=4, pady=4)

    def _add_education_dialog(self):
        if not self._current_profile_id:
            messagebox.showwarning("No Profile", "Select or create a profile first.")
            return
        dlg = _EducationDialog(self, self.colors, profile_id=self._current_profile_id, on_save=self._load_education)
        dlg.grab_set()

    def _load_education(self):
        for w in self._edu_list.winfo_children():
            w.destroy()
        if not self._current_profile_id:
            return
        rows = execute("SELECT * FROM education WHERE profile_id=? ORDER BY sort_order, id DESC", (self._current_profile_id,))
        for row in rows:
            card = ctk.CTkFrame(self._edu_list, fg_color=self.colors["content_bg"], corner_radius=6)
            card.pack(fill="x", pady=4)
            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=12, pady=10)
            ctk.CTkLabel(left, text=f"{row['degree']} in {row['field_of_study']}", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{row['institution']}  ·  {row['start_date'] or ''}  –  {row['end_date'] or ''}", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w")
            ctk.CTkButton(card, text="✕", width=28, height=28, fg_color="transparent", hover_color=self.colors["danger"], text_color=self.colors["danger"], command=lambda rid=row["id"]: self._del_education(rid)).pack(side="right", padx=8)

    def _del_education(self, row_id: int):
        execute_write("DELETE FROM education WHERE id=?", (row_id,))
        self._load_education()

    # ── Skills & Goals Tab ────────────────────────────────────────────────────
    def _build_skills_tab(self):
        tab = self._tab_bar.tab("Skills & Goals")
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Skills (comma-separated)", font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=(10, 2))
        self._skills_var = ctk.StringVar()
        ctk.CTkEntry(scroll, textvariable=self._skills_var, placeholder_text="Python, Docker, AWS, React…", fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=34).pack(fill="x", padx=8)

        ctk.CTkLabel(scroll, text="Desired Roles (comma-separated)", font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=(10, 2))
        self._roles_var = ctk.StringVar()
        ctk.CTkEntry(scroll, textvariable=self._roles_var, placeholder_text="Software Engineer, Backend Developer…", fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=34).pack(fill="x", padx=8)

        for label, key in [("Desired Salary", "desired_salary"), ("Job Type", "job_type")]:
            ctk.CTkLabel(scroll, text=label, font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=(10, 2))
            self._v[key] = ctk.StringVar()
            ctk.CTkEntry(scroll, textvariable=self._v[key], fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=34).pack(fill="x", padx=8)

        self._remote_var = ctk.BooleanVar(value=True)
        self._relocate_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(scroll, text="Open to remote", variable=self._remote_var, text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=6)
        ctk.CTkCheckBox(scroll, text="Willing to relocate", variable=self._relocate_var, text_color=self.colors["text"]).pack(anchor="w", padx=8, pady=2)

        ctk.CTkButton(scroll, text="Save Skills & Goals", fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save_skills).pack(anchor="e", padx=8, pady=12)

    # ── Resume Tab ────────────────────────────────────────────────────────────
    def _build_resume_tab(self):
        tab = self._tab_bar.tab("Resume")
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(top, text="Resume / CV", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(side="left")

        # AI parse button (pack right-most first so Import File appears to its left)
        self._parse_btn = ctk.CTkButton(
            top, text="✨ Parse with AI", width=130, height=28,
            fg_color=self.colors["tag_bg"], hover_color="#388bfd",
            command=self._parse_resume_with_ai,
        )
        self._parse_btn.pack(side="right", padx=4)
        ctk.CTkButton(top, text="Import File", width=100, height=28, fg_color=self.colors["panel_bg"], command=self._import_resume).pack(side="right", padx=4)

        self._parse_status = ctk.CTkLabel(tab, text="", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"])
        self._parse_status.pack(anchor="w", padx=8)

        ctk.CTkLabel(tab, text="Import PDF or paste resume text. Then click 'Parse with AI' to auto-fill all profile fields.", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w", padx=8)
        self._resume_box = ctk.CTkTextbox(tab, fg_color=self.colors["content_bg"], border_color=self.colors["border"], border_width=1)
        self._resume_box.pack(fill="both", expand=True, padx=8, pady=4)
        ctk.CTkButton(tab, text="Save Resume", fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save_resume).pack(anchor="e", padx=8, pady=6)

    def _import_resume(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Resume files", "*.pdf *.txt"),
                ("PDF files", "*.pdf"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        try:
            if path.lower().endswith(".pdf"):
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    pages_text = [page.extract_text() or "" for page in pdf.pages]
                text = "\n".join(pages_text).strip()
                if not text:
                    messagebox.showwarning(
                        "Scanned PDF",
                        "No text could be extracted — this appears to be a scanned image PDF.\n"
                        "Please use a text-based PDF or paste your resume manually.",
                    )
                    return
            else:
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
            self._resume_box.delete("1.0", "end")
            self._resume_box.insert("1.0", text)
            self._parse_status.configure(text="Resume imported. Click '✨ Parse with AI' to auto-fill your profile.")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _parse_resume_with_ai(self):
        from core.settings import get as get_setting
        api_key = get_setting("anthropic_api_key")
        if not api_key:
            messagebox.showwarning(
                "API Key Required",
                "Add your Anthropic API key in Settings → API Keys to use AI parsing.",
            )
            if self.nav_callback:
                self.nav_callback("settings")
            return

        if not self._current_profile_id:
            messagebox.showwarning("No Profile", "Select or create a profile first.")
            return

        resume_text = self._resume_box.get("1.0", "end").strip()
        if len(resume_text) < 80:
            messagebox.showwarning(
                "Too Short",
                "Import or paste your resume text first (at least 80 characters).",
            )
            return

        self._parse_btn.configure(state="disabled", text="Parsing…")
        self._parse_status.configure(text="Sending resume to Claude AI…")

        import threading

        def _worker():
            try:
                from modules.ai.resume_parser import parse_resume
                parsed = parse_resume(api_key, resume_text)
                self.after(0, self._apply_parsed_resume, parsed)
            except Exception as e:
                self.after(0, self._on_parse_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_parsed_resume(self, parsed: dict):
        import json
        from datetime import datetime

        # Fill Basic Info StringVars
        for parsed_key in ("name", "email", "phone", "location", "linkedin_url", "github_url", "portfolio_url", "headline"):
            val = parsed.get(parsed_key, "")
            if val and parsed_key in self._v:
                self._v[parsed_key].set(val)

        if parsed.get("summary"):
            self._summary_box.delete("1.0", "end")
            self._summary_box.insert("1.0", parsed["summary"])

        skills_list = parsed.get("skills", [])
        if skills_list:
            self._skills_var.set(", ".join(skills_list))

        now = datetime.utcnow().isoformat()
        pid = self._current_profile_id

        # Save basic info to DB immediately
        execute_write(
            """UPDATE profiles SET name=?, email=?, phone=?, location=?,
               linkedin_url=?, github_url=?, portfolio_url=?, headline=?, summary=?,
               skills=?, updated_at=? WHERE id=?""",
            (
                parsed.get("name", self._v["name"].get()),
                parsed.get("email", self._v["email"].get()),
                parsed.get("phone", ""),
                parsed.get("location", ""),
                parsed.get("linkedin_url", ""),
                parsed.get("github_url", ""),
                parsed.get("portfolio_url", ""),
                parsed.get("headline", ""),
                parsed.get("summary", ""),
                json.dumps(skills_list),
                now, pid,
            ),
        )

        # Import work experience
        experience = parsed.get("experience", [])
        if experience:
            replace = messagebox.askyesno(
                "Import Work Experience",
                f"Found {len(experience)} work experience entries.\n\nReplace existing experience? (No = append)",
            )
            if replace:
                execute_write("DELETE FROM work_experience WHERE profile_id=?", (pid,))
            for i, exp in enumerate(experience):
                execute_write(
                    """INSERT INTO work_experience
                       (profile_id, company, title, location, start_date, end_date, current, description, sort_order)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        pid,
                        exp.get("company", ""),
                        exp.get("title", ""),
                        exp.get("location", ""),
                        exp.get("start_date", ""),
                        exp.get("end_date", ""),
                        int(bool(exp.get("current", False))),
                        exp.get("description", ""),
                        i,
                    ),
                )
            self._load_experience()

        # Import education
        education = parsed.get("education", [])
        if education:
            replace_edu = messagebox.askyesno(
                "Import Education",
                f"Found {len(education)} education entries.\n\nReplace existing education? (No = append)",
            )
            if replace_edu:
                execute_write("DELETE FROM education WHERE profile_id=?", (pid,))
            for i, edu in enumerate(education):
                execute_write(
                    """INSERT INTO education
                       (profile_id, institution, degree, field_of_study, start_date, end_date, gpa, sort_order)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (
                        pid,
                        edu.get("institution", ""),
                        edu.get("degree", ""),
                        edu.get("field_of_study", ""),
                        edu.get("start_date", ""),
                        edu.get("end_date", ""),
                        edu.get("gpa", ""),
                        i,
                    ),
                )
            self._load_education()

        self._load_profile_list()
        self._parse_btn.configure(state="normal", text="✨ Parse with AI")
        self._parse_status.configure(
            text=f"Parsed: {len(experience)} jobs, {len(education)} education, {len(skills_list)} skills imported. Review and save."
        )

    def _on_parse_error(self, msg: str):
        self._parse_btn.configure(state="normal", text="✨ Parse with AI")
        self._parse_status.configure(text="")
        messagebox.showerror("Parse Failed", f"AI parsing error:\n{msg}")

    # ── Data loading & saving ─────────────────────────────────────────────────
    def _load_profile_list(self):
        for w in self._profile_list.winfo_children():
            w.destroy()
        rows = execute("SELECT id, name, email FROM profiles ORDER BY id DESC")
        for row in rows:
            btn = ctk.CTkButton(
                self._profile_list,
                text=f"{row['name']}\n{row['email']}",
                anchor="w", height=48, corner_radius=6,
                fg_color=self.colors["content_bg"], hover_color=self.colors["border"],
                text_color=self.colors["text"], font=ctk.CTkFont(size=12),
                command=lambda pid=row["id"]: self._load_profile(pid),
            )
            btn.pack(fill="x", pady=2)

    def _load_profile(self, profile_id: int):
        self._current_profile_id = profile_id
        row = execute("SELECT * FROM profiles WHERE id=?", (profile_id,))[0]
        for key in ("name", "email", "phone", "location", "linkedin_url", "github_url", "portfolio_url", "headline", "desired_salary", "job_type"):
            if key in self._v:
                self._v[key].set(row[key] or "")
        self._summary_box.delete("1.0", "end")
        self._summary_box.insert("1.0", row["summary"] or "")
        try:
            self._skills_var.set(", ".join(json.loads(row["skills"] or "[]")))
            self._roles_var.set(", ".join(json.loads(row["desired_roles"] or "[]")))
        except Exception:
            pass
        self._remote_var.set(bool(row["willing_remote"]))
        self._relocate_var.set(bool(row["willing_relocate"]))
        self._resume_box.delete("1.0", "end")
        self._resume_box.insert("1.0", row["resume_text"] or "")
        self._load_experience()
        self._load_education()

    def _new_profile(self):
        now = datetime.utcnow().isoformat()
        pid = execute_write("INSERT INTO profiles (name, email, created_at, updated_at) VALUES (?,?,?,?)", ("New Profile", "email@example.com", now, now))
        self._load_profile_list()
        self._load_profile(pid)

    def _save_basic(self):
        if not self._current_profile_id:
            messagebox.showwarning("No Profile", "Select or create a profile first.")
            return
        now = datetime.utcnow().isoformat()
        execute_write(
            """UPDATE profiles SET name=?, email=?, phone=?, location=?, linkedin_url=?, github_url=?,
               portfolio_url=?, headline=?, summary=?, updated_at=? WHERE id=?""",
            (
                self._v["name"].get(), self._v["email"].get(), self._v["phone"].get(),
                self._v["location"].get(), self._v["linkedin_url"].get(), self._v["github_url"].get(),
                self._v["portfolio_url"].get(), self._v["headline"].get(),
                self._summary_box.get("1.0", "end").strip(), now, self._current_profile_id,
            ),
        )
        self._load_profile_list()
        messagebox.showinfo("Saved", "Basic info saved.")

    def _save_skills(self):
        if not self._current_profile_id:
            return
        skills = json.dumps([s.strip() for s in self._skills_var.get().split(",") if s.strip()])
        roles = json.dumps([r.strip() for r in self._roles_var.get().split(",") if r.strip()])
        now = datetime.utcnow().isoformat()
        execute_write(
            """UPDATE profiles SET skills=?, desired_roles=?, desired_salary=?, job_type=?,
               willing_remote=?, willing_relocate=?, updated_at=? WHERE id=?""",
            (skills, roles, self._v["desired_salary"].get(), self._v["job_type"].get(),
             int(self._remote_var.get()), int(self._relocate_var.get()), now, self._current_profile_id),
        )
        messagebox.showinfo("Saved", "Skills & Goals saved.")

    def _save_resume(self):
        if not self._current_profile_id:
            return
        text = self._resume_box.get("1.0", "end").strip()
        execute_write("UPDATE profiles SET resume_text=?, updated_at=? WHERE id=?",
                      (text, datetime.utcnow().isoformat(), self._current_profile_id))
        messagebox.showinfo("Saved", "Resume saved.")

    def on_show(self):
        self._load_profile_list()
        from core.settings import get
        pid = get("default_profile_id")
        if pid and not self._current_profile_id:
            self._load_profile(pid)


# ── Dialogs ───────────────────────────────────────────────────────────────────

class _ExperienceDialog(ctk.CTkToplevel):
    def __init__(self, parent, colors: dict, profile_id: int, on_save=None):
        super().__init__(parent)
        self.colors = colors
        self.profile_id = profile_id
        self.on_save = on_save
        self.title("Add Work Experience")
        self.geometry("520x500")
        self.configure(fg_color=colors["content_bg"])
        self._build()

    def _field(self, parent, label, var, ph=""):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(anchor="w", pady=(8, 2))
        ctk.CTkEntry(parent, textvariable=var, placeholder_text=ph, fg_color=self.colors["panel_bg"], border_color=self.colors["border"], height=34).pack(fill="x")

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        self._company = ctk.StringVar()
        self._title = ctk.StringVar()
        self._location = ctk.StringVar()
        self._start = ctk.StringVar()
        self._end = ctk.StringVar()
        self._current = ctk.BooleanVar()

        self._field(scroll, "Company *", self._company, "Acme Corp")
        self._field(scroll, "Job Title *", self._title, "Software Engineer")
        self._field(scroll, "Location", self._location, "Remote / NYC")
        self._field(scroll, "Start Date", self._start, "Jan 2022")
        self._field(scroll, "End Date", self._end, "Dec 2024")
        ctk.CTkCheckBox(scroll, text="Currently working here", variable=self._current, text_color=self.colors["text"]).pack(anchor="w", pady=8)

        ctk.CTkLabel(scroll, text="Description", font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(anchor="w", pady=(8, 2))
        self._desc_box = ctk.CTkTextbox(scroll, height=100, fg_color=self.colors["panel_bg"], border_color=self.colors["border"], border_width=1)
        self._desc_box.pack(fill="x")

        ctk.CTkButton(scroll, text="Save Experience", fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save).pack(anchor="e", pady=12)

    def _save(self):
        if not self._company.get() or not self._title.get():
            messagebox.showerror("Required", "Company and Title are required.")
            return
        execute_write(
            """INSERT INTO work_experience (profile_id, company, title, location, start_date, end_date, current, description, sort_order)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (self.profile_id, self._company.get(), self._title.get(), self._location.get(),
             self._start.get(), self._end.get(), int(self._current.get()),
             self._desc_box.get("1.0", "end").strip(), 0),
        )
        if self.on_save:
            self.on_save()
        self.destroy()


class _EducationDialog(ctk.CTkToplevel):
    def __init__(self, parent, colors: dict, profile_id: int, on_save=None):
        super().__init__(parent)
        self.colors = colors
        self.profile_id = profile_id
        self.on_save = on_save
        self.title("Add Education")
        self.geometry("520x400")
        self.configure(fg_color=colors["content_bg"])
        self._build()

    def _field(self, parent, label, var, ph=""):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(anchor="w", pady=(8, 2))
        ctk.CTkEntry(parent, textvariable=var, placeholder_text=ph, fg_color=self.colors["panel_bg"], border_color=self.colors["border"], height=34).pack(fill="x")

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        self._institution = ctk.StringVar()
        self._degree = ctk.StringVar()
        self._field_study = ctk.StringVar()
        self._start = ctk.StringVar()
        self._end = ctk.StringVar()
        self._gpa = ctk.StringVar()

        self._field(scroll, "Institution *", self._institution, "MIT / Stanford / etc.")
        self._field(scroll, "Degree", self._degree, "B.S. / M.S. / Ph.D.")
        self._field(scroll, "Field of Study", self._field_study, "Computer Science")
        self._field(scroll, "Start Date", self._start, "Sep 2018")
        self._field(scroll, "End Date", self._end, "May 2022")
        self._field(scroll, "GPA (optional)", self._gpa, "3.8")

        ctk.CTkButton(scroll, text="Save Education", fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save).pack(anchor="e", pady=12)

    def _save(self):
        if not self._institution.get():
            messagebox.showerror("Required", "Institution is required.")
            return
        execute_write(
            """INSERT INTO education (profile_id, institution, degree, field_of_study, start_date, end_date, gpa, sort_order)
               VALUES (?,?,?,?,?,?,?,?)""",
            (self.profile_id, self._institution.get(), self._degree.get(),
             self._field_study.get(), self._start.get(), self._end.get(), self._gpa.get(), 0),
        )
        if self.on_save:
            self.on_save()
        self.destroy()
