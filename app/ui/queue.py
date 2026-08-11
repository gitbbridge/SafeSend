import tkinter as tk
from tkinter import messagebox, ttk

from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import checkbox as ctk_checkbox
from app.design_system.customtkinter_adapter import combobox as ctk_combobox
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.ui.shared import build_tree, fill_tree, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Sending Queue", "Generated queue after suppression, verification filters, clustering, and rotation.")
    frame.pack(fill="both", expand=True)
    theme = app.theme
    controls = ctk_frame(frame, theme, "background")
    controls.grid(row=2, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 12))
    campaigns = app.campaign_service.list_campaigns()
    campaign_labels = [f"{row['id']} - {row['name']} ({row['status']})" for row in campaigns]
    selected_campaign = tk.StringVar(value=campaign_labels[0] if campaign_labels else "")
    include_risky = tk.BooleanVar(value=False)
    include_unknown = tk.BooleanVar(value=False)
    controls.columnconfigure(1, weight=1)
    ctk_button(controls, theme, "New Queue", command=lambda: build_queue(), variant="primary", icon="new", width=128).grid(row=0, column=0, padx=(0, 8), pady=4)
    ctk_combobox(controls, theme, selected_campaign, campaign_labels, width=360).grid(row=0, column=1, sticky="ew", pady=4)
    ctk_checkbox(controls, theme, "Include Risky", include_risky).grid(row=0, column=2, padx=12, pady=4)
    ctk_checkbox(controls, theme, "Include Unknown", include_unknown).grid(row=0, column=3, padx=(0, 16), pady=4)

    table_frame = ctk_frame(frame, theme, "card")
    table_frame.grid(row=3, column=0, sticky="nsew", padx=theme.spacing.page_padding)
    columns = ("id", "campaign_name", "recipient_email", "smtp_name", "cluster_group", "verification_status", "status", "error_message")
    tree = build_tree(table_frame, columns, height=17)

    def refresh() -> None:
        fill_tree(tree, app.queue_service.list_queue(), columns)

    def build_queue() -> None:
        if not selected_campaign.get():
            messagebox.showinfo("Queue", "Create or select a campaign first.")
            return
        campaign_id = int(selected_campaign.get().split(" - ", 1)[0])

        def worker(handle):
            if handle.cancel_requested():
                raise RuntimeError("Queue build cancelled safely.")
            handle.update("Building campaign queue...")
            def report(current: int, total: int) -> None:
                if handle.cancel_requested():
                    raise RuntimeError("Queue build cancelled safely.")
                handle.update("Building campaign queue", current=current, total=total)

            return app.queue_service.build_campaign_queue(
                campaign_id,
                include_risky.get(),
                include_unknown.get(),
                progress_callback=report,
            )

        def done(result) -> None:
            refresh()
            messagebox.showinfo("Queue built", f"Queued {result['queued']}. Skipped {result['skipped']}. Suppressed {result['suppressed']}.")

        app.run_background_operation(
            "Building campaign queue",
            worker,
            detail="Building campaign queue...",
            on_success=done,
        )

    ctk_button(controls, theme, "Refresh", command=refresh, icon="refresh", width=122).grid(row=0, column=4, sticky="w", padx=8, pady=4)
    frame.rowconfigure(3, weight=1)
    refresh()
