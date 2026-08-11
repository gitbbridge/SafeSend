import tkinter as tk
from tkinter import messagebox, ttk

from app.ui.shared import build_tree, fill_tree, labeled_entry, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Suppression List", "Global do-not-send addresses enforced during queue generation.")
    frame.pack(fill="both", expand=True)
    form = ttk.Frame(frame, padding=12, style="Card.TFrame")
    form.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    form.columnconfigure(1, weight=1)
    email = labeled_entry(form, "Email", 0)
    reason = labeled_entry(form, "Reason", 1)

    table_frame = ttk.Frame(frame)
    table_frame.grid(row=3, column=0, sticky="nsew")
    columns = ("id", "email", "reason", "scope", "created_at")
    tree = build_tree(table_frame, columns, height=14)

    def refresh() -> None:
        fill_tree(tree, app.suppression_service.list_entries(), columns)

    def add() -> None:
        if not app.suppression_service.add(email.get(), reason.get()):
            messagebox.showerror("Suppression", "Enter a valid email address.")
            return
        email.set("")
        reason.set("")
        refresh()

    ttk.Button(form, text="Add Suppression", command=add).grid(row=2, column=1, sticky="w", pady=(8, 0))
    frame.rowconfigure(3, weight=1)
    refresh()
