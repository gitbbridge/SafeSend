import tkinter as tk

import customtkinter as ctk

from app.design_system import components as ds
from app.design_system.icons import ICON_CATEGORIES, icon_color
from app.ui.shared import build_tree, insert_table_row, section


def build(parent: tk.Widget, app) -> None:
    theme = app.theme
    palette = theme.palette
    frame = section(parent, "Design System", "Reusable SafeSend components and visual language.")
    frame.pack(fill="both", expand=True)
    frame.rowconfigure(2, weight=1)

    page = ctk.CTkScrollableFrame(frame, fg_color=palette.background, corner_radius=0)
    page.grid(row=2, column=0, sticky="nsew", padx=theme.spacing.page_padding)
    page.columnconfigure((0, 1, 2), weight=1)

    _colors(page, theme).grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
    _buttons(page, theme).grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=(0, 10))
    _inputs(page, theme).grid(row=0, column=2, sticky="nsew", pady=(0, 10))
    _badges(page, theme).grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
    _selection(page, theme).grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=(0, 10))
    _alerts(page, theme).grid(row=1, column=2, sticky="nsew", pady=(0, 10))
    _cards(page, theme).grid(row=2, column=0, columnspan=2, sticky="nsew", padx=(0, 10), pady=(0, 10))
    _table(page, theme).grid(row=2, column=2, sticky="nsew", pady=(0, 10))
    _empty(page, theme).grid(row=3, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
    ds.SenderReputationCard(page, 92, theme=theme).grid(row=3, column=1, sticky="nsew", padx=(0, 10), pady=(0, 10))
    ds.AIAssistantPanel(page, theme=theme).grid(row=3, column=2, sticky="nsew", pady=(0, 10))
    _icons(page, theme).grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(0, 10))


def _colors(parent: tk.Widget, theme) -> ds.Card:
    card = ds.Card(parent, theme=theme, title="Colors")
    swatches = [
        ("Primary", theme.palette.primary),
        ("Success", theme.palette.success),
        ("Warning", theme.palette.warning),
        ("Danger", theme.palette.danger),
        ("Neutral", theme.palette.secondary),
        ("Light", theme.palette.surface_alt),
    ]
    row = ctk.CTkFrame(card, fg_color="transparent")
    row.grid(row=card.content_row, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
    for idx, (name, color) in enumerate(swatches):
        item = ctk.CTkFrame(row, fg_color="transparent")
        item.grid(row=0, column=idx, sticky="n", padx=(0, 12))
        ctk.CTkFrame(item, width=44, height=44, fg_color=color, corner_radius=7).pack()
        ds.label(item, name, role="caption", theme=theme, surface="transparent").pack(anchor="w", pady=(6, 0))
        ds.label(item, color, role="small", theme=theme, surface="transparent", muted=True).pack(anchor="w")
    return card


def _buttons(parent: tk.Widget, theme) -> ds.Card:
    card = ds.Card(parent, theme=theme, title="Buttons")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=card.content_row, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
    filled = [("primary", "send"), ("success", "success"), ("warning", "warning"), ("danger", "delete")]
    quiet = [("secondary", "settings"), ("outline", "upload"), ("ghost", "more"), ("link", "export")]
    for idx, (variant, icon) in enumerate(filled):
        ds.button(body, variant.title(), variant=variant, theme=theme, icon=icon, width=112).grid(row=0, column=idx, padx=(0, 10), pady=(0, 10))
    for idx, (variant, icon) in enumerate(quiet):
        ds.button(body, variant.title(), variant=variant, theme=theme, icon=icon, width=112).grid(row=1, column=idx, padx=(0, 10), pady=(0, 10))
    return card


def _inputs(parent: tk.Widget, theme) -> ds.Card:
    card = ds.Card(parent, theme=theme, title="Inputs")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=card.content_row, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
    body.columnconfigure((0, 1), weight=1)
    values = {
        "text": tk.StringVar(),
        "email": tk.StringVar(value="user@example.com"),
        "password": tk.StringVar(value="password"),
        "select": tk.StringVar(value="Choose an option"),
        "date": tk.StringVar(value="06/15/2025"),
    }
    ds.label(body, "Text Input", role="caption", theme=theme, surface="transparent").grid(row=0, column=0, sticky="w")
    ds.text_input(body, values["text"], theme=theme, placeholder="Type something...").grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=(2, 10))
    ds.label(body, "Search", role="caption", theme=theme, surface="transparent").grid(row=0, column=1, sticky="w")
    ds.search_box(body, tk.StringVar(), theme=theme).grid(row=1, column=1, sticky="ew", pady=(2, 10))
    ds.label(body, "Email Input", role="caption", theme=theme, surface="transparent").grid(row=2, column=0, sticky="w")
    ds.email_input(body, values["email"], theme=theme).grid(row=3, column=0, sticky="ew", padx=(0, 12), pady=(2, 10))
    ds.label(body, "Password", role="caption", theme=theme, surface="transparent").grid(row=2, column=1, sticky="w")
    ds.password_input(body, values["password"], theme=theme).grid(row=3, column=1, sticky="ew", pady=(2, 10))
    ds.dropdown(body, values["select"], ["Choose an option", "Option 1", "Option 2"], theme=theme).grid(row=5, column=0, sticky="ew", padx=(0, 12), pady=(2, 10))
    ds.toggle(body, "Enabled", tk.BooleanVar(value=True), theme=theme).grid(row=5, column=1, sticky="w", pady=(2, 10))
    return card


