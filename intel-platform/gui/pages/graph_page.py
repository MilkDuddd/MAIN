"""Relationship Graph page — NetworkX + matplotlib embedded in CustomTkinter."""
import threading

import customtkinter as ctk

from gui.pages.base_page import BasePage, COLORS


class GraphPage(BasePage):
    PAGE_TITLE = "Relationship Graph"
    PAGE_SUBTITLE = "   Entity Network Visualization"

    def build_page(self):
        self.left_panel.pack_forget()
        self.right_panel.pack_forget()

        # Controls bar
        ctrl = ctk.CTkFrame(self.main_frame, fg_color=COLORS["panel_bg"], corner_radius=8)
        ctrl.pack(fill="x", pady=(0, 8))

        # Entity search
        ctk.CTkLabel(ctrl, text="Entity:", text_color=COLORS["text_muted"],
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(12, 4), pady=8)
        self.entity_entry = ctk.CTkEntry(ctrl, placeholder_text="Search entity…",
                                          fg_color=COLORS["input_bg"], text_color=COLORS["text"],
                                          width=200)
        self.entity_entry.pack(side="left", padx=4, pady=8)

        ctk.CTkButton(ctrl, text="Center", width=70, height=28, fg_color=COLORS["accent"],
                      command=self._center_entity).pack(side="left", padx=4, pady=8)

        # Depth slider
        ctk.CTkLabel(ctrl, text="Depth:", text_color=COLORS["text_muted"],
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(16, 4))
        self.depth_var = ctk.IntVar(value=2)
        depth_slider = ctk.CTkSlider(ctrl, from_=1, to=3, number_of_steps=2,
                                      variable=self.depth_var, width=80)
        depth_slider.pack(side="left", padx=4)
        self.depth_label = ctk.CTkLabel(ctrl, text="2", text_color=COLORS["text"],
                                         font=ctk.CTkFont(size=12), width=20)
        self.depth_label.pack(side="left")
        depth_slider.configure(command=lambda v: self.depth_label.configure(text=str(int(v))))

        # Layout dropdown
        ctk.CTkLabel(ctrl, text="Layout:", text_color=COLORS["text_muted"],
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(16, 4))
        self.layout_var = ctk.StringVar(value="spring")
        ctk.CTkOptionMenu(ctrl, values=["spring", "circular", "shell", "spectral"],
                           variable=self.layout_var, width=100,
                           fg_color=COLORS["panel_bg"], button_color=COLORS["accent"],
                           text_color=COLORS["text"]).pack(side="left", padx=4)

        ctk.CTkButton(ctrl, text="Refresh", width=80, height=28, fg_color=COLORS["accent"],
                      command=self._refresh_graph).pack(side="right", padx=12)
        ctk.CTkButton(ctrl, text="Export PNG", width=90, height=28, fg_color="#27ae60",
                      command=self._export_png).pack(side="right", padx=4)

        # Graph canvas container
        self.canvas_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["input_bg"], corner_radius=8)
        self.canvas_frame.pack(fill="both", expand=True)

        # Info bar
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text="Click 'Refresh' to load the entity relationship graph  |  Nodes: —  |  Edges: —",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        self.info_label.pack(pady=(4, 0))

        self._canvas_widget = None
        self._figure = None
        self._graph_data = None

        # Load graph after a short delay
        self.after(1000, self._refresh_graph)

    def _refresh_graph(self):
        threading.Thread(target=self._load_graph, daemon=True).start()

    def _center_entity(self):
        entity = self.entity_entry.get().strip()
        if not entity:
            return
        threading.Thread(target=lambda: self._load_graph(focus=entity), daemon=True).start()

    def _load_graph(self, focus: str = None):
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
            import networkx as nx
            from modules.correlation.graph_builder import build_graph, get_networkx_graph

            depth = self.depth_var.get()
            if focus:
                G = build_graph([focus], depth=depth)
            else:
                G = get_networkx_graph()

            if G is None or len(G.nodes) == 0:
                self.after(0, lambda: self.info_label.configure(
                    text="No entities in graph yet. Run 'intel correlate <name>' to add entities."))
                return

            self.after(0, lambda: self._render_graph(G))
        except ImportError as e:
            self.after(0, lambda: self.info_label.configure(text=f"Missing dependency: {e}"))
        except Exception as e:
            self.after(0, lambda: self.info_label.configure(text=f"Graph error: {e}"))

    def _render_graph(self, G):
        try:
            import matplotlib
            matplotlib.use("TkAgg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
            import networkx as nx

            # Clear previous
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
            if self._figure:
                plt.close(self._figure)

            fig, ax = plt.subplots(figsize=(12, 7))
            fig.patch.set_facecolor("#161b22")
            ax.set_facecolor("#161b22")

            layout_fn = {
                "spring":   nx.spring_layout,
                "circular": nx.circular_layout,
                "shell":    nx.shell_layout,
                "spectral": nx.spectral_layout,
            }.get(self.layout_var.get(), nx.spring_layout)

            try:
                pos = layout_fn(G, seed=42)
            except Exception:
                pos = nx.spring_layout(G, seed=42)

            NODE_COLORS = {
                "person":       "#1f6feb",
                "organization": "#3fb950",
                "location":     "#f39c12",
                "vessel":       "#9b59b6",
                "aircraft":     "#e74c3c",
                "unknown":      "#8b949e",
            }

            node_colors = [NODE_COLORS.get(G.nodes[n].get("entity_type", "unknown"), "#8b949e")
                           for n in G.nodes]
            node_labels = {n: G.nodes[n].get("label", str(n))[:20] for n in G.nodes}

            nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                                   node_size=400, alpha=0.9)
            nx.draw_networkx_labels(G, pos, labels=node_labels, ax=ax,
                                    font_size=8, font_color="#c9d1d9")
            nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#30363d",
                                   arrows=True, arrowsize=10, alpha=0.7,
                                   width=1.2)

            ax.axis("off")
            fig.tight_layout(pad=0.5)

            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

            toolbar_frame = ctk.CTkFrame(self.canvas_frame, fg_color=COLORS["panel_bg"])
            toolbar_frame.pack(fill="x")
            NavigationToolbar2Tk(canvas, toolbar_frame)

            self._figure = fig
            self._canvas_widget = canvas
            self._graph_data = G

            self.info_label.configure(
                text=f"Nodes: {len(G.nodes)}  |  Edges: {len(G.edges)}  |  "
                     "Use toolbar to zoom/pan  |  Blue=Person  Green=Org  Orange=Location  Purple=Vessel"
            )
        except Exception as e:
            self.info_label.configure(text=f"Render error: {e}")

    def _export_png(self):
        if not self._figure:
            return
        try:
            from core import settings as cfg
            from pathlib import Path
            from datetime import datetime, timezone
            out_dir = cfg.output_dir()
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            path = out_dir / f"intel_graph_{ts}.png"
            self._figure.savefig(str(path), dpi=150, bbox_inches="tight",
                                  facecolor="#161b22")
            self.info_label.configure(text=f"Graph exported: {path}")
        except Exception as e:
            self.info_label.configure(text=f"Export error: {e}")
