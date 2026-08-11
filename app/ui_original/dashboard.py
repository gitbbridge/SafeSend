import tkinter as tk
from tkinter import ttk

from app.database.db import dashboard_counts
from app.ui.shared import section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Dashboard", f"Local workspace status using {app.theme_name} theme")
    frame.pack(fill="both", expand=True)
    counts = dashboard_counts()
    cards = [
        ("SMTP Profiles", counts["smtp_profiles"]),
        ("Contact Lists", counts["contact_lists"]),
        ("Contacts", counts["contacts"]),
        ("Campaigns", counts["campaigns"]),
        ("Queued", counts["queued"]),
        ("Sent", counts["sent"]),
        ("Failed", counts["failed"]),
        ("Suppressed", counts["suppressed"]),
    ]
    grid = ttk.Frame(frame)
    grid.grid(row=2, column=0, sticky="nsew")
    for index, (label, value) in enumerate(cards):
        card = ttk.Frame(grid, padding=18, style="Card.TFrame")
        card.grid(row=index // 4, column=index % 4, sticky="nsew", padx=8, pady=8)
        ttk.Label(card, text=str(value), font=("Segoe UI Semibold", 26), style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text=label, style="CardMuted.TLabel").pack(anchor="w")
    for col in range(4):
        grid.columnconfigure(col, weight=1)

    checklist = ttk.Frame(frame, padding=18, style="Card.TFrame")
    checklist.grid(row=3, column=0, sticky="ew", padx=8, pady=(18, 0))
    ttk.Label(checklist, text="Safety Readiness", style="PanelTitle.TLabel").pack(anchor="w")
    for item in [
        "Use verified, permission-based lists only.",
        "Keep unsubscribe/footer text in every campaign.",
        "Respect quiet hours, hourly limits, and SMTP provider policies.",
        "Run clustering before large sends to avoid concentrated domain bursts.",
    ]:
        ttk.Label(checklist, text=item, style="CardMuted.TLabel").pack(anchor="w", pady=2)
