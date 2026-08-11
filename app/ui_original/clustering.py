import tkinter as tk
from tkinter import messagebox, ttk

from app.ui.shared import build_tree, fill_tree, section


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Clustering / Reputation Strategy", "Identify recipient concentration and choose queue ordering.")
    frame.pack(fill="both", expand=True)
    controls = ttk.Frame(frame, padding=12, style="Card.TFrame")
    controls.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    lists = app.import_service.list_contact_lists()
    list_labels = [f"{row['id']} - {row['name']} ({row['total_contacts']})" for row in lists]
    selected_list = tk.StringVar(value=list_labels[0] if list_labels else "")
    field = tk.StringVar(value="domain")
    threshold = tk.StringVar(value="5")
    strategy = tk.StringVar(value="interleaved")
    weighted = tk.StringVar(value="20")
    ttk.Label(controls, text="Contact list").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Combobox(controls, textvariable=selected_list, values=list_labels, state="readonly", width=34).grid(row=0, column=1, sticky="ew", pady=5)
    ttk.Label(controls, text="Cluster by").grid(row=0, column=2, sticky="w", padx=(14, 4))
    ttk.Combobox(controls, textvariable=field, values=["domain", "company", "source_list", "verification_category", "custom1"], state="readonly").grid(row=0, column=3)
    ttk.Label(controls, text="Threshold").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Entry(controls, textvariable=threshold, width=8).grid(row=1, column=1, sticky="w", pady=5)
    ttk.Label(controls, text="Strategy").grid(row=1, column=2, sticky="w", padx=(14, 4))
    ttk.Combobox(controls, textvariable=strategy, values=["standard", "cluster_last", "interleaved", "weighted"], state="readonly").grid(row=1, column=3)
    ttk.Label(controls, text="Weighted %").grid(row=1, column=4, sticky="w", padx=(14, 4))
    ttk.Entry(controls, textvariable=weighted, width=8).grid(row=1, column=5, sticky="w")

    table_frame = ttk.Frame(frame)
    table_frame.grid(row=3, column=0, sticky="nsew")
    columns = ("cluster_group", "cluster_size", "contacts")
    tree = build_tree(table_frame, columns, height=14)

    def list_id() -> int:
        return int(selected_list.get().split(" - ", 1)[0]) if selected_list.get() else 0

    def run_cluster() -> None:
        if not list_id():
            messagebox.showinfo("Clustering", "Import or select a contact list first.")
            return
        result = app.cluster_service.cluster_contacts(list_id(), field.get(), int(threshold.get() or 5))
        fill_tree(tree, app.cluster_service.preview(list_id()), columns)
        app.status.set(f"Clustered {result['clustered']} of {result['total']} contacts across {result['groups']} groups.")

    ttk.Button(controls, text="Analyze Clusters", command=run_cluster).grid(row=2, column=1, sticky="w", pady=(10, 0))
    frame.rowconfigure(3, weight=1)
    if list_id():
        fill_tree(tree, app.cluster_service.preview(list_id()), columns)
