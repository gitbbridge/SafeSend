import tkinter as tk
from tkinter import messagebox, ttk

from app.design_system import components as ds
from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import combobox as ctk_combobox
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.ui.shared import build_tree, fill_tree, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Clustering / Reputation Strategy", "Identify recipient concentration and choose queue ordering.")
    frame.pack(fill="both", expand=True)
    theme = app.theme
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(5, weight=1)

    stats = ctk_frame(frame, theme, "background")
    stats.grid(row=2, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 10))
    stats.columnconfigure((0, 1, 2, 3), weight=1)
    ds.MetricCard(stats, "Cluster Method", "Domain", theme=theme, level="info").grid(row=0, column=0, sticky="ew", padx=(0, 10))
    groups_card = ds.MetricCard(stats, "Detected Groups", "0", theme=theme, level="default")
    groups_card.grid(row=0, column=1, sticky="ew", padx=(0, 10))
    contacts_card = ds.MetricCard(stats, "Contacts Reviewed", "0", theme=theme, level="default")
    contacts_card.grid(row=0, column=2, sticky="ew", padx=(0, 10))
    ds.MetricCard(stats, "Queue Strategy", "Interleaved", theme=theme, level="success").grid(row=0, column=3, sticky="ew")

    controls = ctk_frame(frame, theme, "card")
    controls.grid(row=3, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 12))
    lists = app.import_service.list_contact_lists()
    list_labels = [f"{row['id']} - {row['name']} ({row['total_contacts']})" for row in lists]
    selected_list = tk.StringVar(value=list_labels[0] if list_labels else "")
    field = tk.StringVar(value="domain")
    threshold = tk.StringVar(value="5")
    strategy = tk.StringVar(value="interleaved")
    weighted = tk.StringVar(value="20")
    controls.columnconfigure(1, weight=1)
    controls.columnconfigure(3, weight=1)
    ctk_label(controls, theme, "Contact list", "caption", "card").grid(row=0, column=0, sticky="w", padx=(16, 10), pady=(16, 8))
    ctk_combobox(controls, theme, selected_list, list_labels, width=340).grid(row=0, column=1, sticky="ew", pady=(16, 8))
    ctk_label(controls, theme, "Cluster by", "caption", "card").grid(row=0, column=2, sticky="w", padx=(18, 8), pady=(16, 8))
    ctk_combobox(controls, theme, field, ["domain", "company", "source_list", "verification_category", "custom1"], width=180).grid(row=0, column=3, sticky="ew", pady=(16, 8))
    ctk_label(controls, theme, "Threshold", "caption", "card").grid(row=1, column=0, sticky="w", padx=(16, 10), pady=8)
    ctk_entry(controls, theme, threshold, width=110).grid(row=1, column=1, sticky="w", pady=8)
    ctk_label(controls, theme, "Strategy", "caption", "card").grid(row=1, column=2, sticky="w", padx=(18, 8), pady=8)
    ctk_combobox(controls, theme, strategy, ["standard", "cluster_last", "interleaved", "weighted"], width=180).grid(row=1, column=3, sticky="ew", pady=8)
    ctk_label(controls, theme, "Weighted %", "caption", "card").grid(row=1, column=4, sticky="w", padx=(18, 8), pady=8)
    ctk_entry(controls, theme, weighted, width=110).grid(row=1, column=5, sticky="w", padx=(0, 16), pady=8)

    table_frame = ctk_frame(frame, theme, "card")
    table_frame.grid(row=5, column=0, sticky="nsew", padx=theme.spacing.page_padding)
    columns = ("cluster_group", "cluster_size", "contacts")
    tree = build_tree(table_frame, columns, headings=("Cluster Group", "Cluster Size", "Contacts"), height=18)

    def list_id() -> int:
        return int(selected_list.get().split(" - ", 1)[0]) if selected_list.get() else 0

    def run_cluster() -> None:
        if not list_id():
            messagebox.showinfo("Clustering", "Import or select a contact list first.")
            return
        selected_id = list_id()

        def worker(handle):
            if handle.cancel_requested():
                raise RuntimeError("Cluster analysis cancelled safely.")
            handle.update("Analyzing recipient clusters...")
            def report(current: int, total: int) -> None:
                if handle.cancel_requested():
                    raise RuntimeError("Cluster analysis cancelled safely.")
                handle.update("Analyzing recipient clusters", current=current, total=total)

            result = app.cluster_service.cluster_contacts(
                selected_id,
                field.get(),
                int(threshold.get() or 5),
                progress_callback=report,
            )
            rows = app.cluster_service.preview(selected_id)
            return result, rows

        def done(payload) -> None:
            result, rows = payload
            fill_tree(tree, rows, columns, "No clusters yet. Analyze a contact list to begin.")
            groups_card.value_label.configure(text=str(result["groups"]))
            contacts_card.value_label.configure(text=str(result["total"]))
            app.status.set(f"Clustered {result['clustered']} of {result['total']} contacts across {result['groups']} groups.")

        app.run_background_operation(
            "Analyzing clusters",
            worker,
            detail="Analyzing recipient clusters...",
            on_success=done,
        )

    ctk_button(controls, theme, "Analyze Clusters", command=run_cluster, variant="primary", icon="analyze", width=174).grid(row=2, column=1, sticky="w", pady=(6, 16))
    if list_id():
        rows = app.cluster_service.preview(list_id())
        fill_tree(tree, rows, columns, "No clusters yet. Analyze a contact list to begin.")
        groups_card.value_label.configure(text=str(len(rows)))
        contacts_card.value_label.configure(text=str(sum(int(row.get("cluster_size") or 0) for row in rows)))
