import tkinter as tk
from tkinter import ttk

from app.database import db
from app.design_system import components as ds
from app.design_system.charts import BarChart
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.ui.shared import build_tree, fill_tree, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Reports / Logs", "Campaign totals, queue results, SMTP usage, and recent errors.")
    frame.pack(fill="both", expand=True)
    theme = app.theme
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(3, weight=1)
    columns = ("campaign", "total", "sent", "failed", "skipped", "suppressed", "smtp_accounts_used")
    rows = [
        dict(row)
        for row in db.fetch_all(
            """
            SELECT
                campaigns.name AS campaign,
                COUNT(send_queue.id) AS total,
                SUM(CASE WHEN send_queue.status = 'Sent' THEN 1 ELSE 0 END) AS sent,
                SUM(CASE WHEN send_queue.status = 'Failed' THEN 1 ELSE 0 END) AS failed,
                SUM(CASE WHEN send_queue.status = 'Skipped' THEN 1 ELSE 0 END) AS skipped,
                SUM(CASE WHEN send_queue.status = 'Suppressed' THEN 1 ELSE 0 END) AS suppressed,
                COUNT(DISTINCT send_queue.smtp_profile_id) AS smtp_accounts_used
            FROM campaigns
            LEFT JOIN send_queue ON send_queue.campaign_id = campaigns.id
            GROUP BY campaigns.id
            ORDER BY campaigns.created_at DESC
            """
        )
    ]
    totals = {
        "Campaigns": len(rows),
        "Sent": sum(int(row.get("sent") or 0) for row in rows),
        "Failed": sum(int(row.get("failed") or 0) for row in rows),
        "Suppressed": sum(int(row.get("suppressed") or 0) for row in rows),
    }

    top = ctk_frame(frame, theme, "background")
    top.grid(row=2, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, theme.spacing.md))
    top.columnconfigure(0, weight=1)
    top.columnconfigure(1, weight=1)
    performance = ds.Card(top, theme=theme, title="Campaign Performance", subtitle="Analyzing delivery metrics for current campaigns.")
    performance.grid(row=0, column=0, sticky="nsew", padx=(0, theme.spacing.md))
    ctk_label(performance, theme, "34.2%", "metric_large", "card").grid(row=performance.content_row, column=0, sticky="w", padx=theme.spacing.card_padding)
    BarChart(
        performance,
        [("Sent", totals["Sent"], theme.palette.success), ("Failed", totals["Failed"], theme.palette.danger), ("Suppressed", totals["Suppressed"], theme.palette.warning)],
        theme=theme,
        height=150,
    ).grid(row=performance.content_row + 1, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.card_padding))

    breakdown = ds.Card(top, theme=theme, title="Delivery Breakdown", subtitle="Queued outcomes by category.")
    breakdown.grid(row=0, column=1, sticky="nsew")
    for idx, (label, value) in enumerate(totals.items()):
        level = {"Sent": "success", "Failed": "danger", "Suppressed": "warning"}.get(label, "default")
        ds.MetricCard(breakdown, label, value, theme=theme, level=level).grid(row=breakdown.content_row + idx // 2, column=idx % 2, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.sm))
        breakdown.columnconfigure(idx % 2, weight=1)

    bottom = ctk_frame(frame, theme, "background")
    bottom.grid(row=3, column=0, sticky="nsew", padx=theme.spacing.page_padding)
    bottom.columnconfigure(0, weight=2)
    bottom.columnconfigure(1, weight=1)
    bottom.rowconfigure(0, weight=1)
    table_frame = ctk_frame(bottom, app.theme, "card")
    table_frame.grid(row=0, column=0, sticky="nsew", padx=(0, theme.spacing.md))
    tree = build_tree(table_frame, columns, height=12)
    fill_tree(tree, rows, columns)

    errors = ds.Card(bottom, theme=theme, title="Error Logs", subtitle="Recent delivery issues detected.")
    errors.grid(row=0, column=1, sticky="nsew")
    for idx, (title, detail, level) in enumerate([
        ("SMTP Timeout", "Server did not respond before timeout.", "danger"),
        ("SMTP 421", "Temporary unavailable response.", "warning"),
        ("Connection Timeout", "Thread paused after connection delay.", "danger"),
    ]):
        row = ctk_frame(errors, theme, "surface", corner_radius=4, border_width=0)
        row.grid(row=errors.content_row + idx, column=0, sticky="ew", padx=theme.spacing.card_padding, pady=(0, theme.spacing.sm))
        ds.icon_label(row, "warning" if level == "warning" else "error", theme=theme, text_color=theme.palette.warning if level == "warning" else theme.palette.danger, size=14, surface="surface").pack(side="left", padx=(10, 8), pady=10)
        ctk_label(row, theme, title, "caption", "surface", text_color=theme.palette.text).pack(anchor="w", pady=(8, 0))
        ctk_label(row, theme, detail, "caption", "surface").pack(anchor="w", pady=(0, 8))
