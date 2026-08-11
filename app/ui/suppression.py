import tkinter as tk
from tkinter import messagebox, ttk

from app.design_system import components as ds
from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.ui.shared import build_tree, fill_tree, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Suppression List", "Global do-not-send addresses enforced during queue generation.")
    frame.pack(fill="both", expand=True)
    theme = app.theme
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(4, weight=1)

    metrics = ctk_frame(frame, theme, "background")
    metrics.grid(row=2, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 10))
    metrics.columnconfigure((0, 1, 2, 3), weight=1)
    total_card = ds.MetricCard(metrics, "Suppressed Emails", "0", theme=theme, level="danger")
    total_card.grid(row=0, column=0, sticky="ew", padx=(0, 10))
    ds.MetricCard(metrics, "Global Scope", "Active", theme=theme, level="success").grid(row=0, column=1, sticky="ew", padx=(0, 10))
    ds.MetricCard(metrics, "CSV Imports", "Ready", theme=theme, level="info").grid(row=0, column=2, sticky="ew", padx=(0, 10))
    ds.MetricCard(metrics, "Queue Protection", "On", theme=theme, level="success").grid(row=0, column=3, sticky="ew")

    form = ctk_frame(frame, theme, "toolbar")
    form.grid(row=3, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 12))
    form.columnconfigure(1, weight=1)
    form.columnconfigure(3, weight=1)
    email = tk.StringVar()
    reason = tk.StringVar()
    ctk_label(form, theme, "Email", "caption", "card").grid(row=0, column=0, sticky="w", padx=(14, 8), pady=12)
    ctk_entry(form, theme, email, placeholder_text="name@example.com").grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=12)
    ctk_label(form, theme, "Reason", "caption", "card").grid(row=0, column=2, sticky="w", padx=(0, 8), pady=12)
    ctk_entry(form, theme, reason, placeholder_text="Manual suppression, bounce, complaint...").grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=12)

    table_frame = ctk_frame(frame, theme, "card")
    table_frame.grid(row=4, column=0, sticky="nsew", padx=theme.spacing.page_padding)
    columns = ("id", "email", "reason", "scope", "created_at")
    tree = build_tree(table_frame, columns, headings=("ID", "Email", "Reason", "Scope", "Created"), height=18)

    def refresh() -> None:
        rows = app.suppression_service.list_entries()
        fill_tree(tree, rows, columns, "No suppressed contacts yet.")
        total_card.value_label.configure(text=str(len(rows)))

    def add() -> None:
        if not app.suppression_service.add(email.get(), reason.get()):
            messagebox.showerror("Suppression", "Enter a valid email address.")
            return
        email.set("")
        reason.set("")
        refresh()

    ctk_button(form, theme, "Add Suppression", command=add, variant="primary", icon="suppression", width=164).grid(row=0, column=4, sticky="e", padx=(0, 14), pady=12)
    refresh()
