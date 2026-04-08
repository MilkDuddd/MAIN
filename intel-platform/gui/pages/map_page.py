"""Intelligence Map page — tkintermapview with colored layer pins."""
import threading

import customtkinter as ctk

from gui.pages.base_page import BasePage, COLORS


class MapPage(BasePage):
    PAGE_TITLE = "Intelligence Map"
    PAGE_SUBTITLE = "   Live geo-intelligence visualization"

    def build_page(self):
        self.left_panel.pack_forget()
        self.right_panel.pack_forget()

        # Controls bar
        ctrl = ctk.CTkFrame(self.main_frame, fg_color=COLORS["panel_bg"], corner_radius=8)
        ctrl.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(ctrl, text="Layers:", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=(12, 8), pady=8)

        self.layer_vars = {}
        layers = [
            ("Flights",   "flights",   "#1f6feb"),
            ("Vessels",   "vessels",   "#1abc9c"),
            ("Conflicts", "conflicts", "#e74c3c"),
            ("UAP",       "uap",       "#9b59b6"),
        ]
        for label, key, color in layers:
            var = ctk.BooleanVar(value=True)
            self.layer_vars[key] = var
            ctk.CTkCheckBox(ctrl, text=label, variable=var,
                            fg_color=color, hover_color=color,
                            text_color=COLORS["text"],
                            command=self._refresh_pins).pack(side="left", padx=8, pady=8)

        ctk.CTkButton(ctrl, text="Refresh Pins", width=100, height=28, fg_color=COLORS["accent"],
                      command=self._refresh_pins).pack(side="right", padx=12, pady=8)

        # Map container
        self.map_container = ctk.CTkFrame(self.main_frame, fg_color=COLORS["input_bg"], corner_radius=8)
        self.map_container.pack(fill="both", expand=True)

        # Status label
        self.status_lbl = ctk.CTkLabel(
            self.main_frame,
            text="Loading map…",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self.status_lbl.pack(pady=(4, 0))

        self._map_widget = None
        self._markers: list = []
        self.after(500, self._init_map)

    def _init_map(self):
        try:
            import tkintermapview
            self._map_widget = tkintermapview.TkinterMapView(
                self.map_container,
                width=900,
                height=600,
                corner_radius=8,
            )
            self._map_widget.pack(fill="both", expand=True)
            self._map_widget.set_position(20, 0)  # Center on world
            self._map_widget.set_zoom(2)
            self.status_lbl.configure(text="Map loaded. Click 'Refresh Pins' to plot intelligence data.")
            self._refresh_pins()
        except ImportError:
            self.status_lbl.configure(
                text="tkintermapview not installed. Run: pip install tkintermapview")
        except Exception as e:
            self.status_lbl.configure(text=f"Map error: {e}")

    def _refresh_pins(self):
        if not self._map_widget:
            return
        threading.Thread(target=self._load_and_plot, daemon=True).start()

    def _load_and_plot(self):
        try:
            from core import database
            all_markers = []

            if self.layer_vars.get("flights", ctk.BooleanVar(value=True)).get():
                rows = database.execute(
                    "SELECT callsign, latitude, longitude, icao24 FROM flight_tracks "
                    "WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY collected_at DESC LIMIT 500"
                )
                for r in rows:
                    if r["latitude"] and r["longitude"]:
                        all_markers.append({
                            "lat": r["latitude"], "lon": r["longitude"],
                            "label": f"Flight: {r['callsign'] or r['icao24']}",
                            "color": "#1f6feb", "layer": "flights",
                        })

            if self.layer_vars.get("vessels", ctk.BooleanVar(value=True)).get():
                rows = database.execute(
                    "SELECT name, mmsi, latitude, longitude FROM vessel_tracks "
                    "WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY collected_at DESC LIMIT 500"
                )
                for r in rows:
                    if r["latitude"] and r["longitude"]:
                        all_markers.append({
                            "lat": r["latitude"], "lon": r["longitude"],
                            "label": f"Vessel: {r['name'] or r['mmsi']}",
                            "color": "#1abc9c", "layer": "vessels",
                        })

            if self.layer_vars.get("conflicts", ctk.BooleanVar(value=True)).get():
                rows = database.execute(
                    "SELECT location, latitude, longitude, event_type, country FROM conflict_events "
                    "WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY event_date DESC LIMIT 500"
                )
                for r in rows:
                    if r["latitude"] and r["longitude"]:
                        all_markers.append({
                            "lat": r["latitude"], "lon": r["longitude"],
                            "label": f"Conflict: {r['event_type']} — {r['country']}",
                            "color": "#e74c3c", "layer": "conflicts",
                        })

            if self.layer_vars.get("uap", ctk.BooleanVar(value=True)).get():
                rows = database.execute(
                    "SELECT city, state, lat, lon, shape FROM uap_sightings "
                    "WHERE lat IS NOT NULL AND lon IS NOT NULL ORDER BY occurred_date DESC LIMIT 500"
                )
                for r in rows:
                    if r["lat"] and r["lon"]:
                        all_markers.append({
                            "lat": r["lat"], "lon": r["lon"],
                            "label": f"UAP: {r['shape'] or '?'} — {r['city']}, {r['state']}",
                            "color": "#9b59b6", "layer": "uap",
                        })

            self.after(0, lambda m=all_markers: self._plot_markers(m))
        except Exception as e:
            self.after(0, lambda: self.status_lbl.configure(text=f"Data error: {e}"))

    def _plot_markers(self, markers: list):
        if not self._map_widget:
            return
        # Clear existing
        for m in self._markers:
            try:
                m.delete()
            except Exception:
                pass
        self._markers = []

        for m in markers:
            try:
                marker = self._map_widget.set_marker(
                    m["lat"], m["lon"],
                    text=m["label"],
                    marker_color_circle=m["color"],
                    marker_color_outside=m["color"],
                    command=lambda event, lbl=m["label"]: self._show_detail(lbl),
                )
                self._markers.append(marker)
            except Exception:
                pass

        flights = sum(1 for m in markers if m["layer"] == "flights")
        vessels = sum(1 for m in markers if m["layer"] == "vessels")
        conflicts = sum(1 for m in markers if m["layer"] == "conflicts")
        uap = sum(1 for m in markers if m["layer"] == "uap")
        self.status_lbl.configure(
            text=f"Pins: {len(markers)} total  |  "
                 f"Flights: {flights}  Vessels: {vessels}  Conflicts: {conflicts}  UAP: {uap}"
        )

    def _show_detail(self, label: str):
        try:
            popup = ctk.CTkToplevel(self)
            popup.title("Intel Pin Detail")
            popup.geometry("400x200")
            popup.configure(fg_color=COLORS["panel_bg"])
            ctk.CTkLabel(popup, text=label, font=ctk.CTkFont(size=13),
                         text_color=COLORS["text"], wraplength=360).pack(pady=30, padx=20)
            ctk.CTkButton(popup, text="Close", command=popup.destroy,
                          fg_color=COLORS["accent"]).pack()
        except Exception:
            pass
