import tkinter as tk
from tkinter import ttk

from app.database import db
from app.ui.shared import labeled_entry, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Sending Rules", "Pacing, quiet hours, failure thresholds, and compliance defaults.")
    frame.pack(fill="both", expand=True)
    form = ttk.Frame(frame, padding=12, style="Card.TFrame")
    form.grid(row=2, column=0, sticky="ew")
    form.columnconfigure(1, weight=1)
    keys = [
        ("delay_seconds", "Delay between emails"),
        ("random_delay_min", "Random delay min"),
        ("random_delay_max", "Random delay max"),
        ("max_emails_per_hour", "Max emails per hour"),
        ("max_emails_per_day", "Max emails per day"),
        ("quiet_hours_start", "Quiet hours start"),
        ("quiet_hours_end", "Quiet hours end"),
        ("required_footer", "Required footer"),
    ]
    vars_by_key: dict[str, tk.StringVar] = {}
    settings = {row["key"]: row["value"] for row in db.fetch_all("SELECT key, value FROM app_settings")}
    for row_index, (key, label) in enumerate(keys):
        var = labeled_entry(form, label, row_index)
        var.set(settings.get(key, ""))
        vars_by_key[key] = var

    def save() -> None:
        for key, var in vars_by_key.items():
            db.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, var.get()),
            )
        app.status.set("Sending rules saved.")

    ttk.Button(form, text="Save Rules", command=save).grid(row=len(keys), column=1, sticky="w", pady=(12, 0))
