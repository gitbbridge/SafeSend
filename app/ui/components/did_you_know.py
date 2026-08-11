import tkinter as tk

import customtkinter as ctk

from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.theme import active_theme
from app.help.tips import did_you_know


class DidYouKnow(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget) -> None:
        self.theme = active_theme()
        super().__init__(
            parent,
            fg_color=self.theme.palette.surface,
            corner_radius=4,
            border_width=1,
            border_color=self.theme.palette.border_soft,
        )
        self.index = 0
        ctk_label(self, self.theme, "Did You Know", role="panel_title", variant="card").pack(
            anchor="w",
            padx=self.theme.spacing.card_padding,
            pady=(self.theme.spacing.card_padding, 0),
        )
        self.label = ctk_label(
            self,
            self.theme,
            "",
            role="caption",
            variant="card",
            wraplength=780,
            justify="left",
            text_color=self.theme.palette.text_muted,
        )
        self.label.pack(anchor="w", padx=self.theme.spacing.card_padding, pady=(self.theme.spacing.sm, 0))
        ctk_button(self, self.theme, "Next Tip", command=self.next_tip, icon="redo", width=116).pack(
            anchor="e",
            padx=self.theme.spacing.card_padding,
            pady=(self.theme.spacing.sm, self.theme.spacing.card_padding),
        )
        self.next_tip()

    def next_tip(self) -> None:
        self.label.configure(text=did_you_know(self.index))
        self.index += 1
