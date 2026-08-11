import tkinter as tk
from tkinter import messagebox, ttk

from app.ui.shared import build_tree, fill_tree, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Sending Queue", "Generated queue after suppression, verification filters, clustering, and rotation.")
    frame.pack(fill="both", expand=True)
    controls = ttk.Frame(frame, padding=12, style="Card.TFrame")
    controls.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    campaigns = app.campaign_service.list_campaigns()
    campaign_labels = [f"{row['id']} - {row['name']} ({row['status']})" for row in campaigns]
    selected_campaign = tk.StringVar(value=campaign_labels[0] if campaign_labels else "")
    include_risky = tk.BooleanVar(value=False)
    include_unknown = tk.BooleanVar(value=False)
    ttk.Label(controls, text="Campaign").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Combobox(controls, textvariable=selected_campaign, values=campaign_labels, state="readonly", width=42).grid(row=0, column=1, sticky="ew", pady=5)
    ttk.Checkbutton(controls, text="Include Risky", variable=include_risky).grid(row=0, column=2, padx=8)
    ttk.Checkbutton(controls, text="Include Unknown", variable=include_unknown).grid(row=0, column=3, padx=8)

    table_frame = ttk.Frame(frame)
    table_frame.grid(row=3, column=0, sticky="nsew")
    columns = ("id", "campaign_name", "recipient_email", "smtp_name", "cluster_group", "verification_status", "status", "error_message")
    tree = build_tree(table_frame, columns, height=17)

    def refresh() -> None:
        fill_tree(tree, app.queue_service.list_queue(), columns)

    def build_queue() -> None:
        if not selected_campaign.get():
            messagebox.showinfo("Queue", "Create or select a campaign first.")
            return
        campaign_id = int(selected_campaign.get().split(" - ", 1)[0])
        result = app.queue_service.build_campaign_queue(campaign_id, include_risky.get(), include_unknown.get())
        refresh()
        messagebox.showinfo("Queue built", f"Queued {result['queued']}. Skipped {result['skipped']}. Suppressed {result['suppressed']}.")

    ttk.Button(controls, text="Build Queue", command=build_queue).grid(row=1, column=1, sticky="w", pady=(8, 0))
    ttk.Button(controls, text="Refresh", command=refresh).grid(row=1, column=2, sticky="w", pady=(8, 0))
    frame.rowconfigure(3, weight=1)
    refresh()
