import tkinter as tk
from tkinter import ttk

from app.design_system import components as ds
from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.ui.shared import section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Verification", "Save Emailable credentials and review verification categories.")
    frame.pack(fill="both", expand=True)
    theme = app.theme
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(4, weight=1)

    form = ctk_frame(frame, theme, "card")
    form.grid(row=2, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 12))
    form.columnconfigure(0, weight=1)
    form.columnconfigure(1, weight=0)
    ctk_label(form, theme, "Verification Provider", "panel_title", "card").grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))
    ctk_label(form, theme, "Connect Emailable to keep list quality visible before campaigns are queued.", "caption", "card", wraplength=720).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))
    api_key = tk.StringVar()
    api_key.set(app.verification_service.settings_key())
    ctk_entry(form, theme, api_key, placeholder_text="Emailable API key", show="*").grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))

    def save() -> None:
        app.verification_service.save_api_key(api_key.get())
        app.status.set("Verification settings saved.")

    ctk_button(form, theme, "Save API Key", command=save, variant="primary", icon="save", width=158).grid(row=2, column=1, sticky="e", padx=(0, 18), pady=(0, 18))

    cards = ctk_frame(frame, theme, "background")
    cards.grid(row=3, column=0, sticky="ew", padx=theme.spacing.page_padding)
    summary = app.verification_service.summary()
    for idx, status in enumerate(["Deliverable", "Risky", "Undeliverable", "Unknown"]):
        level = {"Deliverable": "success", "Risky": "warning", "Undeliverable": "danger"}.get(status, "default")
        card = ds.MetricCard(cards, status, summary[status], theme=theme, level=level)
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 10, 0))
        cards.columnconfigure(idx, weight=1)

    readiness = ctk_frame(frame, theme, "card")
    readiness.grid(row=4, column=0, sticky="nsew", padx=theme.spacing.page_padding, pady=(12, 0))
    readiness.columnconfigure(0, weight=1)
    ctk_label(readiness, theme, "Verification Readiness", "panel_title", "card").grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))
    ctk_label(
        readiness,
        theme,
        "Imported contacts will be grouped as deliverable, risky, undeliverable, or unknown after verification runs are connected in the sending workflow.",
        "caption",
        "card",
        wraplength=900,
    ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 18))
