"""Alert toast notification system for Intel Platform GUI."""
import threading
import time
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from gui.app_window import IntelPlatformApp

COLORS = {
    "sidebar_bg": "#0d1117",
    "content_bg": "#161b22",
    "accent":     "#1f6feb",
    "text":       "#c9d1d9",
    "text_muted": "#8b949e",
    "danger":     "#f85149",
    "warning":    "#d29922",
    "panel_bg":   "#21262d",
}

_SEV_COLORS = {
    "critical": "#f85149",
    "warning":  "#d29922",
    "info":     "#1f6feb",
}

_SEV_ICONS = {
    "critical": "✕",
    "warning":  "⚠",
    "info":     "ℹ",
}


class ToastNotification(ctk.CTkToplevel):
    """Single toast overlay notification window."""

    def __init__(self, parent, message: str, severity: str = "info",
                 on_dismiss=None, on_click=None):
        super().__init__(parent)
        self._dismissed = False
        self._on_dismiss = on_dismiss

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=_SEV_COLORS.get(severity, COLORS["accent"]))

        color = _SEV_COLORS.get(severity, COLORS["accent"])
        icon = _SEV_ICONS.get(severity, "ℹ")

        frame = ctk.CTkFrame(self, fg_color=color, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(frame, text=icon, font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="white", width=28).pack(side="left", padx=(10, 4), pady=10)

        msg_text = message[:70] + "…" if len(message) > 70 else message
        lbl = ctk.CTkLabel(frame, text=msg_text, font=ctk.CTkFont(size=12),
                           text_color="white", anchor="w", wraplength=240)
        lbl.pack(side="left", fill="x", expand=True, padx=4)
        if on_click:
            lbl.bind("<Button-1>", lambda e: on_click())

        ctk.CTkButton(frame, text="×", width=28, height=28,
                      fg_color="transparent", hover_color="#ffffff22",
                      text_color="white", font=ctk.CTkFont(size=14),
                      command=self.dismiss).pack(side="right", padx=6)

        # Auto-dismiss after 6 seconds
        self.after(6000, self.dismiss)

    def position(self, x: int, y: int):
        self.geometry(f"340x64+{x}+{y}")

    def dismiss(self):
        if self._dismissed:
            return
        self._dismissed = True
        try:
            self.destroy()
        except Exception:
            pass
        if self._on_dismiss:
            self._on_dismiss(self)


class ToastManager:
    """
    Manages a stack of toast notifications.
    Polls for new alerts every 15s in a background thread.
    """

    POLL_INTERVAL = 15  # seconds

    def __init__(self, app: "IntelPlatformApp"):
        self._app = app
        self._active_toasts: list[ToastNotification] = []
        self._seen_alert_ids: set[str] = set()
        self._running = False

    def start_polling(self):
        if self._running:
            return
        self._running = True
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def _poll_loop(self):
        # Short initial delay
        time.sleep(10)
        while self._running:
            try:
                self._check_alerts()
            except Exception:
                pass
            time.sleep(self.POLL_INTERVAL)

    def _check_alerts(self):
        try:
            from modules.feed.alert_engine import get_active_alerts
            alerts = get_active_alerts(limit=5)
            for alert in alerts:
                aid = getattr(alert, "alert_id", None) or str(getattr(alert, "id", ""))
                if aid and aid not in self._seen_alert_ids:
                    self._seen_alert_ids.add(aid)
                    sev = getattr(alert, "severity", "info")
                    msg = getattr(alert, "message", "New alert")
                    self._app.after(0, lambda m=msg, s=sev: self._show_toast(m, s))
        except Exception:
            pass

    def _show_toast(self, message: str, severity: str = "info"):
        # Clean up dismissed toasts
        self._active_toasts = [t for t in self._active_toasts if not t._dismissed]

        # Calculate position (top-right, stacked)
        try:
            app_x = self._app.winfo_x()
            app_y = self._app.winfo_y()
            app_w = self._app.winfo_width()
        except Exception:
            app_x, app_y, app_w = 0, 0, 1400

        x = app_x + app_w - 360
        y = app_y + 40 + len(self._active_toasts) * 80

        def on_dismiss(toast):
            if toast in self._active_toasts:
                self._active_toasts.remove(toast)
            self._restack()

        def on_click():
            # Navigate to Feed page
            try:
                self._app._navigate("feed")
            except Exception:
                pass

        toast = ToastNotification(self._app, message, severity,
                                   on_dismiss=on_dismiss, on_click=on_click)
        toast.position(x, y)
        self._active_toasts.append(toast)

    def _restack(self):
        """Reposition remaining toasts after one is dismissed."""
        try:
            app_x = self._app.winfo_x()
            app_y = self._app.winfo_y()
            app_w = self._app.winfo_width()
            x = app_x + app_w - 360
            for i, toast in enumerate(self._active_toasts):
                if not toast._dismissed:
                    y = app_y + 40 + i * 80
                    toast.geometry(f"340x64+{x}+{y}")
        except Exception:
            pass
