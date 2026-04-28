"""Cover Letter page — AI-powered cover letter generation and management."""

import threading
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from core.database import execute, execute_write
from core.settings import get as get_setting


class CoverLetterPage(ctk.CTkFrame):
    def __init__(self, parent, colors: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=colors["content_bg"], **kwargs)
        self.colors = colors
        self.nav_callback = nav_callback
        self._current_cl_id: int | None = None
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkLabel(hdr, text="Cover Letters", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.colors["text"]).pack(side="left")
        ctk.CTkButton(
            hdr, text="+ New", width=80, height=32,
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
            command=self._new_cover_letter,
        ).pack(side="right")

        # Main split
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=8)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # Left: cover letter list
        left = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(left, text="Saved Letters", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", padx=14, pady=(12, 6))
        ctk.CTkFrame(left, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=10)
        self._cl_list = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._cl_list.pack(fill="both", expand=True, padx=4, pady=4)

        # Right: editor + AI panel
        right = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew")

        # AI generation controls
        ai_panel = ctk.CTkFrame(right, fg_color=self.colors["content_bg"], corner_radius=6)
        ai_panel.pack(fill="x", padx=12, pady=(12, 6))

        ai_top = ctk.CTkFrame(ai_panel, fg_color="transparent")
        ai_top.pack(fill="x", padx=12, pady=(10, 6))
        ctk.CTkLabel(ai_top, text="AI Cover Letter Generator", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"]).pack(side="left")
        ai_badge = ctk.CTkLabel(ai_top, text=" Claude AI ", font=ctk.CTkFont(size=10), fg_color=self.colors["tag_bg"], corner_radius=4, text_color="#ffffff")
        ai_badge.pack(side="left", padx=8)

        ai_fields = ctk.CTkFrame(ai_panel, fg_color="transparent")
        ai_fields.pack(fill="x", padx=12, pady=(0, 10))
        ai_fields.columnconfigure(0, weight=1)
        ai_fields.columnconfigure(1, weight=1)

        self._ai_role = ctk.StringVar()
        self._ai_company = ctk.StringVar()
        self._ai_tone = ctk.StringVar(value="Professional")
        self._ai_length = ctk.StringVar(value="Medium (3 paragraphs)")

        def ai_field(parent, row, col, label, var, ph=""):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=col, sticky="ew", padx=4, pady=3)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w")
            ctk.CTkEntry(f, textvariable=var, placeholder_text=ph, fg_color=self.colors["panel_bg"], border_color=self.colors["border"], height=32).pack(fill="x")

        ai_field(ai_fields, 0, 0, "Role / Job Title", self._ai_role, "Software Engineer")
        ai_field(ai_fields, 0, 1, "Company Name", self._ai_company, "Google")

        f_tone = ctk.CTkFrame(ai_fields, fg_color="transparent")
        f_tone.grid(row=1, column=0, sticky="ew", padx=4, pady=3)
        ctk.CTkLabel(f_tone, text="Tone", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w")
        ctk.CTkComboBox(f_tone, variable=self._ai_tone, values=["Professional", "Enthusiastic", "Concise", "Creative", "Formal"], fg_color=self.colors["panel_bg"], border_color=self.colors["border"], height=32).pack(fill="x")

        f_len = ctk.CTkFrame(ai_fields, fg_color="transparent")
        f_len.grid(row=1, column=1, sticky="ew", padx=4, pady=3)
        ctk.CTkLabel(f_len, text="Length", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w")
        ctk.CTkComboBox(f_len, variable=self._ai_length, values=["Short (1 paragraph)", "Medium (3 paragraphs)", "Long (5 paragraphs)"], fg_color=self.colors["panel_bg"], border_color=self.colors["border"], height=32).pack(fill="x")

        self._jd_box = ctk.CTkTextbox(ai_panel, height=60, fg_color=self.colors["panel_bg"], border_color=self.colors["border"], border_width=1)
        self._jd_box.pack(fill="x", padx=12, pady=(0, 8))
        self._jd_box.insert("1.0", "Paste key job requirements or the full job description here…")

        self._gen_btn = ctk.CTkButton(
            ai_panel, text="✨ Generate with AI", height=34,
            fg_color=self.colors["tag_bg"], hover_color="#388bfd",
            command=self._generate_ai,
        )
        self._gen_btn.pack(anchor="e", padx=12, pady=(0, 10))

        # Editor
        editor_hdr = ctk.CTkFrame(right, fg_color="transparent")
        editor_hdr.pack(fill="x", padx=12, pady=(4, 2))
        self._title_var = ctk.StringVar(value="Untitled Cover Letter")
        ctk.CTkEntry(editor_hdr, textvariable=self._title_var, fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=32, font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(editor_hdr, text="Save", width=70, height=32, fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"], command=self._save_cl).pack(side="right")

        self._editor = ctk.CTkTextbox(right, fg_color=self.colors["content_bg"], border_color=self.colors["border"], border_width=1, font=ctk.CTkFont(size=13))
        self._editor.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self._load_cl_list()

    def _load_cl_list(self):
        for w in self._cl_list.winfo_children():
            w.destroy()
        pid = get_setting("default_profile_id")
        if not pid:
            return
        rows = execute("SELECT * FROM cover_letters WHERE profile_id=? ORDER BY updated_at DESC", (pid,))
        for row in rows:
            btn = ctk.CTkButton(
                self._cl_list,
                text=f"{row['title']}\n{'AI' if row['ai_generated'] else 'Manual'}  ·  {(row['updated_at'] or '')[:10]}",
                anchor="w", height=52, corner_radius=6,
                fg_color=self.colors["content_bg"], hover_color=self.colors["border"],
                text_color=self.colors["text"], font=ctk.CTkFont(size=11),
                command=lambda rid=row["id"]: self._load_cl(rid),
            )
            btn.pack(fill="x", pady=2)

    def _load_cl(self, cl_id: int):
        self._current_cl_id = cl_id
        row = execute("SELECT * FROM cover_letters WHERE id=?", (cl_id,))[0]
        self._title_var.set(row["title"])
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", row["content"])

    def _new_cover_letter(self):
        self._current_cl_id = None
        self._title_var.set("Untitled Cover Letter")
        self._editor.delete("1.0", "end")

    def _save_cl(self):
        pid = get_setting("default_profile_id")
        if not pid:
            messagebox.showwarning("No Profile", "Set up a profile first.")
            return
        title = self._title_var.get().strip() or "Untitled"
        content = self._editor.get("1.0", "end").strip()
        now = datetime.utcnow().isoformat()

        if self._current_cl_id:
            execute_write("UPDATE cover_letters SET title=?, content=?, updated_at=? WHERE id=?", (title, content, now, self._current_cl_id))
        else:
            self._current_cl_id = execute_write(
                "INSERT INTO cover_letters (profile_id, title, content, ai_generated, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (pid, title, content, 0, now, now),
            )
        self._load_cl_list()
        messagebox.showinfo("Saved", "Cover letter saved.")

    def _generate_ai(self):
        api_key = get_setting("anthropic_api_key")
        if not api_key:
            messagebox.showwarning("API Key Required", "Add your Anthropic API key in Settings to use AI generation.")
            if self.nav_callback:
                self.nav_callback("settings")
            return

        pid = get_setting("default_profile_id")
        if not pid:
            messagebox.showwarning("No Profile", "Set up a profile first.")
            return

        role = self._ai_role.get().strip()
        company = self._ai_company.get().strip()
        if not role or not company:
            messagebox.showwarning("Required", "Enter a role and company name.")
            return

        self._gen_btn.configure(state="disabled", text="Generating…")

        def _worker():
            try:
                from modules.ai.cover_letter import generate_cover_letter
                profile = execute("SELECT * FROM profiles WHERE id=?", (pid,))[0]
                jd_text = self._jd_box.get("1.0", "end").strip()
                content = generate_cover_letter(
                    api_key=api_key,
                    profile=dict(profile),
                    role=role,
                    company=company,
                    tone=self._ai_tone.get(),
                    length=self._ai_length.get(),
                    job_description=jd_text,
                )
                self.after(0, self._on_ai_done, content, role, company)
            except Exception as e:
                self.after(0, self._on_ai_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_ai_done(self, content: str, role: str, company: str):
        self._gen_btn.configure(state="normal", text="✨ Generate with AI")
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", content)
        self._title_var.set(f"Cover Letter — {role} at {company}")
        # Auto-save
        pid = get_setting("default_profile_id")
        now = datetime.utcnow().isoformat()
        cl_id = execute_write(
            "INSERT INTO cover_letters (profile_id, title, content, ai_generated, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (pid, self._title_var.get(), content, 1, now, now),
        )
        self._current_cl_id = cl_id
        self._load_cl_list()

    def _on_ai_error(self, msg: str):
        self._gen_btn.configure(state="normal", text="✨ Generate with AI")
        messagebox.showerror("Generation Failed", f"AI error:\n{msg}")

    def on_show(self):
        self._load_cl_list()
