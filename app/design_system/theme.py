import os
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

from app.design_system.buttons import configure_button_styles
from app.design_system.cards import configure_card_styles
from app.design_system.colors import NEW_SKIN_COLORS, ORIGINAL_SKIN_COLORS, Palette
from app.design_system.forms import configure_form_styles
from app.design_system.sidebar import configure_sidebar_styles
from app.design_system.spacing import Spacing
from app.design_system.status_badges import configure_status_badge_styles
from app.design_system.tables import configure_table_styles
from app.design_system.toolbar import configure_toolbar_styles
from app.design_system.typography import Typography


@dataclass(frozen=True)
class SafeSendTheme:
    name: str
    palette: Palette
    typography: Typography
    spacing: Spacing


NEW_SKIN = SafeSendTheme(
    name="HubSpot Design System",
    palette=NEW_SKIN_COLORS,
    typography=Typography(),
    spacing=Spacing(),
)

ORIGINAL_SKIN = SafeSendTheme(
    name="Original Skin",
    palette=ORIGINAL_SKIN_COLORS,
    typography=Typography(title=24, page_title=26, panel_title=14, metric=24, metric_large=32),
    spacing=Spacing(sidebar_width=230, card_padding=12, page_padding=18, page_margin=18),
)


def active_theme() -> SafeSendTheme:
    skin = os.environ.get("SAFESEND_SKIN", "hubspot").strip().lower()
    if skin in {"original", "original skin"}:
        return ORIGINAL_SKIN
    return NEW_SKIN


def apply_theme(root: tk.Tk, theme: SafeSendTheme | None = None) -> SafeSendTheme:
    theme = theme or active_theme()
    palette = theme.palette
    typo = theme.typography
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    try:
        root.configure(fg_color=palette.background)
    except tk.TclError:
        root.configure(bg=palette.background)
    style.configure(".", font=(typo.family, typo.body), background=palette.background, foreground=palette.text)
    style.configure("TFrame", background=palette.background)
    style.configure("Content.TFrame", background=palette.background)
    style.configure("Title.TLabel", font=(typo.family_semibold, typo.page_title), background=palette.background, foreground=palette.text)
    style.configure("SectionTitle.TLabel", font=(typo.family_semibold, typo.section_header), background=palette.background, foreground=palette.text)
    style.configure("PanelTitle.TLabel", font=(typo.family_semibold, typo.panel_title), background=palette.surface, foreground=palette.text)
    style.configure("Muted.TLabel", foreground=palette.text_muted, background=palette.background, font=(typo.family, typo.caption))
    style.configure("CardMuted.TLabel", foreground=palette.text_muted, background=palette.surface, font=(typo.family, typo.card_subtitle))
    style.configure("Metric.TLabel", font=(typo.family_semibold, typo.metric), background=palette.surface, foreground=palette.text)
    style.configure("MetricLarge.TLabel", font=(typo.family_semibold, typo.metric_large), background=palette.surface, foreground=palette.text)

    configure_card_styles(style, theme)
    configure_toolbar_styles(style, theme)
    configure_sidebar_styles(style, theme)
    configure_button_styles(style, theme)
    configure_form_styles(style, theme)
    configure_table_styles(style, theme)
    configure_status_badge_styles(style, theme)
    return theme
