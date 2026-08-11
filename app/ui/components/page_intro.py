import tkinter as tk

import customtkinter as ctk

from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.theme import active_theme
from app.help.page_intros import get_page_intro
from app.help.preferences import learning_mode_enabled


class PageIntro(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, page: str) -> None:
        theme = active_theme()
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        self.columnconfigure(0, weight=1)
        text = get_page_intro(page) if learning_mode_enabled() else ""
        self.label = ctk_label(
            self,
            theme,
            text,
            role="caption",
            variant="background",
            wraplength=980,
            justify="left",
            text_color=theme.palette.text_muted,
        )
        self.label.grid(row=0, column=0, sticky="ew", pady=(0, theme.spacing.md))
