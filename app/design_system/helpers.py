import tkinter as tk
from tkinter import ttk


def create_page_header(parent: tk.Widget, title: str, subtitle: str = "") -> ttk.Frame:
    from app.design_system.theme import active_theme

    theme = active_theme()
    frame = ttk.Frame(parent, padding=theme.spacing.page_padding)
    frame.columnconfigure(0, weight=1)
    ttk.Label(frame, text=title, style="Title.TLabel").grid(row=0, column=0, sticky="w")
    if subtitle:
        ttk.Label(frame, text=subtitle, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(theme.spacing.xs, theme.spacing.lg))
    return frame


def create_toolbar(parent: tk.Widget) -> ttk.Frame:
    from app.design_system.theme import active_theme

    return ttk.Frame(parent, padding=active_theme().spacing.toolbar_padding, style="Toolbar.TFrame")


def create_statistics_card(parent: tk.Widget, title: str, value: str, subtitle: str = "") -> ttk.Frame:
    return _card(parent, title, value, subtitle, "StatisticsCard.TFrame")


def create_help_panel(parent: tk.Widget, title: str, body: str) -> ttk.Frame:
    card = _base_card(parent, "HelpCard.TFrame")
    ttk.Label(card, text=title, style="PanelTitle.TLabel").pack(anchor="w")
    ttk.Label(card, text=body, style="CardMuted.TLabel", wraplength=360, justify="left").pack(anchor="w", pady=(6, 0))
    return card


def create_section_header(parent: tk.Widget, title: str, subtitle: str = "") -> ttk.Frame:
    from app.design_system.theme import active_theme

    theme = active_theme()
    frame = ttk.Frame(parent)
    ttk.Label(frame, text=title, style="SectionTitle.TLabel").pack(anchor="w")
    if subtitle:
        ttk.Label(frame, text=subtitle, style="Muted.TLabel").pack(anchor="w", pady=(theme.spacing.xs, 0))
    return frame


def create_primary_button(parent: tk.Widget, text: str, command=None) -> ttk.Button:
    return ttk.Button(parent, text=text, command=command, style="Primary.TButton")


def create_table(parent: tk.Widget, columns: tuple[str, ...], headings: tuple[str, ...] | None = None, height: int = 12) -> ttk.Treeview:
    from app.ui.shared import build_tree

    return build_tree(parent, columns, headings=headings, height=height)


def create_status_badge(parent: tk.Widget, text: str, level: str) -> ttk.Label:
    from app.design_system.status_badges import status_help, status_style
    from app.design_system.tooltips import tooltip

    label = ttk.Label(parent, text=text, style=status_style(level))
    tooltip(label, status_help(level))
    return label


def create_chart_card(parent: tk.Widget, title: str) -> ttk.Frame:
    card = _base_card(parent, "ChartCard.TFrame")
    ttk.Label(card, text=title, style="PanelTitle.TLabel").pack(anchor="w")
    return card


def _card(parent: tk.Widget, title: str, value: str, subtitle: str, style: str) -> ttk.Frame:
    card = _base_card(parent, style)
    ttk.Label(card, text=title, style="CardMuted.TLabel").pack(anchor="w")
    ttk.Label(card, text=value, style="Metric.TLabel").pack(anchor="w", pady=(6, 0))
    if subtitle:
        ttk.Label(card, text=subtitle, style="CardMuted.TLabel").pack(anchor="w")
    return card


def _base_card(parent: tk.Widget, style: str) -> ttk.Frame:
    from app.design_system.theme import active_theme

    return ttk.Frame(parent, padding=active_theme().spacing.card_padding, style=style)