def _badges(parent: tk.Widget, theme) -> ds.Card:
    card = ds.Card(parent, theme=theme, title="Badges")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=card.content_row, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
    badges = [("New", "primary"), ("Active", "success"), ("Paused", "paused"), ("Draft", "draft"), ("Failed", "danger"), ("Info", "info")]
    for idx, (text, level) in enumerate(badges):
        ds.status_badge(body, text, level=level, theme=theme).grid(row=idx // 3, column=idx % 3, padx=(0, 10), pady=(0, 10))
    return card


def _selection(parent: tk.Widget, theme) -> ds.Card:
    card = ds.Card(parent, theme=theme, title="Checkboxes & Radio")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=card.content_row, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
    ds.checkbox(body, "I agree to the terms and conditions", tk.BooleanVar(value=True), theme=theme).pack(anchor="w", pady=(0, 8))
    ds.checkbox(body, "Send performance updates", tk.BooleanVar(), theme=theme).pack(anchor="w", pady=(0, 8))
    ds.radio_group(body, ["Option One", "Option Two", "Option Three"], theme=theme).pack(anchor="w")
    return card


def _alerts(parent: tk.Widget, theme) -> ds.Card:
    card = ds.Card(parent, theme=theme, title="Alerts")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=card.content_row, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
    ds.alert(body, "Success!", "Your campaign was sent successfully.", level="success", theme=theme).pack(fill="x", pady=(0, 8))
    ds.alert(body, "Warning!", "Some email addresses may be risky.", level="warning", theme=theme).pack(fill="x", pady=(0, 8))
    ds.alert(body, "Error!", "Failed to connect to SMTP server.", level="danger", theme=theme).pack(fill="x", pady=(0, 8))
    return card


def _cards(parent: tk.Widget, theme) -> ds.Card:
    card = ds.Card(parent, theme=theme, title="Cards")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=card.content_row, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
    body.columnconfigure((0, 1, 2), weight=1)
    ds.MetricCard(body, "SMTP Health", "Healthy", detail="Response 245ms", theme=theme, level="success").grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    ds.CircularProgress(body, 0.92, title="Deliverability Score", detail="Excellent", theme=theme, level="success").grid(row=0, column=1, sticky="nsew", padx=(0, 10))
    ds.MetricCard(body, "Campaign Summary", "12,584", detail="Emails sent", theme=theme).grid(row=0, column=2, sticky="nsew")
    return card


def _table(parent: tk.Widget, theme) -> ds.Card:
    card = ds.Card(parent, theme=theme, title="Table")
    table_frame = ctk.CTkFrame(card, fg_color="transparent")
    table_frame.grid(row=card.content_row, column=0, sticky="nsew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
    tree = build_tree(table_frame, ("id", "campaign", "status", "sent"), headings=("ID", "Campaign Name", "Status", "Sent"), height=5)
    for row in [
        (1, "Welcome Series", "Sent", "2,584"),
        (2, "Product Launch", "Scheduled", "-"),
        (3, "Newsletter", "Sent", "5,632"),
    ]:
        insert_table_row(tree, row)
    return card


def _empty(parent: tk.Widget, theme) -> ds.EmptyState:
    return ds.empty_state(parent, "campaigns", theme=theme, action_text="Create Campaign")


def _icons(parent: tk.Widget, theme) -> ds.Card:
    card = ds.Card(parent, theme=theme, title="Icon Library", subtitle="Named 24px-style line icons rendered from the centralized SafeSend catalog.")
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.grid(row=card.content_row, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))
    body.columnconfigure((0, 1, 2), weight=1)

    categories = [
        "Navigation",
        "SMTP & Infrastructure",
        "Deliverability",
        "Contacts & Lists",
        "Campaign Analytics",
        "Actions & Controls",
        "Status & Indicators",
        "AI & Insights",
        "Email",
    ]
    for idx, category in enumerate(categories):
        group = ctk.CTkFrame(body, fg_color=theme.palette.surface_soft, corner_radius=12, border_width=1, border_color=theme.palette.border_soft)
        group.grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=(0 if idx % 3 == 0 else 10, 0), pady=(0, 10))
        ds.label(group, category, role="caption", theme=theme, surface="transparent", text_color=theme.palette.primary).grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="w",
            padx=12,
            pady=(10, 8),
        )
        for item_index, spec in enumerate(ICON_CATEGORIES.get(category, [])[:12]):
            tile = ctk.CTkFrame(group, fg_color="transparent")
            tile.grid(row=1 + item_index // 4, column=item_index % 4, sticky="n", padx=8, pady=(0, 10))
            ds.icon_label(tile, spec.name, theme=theme, text_color=icon_color(spec.name), size=20, surface="transparent").pack(anchor="center")
            ds.label(tile, spec.label, role="small", theme=theme, surface="transparent", muted=True, wraplength=70, justify="center").pack(anchor="center", pady=(4, 0))
    return card
