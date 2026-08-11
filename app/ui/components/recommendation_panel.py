import tkinter as tk

import customtkinter as ctk

from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.typography import font
from app.help.recommendations import get_recommendation, recommendations_for_page
from app.help.tips import did_you_know
from app.design_system.theme import active_theme

_ACTIVE_PANELS = []


def register_panel(panel) -> None:
    _ACTIVE_PANELS.append(panel)


def set_active_recommendation(setting_key: str) -> None:
    for panel in list(_ACTIVE_PANELS):
        try:
            panel.show_recommendation(setting_key)
        except tk.TclError:
            _ACTIVE_PANELS.remove(panel)


class RecommendationPanel(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, page: str) -> None:
        self.theme = active_theme()
        self.page = page
        self.expanded = tk.BooleanVar(value=True)
        super().__init__(
            parent,
            fg_color=self.theme.palette.surface,
            corner_radius=4,
            border_width=1,
            border_color=self.theme.palette.border_soft,
        )
        self.columnconfigure(0, weight=1)

        self.header = tk.Canvas(self, height=52, highlightthickness=0, bd=0, cursor="hand2")
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.bind("<Configure>", self._draw_header)
        self.header.bind("<Button-1>", self._header_click)

        self.body = ctk_frame(self, self.theme, "card", corner_radius=0, border_width=0)
        self.body.grid(row=1, column=0, sticky="ew")
        self.body.columnconfigure(0, weight=1)

        self.content_area = ctk_frame(self.body, self.theme, "card", corner_radius=0, border_width=0)
        self.content_area.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.content_area.columnconfigure(0, weight=1)
        self.heading = ctk_label(self.content_area, self.theme, "", role="panel_title", variant="card")
        self.heading.grid(row=0, column=0, sticky="w", padx=28, pady=(24, 8))
        self.content = ctk_label(
            self.content_area,
            self.theme,
            "",
            role="body",
            variant="card",
            wraplength=1060,
            justify="left",
            text_color=self.theme.palette.text,
            anchor="w",
            font=font(self.theme, "body", scale=1.15),
        )
        self.content.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 24))

        self.footer = ctk_frame(self.body, self.theme, "surface", fg_color=self.theme.palette.surface_alt, corner_radius=0, border_width=0)
        self.footer.grid(row=1, column=0, sticky="ew")
        self.footer.configure(height=44)
        self.footer.pack_propagate(False)
        self.tip = ctk_label(
            self.footer,
            self.theme,
            "",
            role="body",
            variant="surface",
            wraplength=1040,
            justify="left",
            text_color=self.theme.palette.text_muted,
            fg_color=self.theme.palette.surface_alt,
            anchor="w",
            font=font(self.theme, "body", scale=1.1),
        )
        self.tip.pack(anchor="w", padx=28, pady=10)

        self.tip_index = 0
        self.show_page_defaults()
        register_panel(self)

    def toggle(self) -> None:
        self.expanded.set(not self.expanded.get())
        if self.expanded.get():
            self.body.grid()
        else:
            self.body.grid_remove()
        self._draw_header()

    def show_page_defaults(self) -> None:
        recs = recommendations_for_page(self.page)
        self.heading.configure(text=f"{self.page} guidance")
        lines = [f"{rec.label}: {rec.best_practice}" for rec in recs]
        self.content.configure(text="  |  ".join(lines) if lines else "Review recommended settings before making changes.")
        self.tip.configure(text=f"Did you know: {did_you_know(self.tip_index)}")

    def show_recommendation(self, setting_key: str) -> None:
        rec = get_recommendation(setting_key)
        self.heading.configure(text=rec.label)
        text = "  |  ".join(
            [
                f"Recommended default: {rec.recommended_default}",
                f"Recommended range: {rec.recommended_range}",
                rec.description,
                f"Why it matters: {rec.why_it_matters}",
                f"Best practice: {rec.best_practice}",
                f"Risks: {rec.risks}",
            ]
        )
        self.content.configure(text=text)
        if not self.expanded.get():
            self.toggle()

    def _header_click(self, event) -> None:
        if event.x >= max(self.header.winfo_width() - 72, 0):
            self.toggle()

    def _draw_header(self, _event=None) -> None:
        width = max(self.header.winfo_width(), 1)
        height = max(self.header.winfo_height(), 52)
        self.header.delete("all")
        left = self.theme.palette.info
        right = self.theme.palette.success
        for x in range(width):
            ratio = x / max(width - 1, 1)
            self.header.create_line(x, 0, x, height, fill=_blend(left, right, ratio))
        self.header.create_text(
            28,
            height / 2,
            text="Guided Configuration",
            anchor="w",
            fill=self.theme.palette.sidebar_text,
            font=(self.theme.typography.family_semibold, 15),
        )
        self.header.create_text(
            width - 32,
            height / 2,
            text="x" if self.expanded.get() else "+",
            anchor="center",
            fill=self.theme.palette.sidebar_text,
            font=(self.theme.typography.family, 22),
        )


def _blend(start: str, end: str, ratio: float) -> str:
    sr, sg, sb = _hex_to_rgb(start)
    er, eg, eb = _hex_to_rgb(end)
    return f"#{int(sr + (er - sr) * ratio):02x}{int(sg + (eg - sg) * ratio):02x}{int(sb + (eb - sb) * ratio):02x}"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
