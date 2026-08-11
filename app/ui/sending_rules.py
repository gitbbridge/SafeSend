import tkinter as tk
from tkinter import ttk

from app.database import db
from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.help.warning_rules import evaluate_settings
from app.ui.shared import section
from app.ui.components.warning_banner import WarningBanner


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Sending Rules", "Pacing, quiet hours, failure thresholds, and compliance defaults.")
    frame.pack(fill="both", expand=True)
    theme = app.theme
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
    for key, _label in keys:
        var = tk.StringVar()
        var.set(settings.get(key, ""))
        vars_by_key[key] = var

    top = ctk_frame(frame, theme, "background")
    top.grid(row=2, column=0, sticky="ew", padx=theme.spacing.page_padding)
    top.columnconfigure(0, weight=1)
    top.columnconfigure(1, weight=1)

    velocity = ctk_frame(top, theme, "card")
    velocity.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
    velocity.columnconfigure((0, 1), weight=1)
    ctk_label(velocity, theme, "Sending Velocity", "panel_title", "card").grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 8))
    _field(velocity, theme, "Delay Between Emails", vars_by_key["delay_seconds"], 1, 0)
    _field(velocity, theme, "Max Emails / Hour", vars_by_key["max_emails_per_hour"], 2, 0)
    _field(velocity, theme, "Max Emails / Day", vars_by_key["max_emails_per_day"], 2, 1)
    banner = WarningBanner(velocity)
    banner.grid(row=5, column=0, columnspan=2, sticky="ew", padx=18, pady=(12, 18))

    rotation = ctk_frame(top, theme, "card")
    rotation.grid(row=0, column=1, sticky="nsew")
    ctk_label(rotation, theme, "Rotation Logic", "panel_title", "card").pack(anchor="w", padx=18, pady=(18, 8))
    for title, body in [
        ("Round-robin", "Rotate distribution across all active SMTP nodes."),
        ("Random", "Shuffle selection to mimic organic sending patterns."),
        ("Weighted", "Prioritize high-reputation servers first."),
    ]:
        row = ctk_frame(rotation, theme, "surface", corner_radius=4, border_width=1)
        row.pack(fill="x", padx=18, pady=(0, 8))
        ctk_label(row, theme, title, "caption", "surface", text_color=theme.palette.text).pack(anchor="w", padx=12, pady=(8, 0))
        ctk_label(row, theme, body, "caption", "surface", wraplength=380).pack(anchor="w", padx=12, pady=(0, 8))

    windows = ctk_frame(frame, theme, "card")
    windows.grid(row=3, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(12, 0))
    windows.columnconfigure((0, 1, 2, 3), weight=1)
    ctk_label(windows, theme, "Sending Windows & Quiet Hours", "panel_title", "card").grid(row=0, column=0, columnspan=4, sticky="w", padx=18, pady=(18, 8))
    _field(windows, theme, "Quiet Hours Start", vars_by_key["quiet_hours_start"], 1, 0)
    _field(windows, theme, "Quiet Hours End", vars_by_key["quiet_hours_end"], 1, 1)
    _field(windows, theme, "Random Delay Min", vars_by_key["random_delay_min"], 2, 0)
    _field(windows, theme, "Random Delay Max", vars_by_key["random_delay_max"], 2, 1)
    ctk_label(windows, theme, "Required Footer", "caption", "card").grid(row=5, column=0, sticky="w", padx=18, pady=(8, 6))
    ctk_entry(windows, theme, vars_by_key["required_footer"]).grid(row=5, column=1, columnspan=3, sticky="ew", padx=(0, 18), pady=(8, 6))

    def refresh_warnings() -> None:
        banner.show_warnings(evaluate_settings({key: var.get() for key, var in vars_by_key.items()}))

    for var in vars_by_key.values():
        var.trace_add("write", lambda *_: refresh_warnings())

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
        refresh_warnings()
        app.status.set("Sending rules saved.")

    footer = ctk_frame(frame, theme, "background")
    footer.grid(row=4, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(14, 0))
    ctk_button(footer, theme, "Reset to Defaults", command=lambda: app.status.set("Defaults placeholder"), width=142).pack(side="right", padx=(8, 0))
    ctk_button(footer, theme, "Apply Changes", command=save, variant="primary", icon="save", width=142).pack(side="right")
    refresh_warnings()


def _field(parent: tk.Widget, theme, label: str, variable: tk.StringVar, row: int, column: int) -> None:
    ctk_label(parent, theme, label, "caption", "card").grid(row=row * 2 - 1, column=column, sticky="w", padx=18, pady=(8, 4))
    ctk_entry(parent, theme, variable).grid(row=row * 2, column=column, sticky="ew", padx=18, pady=(0, 8))
