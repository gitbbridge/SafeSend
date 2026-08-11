import tkinter as tk
from tkinter import ttk

from app.database import db
from app.ui.shared import section
from app.utils.paths import CONFIG_DIR, DATA_DIR, LOG_DIR


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Settings", "Local database, folders, and application configuration.")
    frame.pack(fill="both", expand=True)
    panel = ttk.Frame(frame, padding=18, style="Card.TFrame")
    panel.grid(row=2, column=0, sticky="ew")
    ttk.Label(panel, text="Local Paths", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
    for idx, (label, path) in enumerate([("Data", DATA_DIR), ("Logs", LOG_DIR), ("Config", CONFIG_DIR)], start=1):
        ttk.Label(panel, text=label, style="CardMuted.TLabel").grid(row=idx, column=0, sticky="w", pady=3)
        ttk.Label(panel, text=str(path), style="CardMuted.TLabel").grid(row=idx, column=1, sticky="w", padx=10, pady=3)

    settings_panel = ttk.Frame(frame, padding=18, style="Card.TFrame")
    settings_panel.grid(row=3, column=0, sticky="nsew", pady=(14, 0))
    ttk.Label(settings_panel, text="Stored Settings", style="PanelTitle.TLabel").pack(anchor="w", pady=(0, 8))
    text = tk.Text(settings_panel, height=14, wrap="word")
    text.pack(fill="both", expand=True)
    rows = db.fetch_all("SELECT key, value, updated_at FROM app_settings ORDER BY key")
    text.insert("1.0", "\n".join(f"{row['key']} = {row['value']} ({row['updated_at']})" for row in rows))
    text.configure(state="disabled")
    frame.rowconfigure(3, weight=1)
