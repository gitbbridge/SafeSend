import tkinter as tk

import customtkinter as ctk

from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.theme import active_theme
from app.help.recommendations import Recommendation


class RecommendationCard(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, recommendation: Recommendation) -> None:
        theme = active_theme()
        super().__init__(
            parent,
            fg_color=theme.palette.surface,
            corner_radius=4,
            border_width=1,
            border_color=theme.palette.border_soft,
        )
        self.columnconfigure(0, weight=1)
        ctk_label(self, theme, recommendation.label, role="panel_title", variant="card").grid(
            row=0,
            column=0,
            sticky="w",
            padx=theme.spacing.card_padding,
            pady=(theme.spacing.card_padding, 0),
        )
        ctk_label(
            self,
            theme,
            f"Default: {recommendation.recommended_default}   Range: {recommendation.recommended_range}",
            role="caption",
            variant="card",
            text_color=theme.palette.text_muted,
        ).grid(row=1, column=0, sticky="w", padx=theme.spacing.card_padding, pady=(theme.spacing.xs, theme.spacing.sm))
        body = "\n".join(
            [
                recommendation.description,
                f"Why it matters: {recommendation.why_it_matters}",
                f"Best practice: {recommendation.best_practice}",
                f"Risks: {recommendation.risks}",
            ]
        )
        ctk_label(
            self,
            theme,
            body,
            role="caption",
            variant="card",
            wraplength=760,
            justify="left",
            text_color=theme.palette.text_muted,
        ).grid(row=2, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
