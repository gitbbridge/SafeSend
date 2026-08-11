import tkinter as tk

from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.charts import BarChart
from app.design_system import components as ds
from app.database.db import dashboard_counts
from app.ui.shared import section
from app.design_system.icons import get_route_icon
from app.design_system.theme import active_theme


def build(parent: tk.Widget, app) -> None:
    theme = active_theme()
    palette = theme.palette
    space = theme.spacing
    frame = section(parent, "Dashboard", "Workspace overview")
    frame.pack(fill="both", expand=True)
    frame.rowconfigure(3, weight=1, minsize=420)
    frame.columnconfigure(0, weight=1)

    counts = dashboard_counts()
    failed = int(counts.get("failed") or 0)
    sent = int(counts.get("sent") or 0)
    bounce_rate = f"{round((failed / max(sent + failed, 1)) * 100, 1)}%"
    cards = [
        ("Emails Today", counts["sent"], "Completed sends today", "Reports / Logs", "default"),
        ("Delivered Today", counts["sent"], "Successful delivery placeholder", "Reports / Logs", "success"),
        ("Queued", counts["queued"], "Prepared recipients", "Sending Queue", "info"),
        ("Spam Complaints", "0", "No complaint data yet", "Suppression List", "danger"),
        ("Open Rate", "0%", "Tracking appears after sends", "Reports / Logs", "default"),
        ("Click Rate", "0%", "Tracking appears after sends", "Reports / Logs", "default"),
        ("Bounce Rate", bounce_rate, "Based on failed queue rows", "Reports / Logs", "warning" if failed else "success"),
    ]

    card_grid = ctk_frame(frame, theme, "background")
    card_grid.grid(row=2, column=0, sticky="ew", padx=space.page_padding)
    for index, (label, value, caption, route, level) in enumerate(cards):
        row = index // 4
        col = index % 4
        card = ds.MetricCard(card_grid, label, value, detail=caption, theme=theme, level=level or _route_level(route))
        card.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else space.md, 0), pady=(0, space.md))
        ds.icon_label(card, get_route_icon(route), theme=theme, text_color=palette.primary, size=18, surface="card").place(relx=1.0, x=-space.card_padding, y=space.card_padding, anchor="ne")
    for col in range(4):
        card_grid.columnconfigure(col, weight=1)

    body = ctk_frame(frame, theme, "background")
    body.grid(row=3, column=0, sticky="nsew", padx=space.page_padding, pady=(space.sm, 0))
    body.columnconfigure(0, weight=3)
    body.columnconfigure(1, weight=1)
    body.rowconfigure(0, weight=2, minsize=260)
    body.rowconfigure(1, weight=1, minsize=150)

    chart_card = ds.Card(body, theme=theme, title="Sending Volume", subtitle="Live totals across the current workspace.")
    chart_card.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, space.md))
    chart_card.rowconfigure(1, weight=1)
    chart_card.columnconfigure(0, weight=1)
    chart_values = [
        ("Contacts", counts["contacts"], palette.primary),
        ("Campaigns", counts["campaigns"], palette.info),
        ("Queued", counts["queued"], palette.warning),
        ("Suppressed", counts["suppressed"], palette.danger),
    ]
    BarChart(chart_card, chart_values, theme=theme, height=280).grid(row=chart_card.content_row, column=0, sticky="nsew", padx=space.card_padding, pady=(0, space.card_padding))

    health = ds.Card(body, theme=theme, title="System Status", subtitle="Operational readiness at a glance.")
    health.grid(row=0, column=1, sticky="nsew", pady=(0, space.md))
    health_items = [
        ("SMTP Health", "Healthy" if counts["smtp_profiles"] else "Setup needed", "success" if counts["smtp_profiles"] else "warning"),
        ("Queue Summary", "Idle" if counts["queued"] == 0 else "Queued", "success" if counts["queued"] == 0 else "info"),
        ("Deliverability", "Ready for verification", "info"),
        ("Reputation", "Monitor available", "info"),
        ("System Health", "Local database online", "success"),
    ]
    health_body = ctk_frame(health, theme, "background")
    health_body.grid(row=health.content_row, column=0, sticky="nsew", padx=space.card_padding, pady=(0, space.card_padding))
    for col in range(3):
        health_body.columnconfigure(col, weight=1, uniform="health")
    for index, (title, status, level) in enumerate(health_items):
        tile = ctk_frame(health_body, theme, "surface", corner_radius=10, border_width=0)
        tile.grid(row=index // 3, column=index % 3, sticky="nsew", padx=(0 if index % 3 == 0 else space.xs, 0), pady=(0, space.xs))
        tile.configure(height=58)
        tile.grid_propagate(False)
        tile.columnconfigure(1, weight=1)
        ds.icon_label(tile, _status_icon(level), theme=theme, text_color=_badge_color(level, palette), size=14, surface="surface").grid(row=0, column=0, rowspan=2, sticky="nw", padx=(space.sm, space.xs), pady=(space.sm, 0))
        ctk_label(tile, theme, title, role="caption", variant="surface", fg_color=palette.surface_alt).grid(row=0, column=1, sticky="w", padx=(0, space.xs), pady=(space.xs, 0))
        ctk_label(
            tile,
            theme,
            status,
            role="caption",
            variant="surface",
            text_color=_badge_color(level, palette),
            fg_color=palette.surface_alt,
            wraplength=110,
            justify="left",
        ).grid(row=1, column=1, sticky="w", padx=(0, space.xs), pady=(0, space.xs))

    quick = ds.Card(body, theme=theme, title="Quick Actions", subtitle="Common next steps for the workspace.")
    quick.grid(row=1, column=1, sticky="nsew")
    actions = ctk_frame(quick, theme, "card")
    actions.grid(row=quick.content_row, column=0, sticky="nsew", padx=space.card_padding, pady=(0, space.card_padding))
    actions.columnconfigure(0, weight=1)
    quick_actions = [
        ("New Campaign", "new", "Campaigns"),
        ("Import Contacts", "import", "Contacts / Lists"),
        ("Add SMTP Server", "smtp_servers", "SMTP Servers"),
        ("Run Verification", "verified", "Verification"),
        ("View Reports", "reports", "Reports / Logs"),
    ]
    for index, (text, icon, route) in enumerate(quick_actions):
        ds.button(
            actions,
            text,
            command=lambda value=route: app.navigate(value),
            theme=theme,
            variant="secondary" if index else "primary",
            icon=icon,
            anchor="w",
            height=34,
        ).grid(row=index, column=0, sticky="ew", pady=(0 if index == 0 else space.xs, 0))


def _badge_color(level: str, palette) -> str:
    return {
        "success": palette.success,
        "warning": palette.warning,
        "info": palette.info,
        "danger": palette.danger,
    }.get(level, palette.text_muted)


def _route_level(route: str) -> str:
    return {
        "SMTP Servers": "success",
        "Sending Queue": "info",
        "Reports / Logs": "warning",
        "Suppression List": "danger",
    }.get(route, "default")


def _status_icon(level: str) -> str:
    return {
        "success": "success",
        "warning": "warning",
        "info": "info",
        "danger": "error",
    }.get(level, "info")
