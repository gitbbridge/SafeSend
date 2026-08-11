import tkinter as tk

import customtkinter as ctk

from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.theme import active_theme


class WarningBanner(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget) -> None:
        theme = active_theme()
        super().__init__(
            parent,
            fg_color=theme.palette.surface,
            corner_radius=12,
            border_width=1,
            border_color=theme.palette.warning,
        )
        self.theme = theme
        self.columnconfigure(0, weight=1)
        self.label = ctk_label(self, theme, "", role="caption", variant="panel", wraplength=900, justify="left", text_color=theme.palette.orange)
        self.label.grid(row=0, column=0, sticky="ew", padx=theme.spacing.md, pady=theme.spacing.md)
        self.grid_remove()

    def show_warnings(self, warnings: list[str]) -> None:
        if warnings:
            self.label.configure(text="\n".join(warnings))
            self.grid()
        else:
            self.grid_remove()
