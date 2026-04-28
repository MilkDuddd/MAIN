"""Application Tracker page — manage and monitor all applications."""

import json
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from core.database import execute, execute_write

STATUS_OPTIONS = ["applied", "viewed", "phone_screen", "interview", "offer", "rejected", "withdrawn"]

STATUS_COLORS = {
    "applied":      "#1f6feb",
    "viewed":       "#8b949e",
    "phone_screen": "#d29922",
    "interview":    "#d29922",
    "offer":        "#3fb950",
    "rejected":     "#f85149",
    "withdrawn":    "#8b949e",
}


class TrackerPage(ctk.CTkFrame):
    def __init__(self, parent, colors: dict, nav_callback=None, **kwargs):
        super().__init__(parent, fg_color=colors["content_bg"], **kwargs)
        self.colors = colors
        self.nav_callback = nav_callback
        self._filter_status = "all"
        self._selected_app_id: int | None = None
        self._build()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=28, pady=(24, 8))
        ctk.CTkLabel(hdr, text="Applications", font=ctk.CTkFont(size=22, weight="bold"), text_color=self.colors["text"]).pack(side="left")
        ctk.CTkButton(
            hdr, text="↓ Export CSV", width=120, height=32,
            fg_color=self.colors["panel_bg"],
            command=self._export_csv,
        ).pack(side="right")

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color=self.colors["panel_bg"], corner_radius=8)
        filter_bar.pack(fill="x", padx=28, pady=(0, 12))
        inner = ctk.CTkFrame(filter_bar, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(inner, text="Filter:", font=ctk.CTkFont(size=12), text_color=self.colors["text_muted"]).pack(side="left", padx=(0, 8))

        self._filter_btns: dict[str, ctk.CTkButton] = {}
        for status in ["all"] + STATUS_OPTIONS:
            label = status.replace("_", " ").title()
            btn = ctk.CTkButton(
                inner, text=label, width=90, height=26, corner_radius=4,
                fg_color=self.colors["accent"] if status == "all" else self.colors["content_bg"],
                hover_color=self.colors["border"],
                text_color=self.colors["text"],
                font=ctk.CTkFont(size=11),
                command=lambda s=status: self._set_filter(s),
            )
            btn.pack(side="left", padx=3)
            self._filter_btns[status] = btn

        self._search_var = ctk.StringVar()
        self._search_var.trace("w", lambda *a: self._render_list())
        ctk.CTkEntry(inner, textvariable=self._search_var, placeholder_text="Search…", width=160, height=28, fg_color=self.colors["content_bg"], border_color=self.colors["border"]).pack(side="right")

        # Main split
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=4)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=3)
        body.rowconfigure(0, weight=1)

        # Left: app list
        left = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._count_label = ctk.CTkLabel(left, text="Applications", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"])
        self._count_label.pack(anchor="w", padx=14, pady=(12, 6))
        ctk.CTkFrame(left, height=1, fg_color=self.colors["border"]).pack(fill="x", padx=10)
        self._list_scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self._list_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Right: detail
        right = ctk.CTkFrame(body, fg_color=self.colors["panel_bg"], corner_radius=8)
        right.grid(row=0, column=1, sticky="nsew")
        self._detail = right
        self._show_empty_detail()

        self._render_list()

    def _set_filter(self, status: str):
        self._filter_status = status
        for k, btn in self._filter_btns.items():
            btn.configure(fg_color=self.colors["accent"] if k == status else self.colors["content_bg"])
        self._render_list()

    def _render_list(self):
        for w in self._list_scroll.winfo_children():
            w.destroy()

        search = self._search_var.get().lower()
        try:
            if self._filter_status == "all":
                rows = execute(
                    """SELECT a.id, a.status, a.applied_at, a.notes, j.title, j.company, j.platform
                       FROM applications a JOIN job_listings j ON a.job_id=j.id
                       ORDER BY a.applied_at DESC"""
                )
            else:
                rows = execute(
                    """SELECT a.id, a.status, a.applied_at, a.notes, j.title, j.company, j.platform
                       FROM applications a JOIN job_listings j ON a.job_id=j.id
                       WHERE a.status=? ORDER BY a.applied_at DESC""",
                    (self._filter_status,)
                )
        except Exception:
            rows = []

        if search:
            rows = [r for r in rows if search in (r["title"] or "").lower() or search in (r["company"] or "").lower()]

        self._count_label.configure(text=f"{len(rows)} Applications")

        if not rows:
            ctk.CTkLabel(self._list_scroll, text="No applications found.", font=ctk.CTkFont(size=12), text_color=self.colors["text_muted"]).pack(expand=True, pady=30)
            return

        for row in rows:
            self._app_card(row)

    def _app_card(self, row):
        color = STATUS_COLORS.get(row["status"], self.colors["text_muted"])
        card = ctk.CTkFrame(self._list_scroll, fg_color=self.colors["content_bg"], corner_radius=6, cursor="hand2")
        card.pack(fill="x", pady=3)
        card.bind("<Button-1>", lambda e, rid=row["id"]: self._load_detail(rid))

        left = ctk.CTkFrame(card, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=row["title"], font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text"], anchor="w").pack(side="left")

        ctk.CTkLabel(left, text=f"{row['company']}  ·  {row['platform']}", font=ctk.CTkFont(size=11), text_color=self.colors["text_muted"]).pack(anchor="w")
        date_str = (row["applied_at"] or "")[:10]
        ctk.CTkLabel(left, text=f"Applied: {date_str}", font=ctk.CTkFont(size=10), text_color=self.colors["text_muted"]).pack(anchor="w")

        ctk.CTkLabel(
            card,
            text=f"  {row['status'].replace('_', ' ').title()}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=color, corner_radius=4, text_color="#ffffff",
        ).pack(side="right", padx=10, pady=10)

    def _load_detail(self, app_id: int):
        self._selected_app_id = app_id
        for w in self._detail.winfo_children():
            w.destroy()

        try:
            row = execute(
                """SELECT a.*, j.title, j.company, j.platform, j.location, j.salary_text, j.description, j.apply_url
                   FROM applications a JOIN job_listings j ON a.job_id=j.id
                   WHERE a.id=?""",
                (app_id,)
            )[0]
        except Exception:
            return

        scroll = ctk.CTkScrollableFrame(self._detail, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(scroll, text=row["title"], font=ctk.CTkFont(size=17, weight="bold"), text_color=self.colors["text"], wraplength=420, justify="left").pack(anchor="w")
        ctk.CTkLabel(scroll, text=row["company"], font=ctk.CTkFont(size=13), text_color=self.colors["text_muted"]).pack(anchor="w", pady=(2, 8))

        # Status selector
        status_row = ctk.CTkFrame(scroll, fg_color="transparent")
        status_row.pack(fill="x", pady=4)
        ctk.CTkLabel(status_row, text="Status:", font=ctk.CTkFont(size=12), text_color=self.colors["text"]).pack(side="left", padx=(0, 8))
        status_var = ctk.StringVar(value=row["status"])
        ctk.CTkComboBox(
            status_row, variable=status_var,
            values=STATUS_OPTIONS,
            width=160, height=30, fg_color=self.colors["content_bg"], border_color=self.colors["border"],
            command=lambda v, aid=app_id: self._update_status(aid, v),
        ).pack(side="left")

        ctk.CTkFrame(scroll, height=1, fg_color=self.colors["border"]).pack(fill="x", pady=10)

        # Meta
        for label, value in [
            ("Platform", row["platform"]),
            ("Location", row["location"] or "—"),
            ("Salary", row["salary_text"] or "—"),
            ("Applied", (row["applied_at"] or "")[:10]),
            ("Last Updated", (row["last_updated"] or "")[:10]),
        ]:
            r = ctk.CTkFrame(scroll, fg_color="transparent")
            r.pack(fill="x", pady=2)
            ctk.CTkLabel(r, text=f"{label}:", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_muted"], width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=str(value), font=ctk.CTkFont(size=11), text_color=self.colors["text"]).pack(side="left")

        ctk.CTkFrame(scroll, height=1, fg_color=self.colors["border"]).pack(fill="x", pady=10)

        # Notes
        ctk.CTkLabel(scroll, text="Notes", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text"]).pack(anchor="w")
        notes_box = ctk.CTkTextbox(scroll, height=80, fg_color=self.colors["content_bg"], border_color=self.colors["border"], border_width=1)
        notes_box.pack(fill="x", pady=4)
        notes_box.insert("1.0", row["notes"] or "")

        # Next action
        ctk.CTkLabel(scroll, text="Next Action", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text"]).pack(anchor="w", pady=(8, 0))
        action_var = ctk.StringVar(value=row["next_action"] or "")
        ctk.CTkEntry(scroll, textvariable=action_var, placeholder_text="Follow up, prepare for interview…", fg_color=self.colors["content_bg"], border_color=self.colors["border"], height=32).pack(fill="x", pady=4)

        ctk.CTkButton(
            scroll, text="Save Notes", height=32,
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
            command=lambda: self._save_notes(app_id, notes_box.get("1.0", "end").strip(), action_var.get()),
        ).pack(anchor="e", pady=8)

        # Cover letter
        if row["cover_letter"]:
            ctk.CTkFrame(scroll, height=1, fg_color=self.colors["border"]).pack(fill="x", pady=8)
            ctk.CTkLabel(scroll, text="Cover Letter", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text"]).pack(anchor="w")
            cl_box = ctk.CTkTextbox(scroll, height=120, fg_color=self.colors["content_bg"], border_color=self.colors["border"], border_width=1)
            cl_box.pack(fill="x", pady=4)
            cl_box.insert("1.0", row["cover_letter"])

        # Delete button
        ctk.CTkButton(
            scroll, text="Delete Application", height=28, fg_color="transparent",
            text_color=self.colors["danger"], hover_color=self.colors["panel_bg"],
            command=lambda: self._delete_app(app_id),
        ).pack(anchor="e", pady=(4, 8))

    def _update_status(self, app_id: int, status: str):
        now = datetime.utcnow().isoformat()
        execute_write("UPDATE applications SET status=?, last_updated=? WHERE id=?", (status, now, app_id))
        execute_write(
            "INSERT INTO application_events (application_id, event_type, new_value, created_at) VALUES (?,?,?,?)",
            (app_id, "status_change", status, now),
        )
        self._render_list()

    def _save_notes(self, app_id: int, notes: str, next_action: str):
        now = datetime.utcnow().isoformat()
        execute_write("UPDATE applications SET notes=?, next_action=?, last_updated=? WHERE id=?", (notes, next_action, now, app_id))
        messagebox.showinfo("Saved", "Notes saved.")

    def _delete_app(self, app_id: int):
        if messagebox.askyesno("Delete", "Delete this application? This cannot be undone."):
            execute_write("DELETE FROM applications WHERE id=?", (app_id,))
            self._selected_app_id = None
            self._show_empty_detail()
            self._render_list()

    def _show_empty_detail(self):
        ctk.CTkLabel(self._detail, text="Select an application to view details", font=ctk.CTkFont(size=14), text_color=self.colors["text_muted"]).pack(expand=True)

    def _export_csv(self):
        try:
            from tkinter import filedialog
            import csv
            path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if not path:
                return
            rows = execute(
                """SELECT a.status, a.applied_at, a.notes, j.title, j.company, j.platform, j.location, j.salary_text
                   FROM applications a JOIN job_listings j ON a.job_id=j.id ORDER BY a.applied_at DESC"""
            )
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Status", "Applied At", "Title", "Company", "Platform", "Location", "Salary", "Notes"])
                for r in rows:
                    writer.writerow([r["status"], r["applied_at"][:10], r["title"], r["company"], r["platform"], r["location"] or "", r["salary_text"] or "", r["notes"] or ""])
            messagebox.showinfo("Exported", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def on_show(self):
        self._render_list()
