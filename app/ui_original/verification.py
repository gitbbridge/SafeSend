import tkinter as tk
from tkinter import ttk

from app.ui.shared import labeled_entry, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Verification", "Save Emailable credentials and review verification categories.")
    frame.pack(fill="both", expand=True)
    form = ttk.Frame(frame, padding=12, style="Card.TFrame")
    form.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    form.columnconfigure(1, weight=1)
    api_key = labeled_entry(form, "Emailable API key", 0, show="*")
    api_key.set(app.verification_service.settings_key())

    def save() -> None:
        app.verification_service.save_api_key(api_key.get())
        app.status.set("Verification settings saved.")

    ttk.Button(form, text="Save API Key", command=save).grid(row=1, column=1, sticky="w", pady=(8, 0))

    cards = ttk.Frame(frame)
    cards.grid(row=3, column=0, sticky="ew")
    summary = app.verification_service.summary()
    for idx, status in enumerate(["Deliverable", "Risky", "Undeliverable", "Unknown"]):
        card = ttk.Frame(cards, padding=16, style="Card.TFrame")
        card.grid(row=0, column=idx, sticky="nsew", padx=8)
        ttk.Label(card, text=str(summary[status]), font=("Segoe UI Semibold", 22), style="PanelTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text=status, style="CardMuted.TLabel").pack(anchor="w")
        cards.columnconfigure(idx, weight=1)
