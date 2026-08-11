import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from app.services.import_service import SUPPORTED_FIELDS
from app.ui.shared import build_tree, section

CONTACT_COLUMNS = (
    "id",
    "email",
    "first_name",
    "last_name",
    "company",
    "phone",
    "city",
    "state",
    "verification_status",
    "suppressed_label",
    "last_sent_at",
    "last_verified_at",
)


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Contacts / Lists", "Import, search, edit, suppress, export, and organize contact lists.")
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=4)
    frame.rowconfigure(4, weight=1)

    selected_list_id = tk.IntVar(value=0)
    search_var = tk.StringVar()
    verification_var = tk.StringVar(value="All")
    suppressed_var = tk.StringVar(value="All")
    sort_state = {"column": "email", "descending": False}
    current_contacts: list[dict] = []

    list_panel = ttk.Frame(frame, padding=12, style="Card.TFrame")
    list_panel.grid(row=2, column=0, rowspan=3, sticky="nsew", padx=(0, 12))
    list_panel.columnconfigure(0, weight=1)
    list_panel.rowconfigure(2, weight=1)
    ttk.Label(list_panel, text="Contact Lists", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
    list_toolbar = ttk.Frame(list_panel)
    list_toolbar.grid(row=1, column=0, sticky="ew", pady=8)
    list_toolbar.columnconfigure((0, 1), weight=1)

    list_tree = build_tree(
        list_panel,
        ("id", "name", "total_contacts", "last_imported_at", "last_verified_at"),
        headings=("#", "List", "Count", "Imported", "Verified"),
        height=12,
    )
    list_tree.column("id", width=36, stretch=False)
    list_tree.column("total_contacts", width=62, stretch=False)

    ttk.Button(list_toolbar, text="New", command=lambda: edit_list()).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)
    ttk.Button(list_toolbar, text="Rename", command=lambda: edit_list(selected_list_id.get())).grid(row=0, column=1, sticky="ew", pady=2)
    ttk.Button(list_toolbar, text="Duplicate", command=lambda: duplicate_list()).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=2)
    ttk.Button(list_toolbar, text="Archive", command=lambda: archive_list()).grid(row=1, column=1, sticky="ew", pady=2)
    ttk.Button(list_toolbar, text="Delete", command=lambda: delete_list()).grid(row=2, column=0, columnspan=2, sticky="ew", pady=2)

    stats_panel = ttk.Frame(frame)
    stats_panel.grid(row=2, column=1, sticky="ew", pady=(0, 10))
    stat_labels = _build_stats(stats_panel)

    toolbar = ttk.Frame(frame, padding=12, style="Card.TFrame")
    toolbar.grid(row=3, column=1, sticky="ew", pady=(0, 10))
    toolbar.columnconfigure(1, weight=1)
    ttk.Label(toolbar, text="Search").grid(row=0, column=0, sticky="w", padx=(0, 6))
    search_entry = ttk.Entry(toolbar, textvariable=search_var)
    search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
    ttk.Label(toolbar, text="Verification").grid(row=0, column=2, sticky="w", padx=(0, 6))
    ttk.Combobox(
        toolbar,
        textvariable=verification_var,
        values=["All", "Deliverable", "Risky", "Unknown", "Undeliverable"],
        state="readonly",
        width=14,
    ).grid(row=0, column=3, sticky="w", padx=(0, 8))
    ttk.Label(toolbar, text="Suppression").grid(row=0, column=4, sticky="w", padx=(0, 6))
    ttk.Combobox(toolbar, textvariable=suppressed_var, values=["All", "Suppressed", "Not suppressed"], state="readonly", width=15).grid(
        row=0, column=5, sticky="w"
    )

    actions = ttk.Frame(toolbar)
    actions.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(10, 0))
    ttk.Button(actions, text="Import CSV", command=lambda: open_import_wizard()).pack(side="left")
    ttk.Button(actions, text="New Contact", command=lambda: edit_contact()).pack(side="left", padx=5)
    ttk.Button(actions, text="Delete", command=lambda: delete_selected()).pack(side="left", padx=5)
    ttk.Button(actions, text="Suppress", command=lambda: suppress_selected()).pack(side="left", padx=5)
    ttk.Button(actions, text="Unsuppress", command=lambda: unsuppress_selected()).pack(side="left", padx=5)
    ttk.Button(actions, text="Move", command=lambda: move_or_copy("move")).pack(side="left", padx=5)
    ttk.Button(actions, text="Copy", command=lambda: move_or_copy("copy")).pack(side="left", padx=5)
    ttk.Button(actions, text="Export Selected", command=lambda: export_contacts("selected")).pack(side="left", padx=(18, 5))
    ttk.Button(actions, text="Export Filtered", command=lambda: export_contacts("filtered")).pack(side="left", padx=5)
    ttk.Button(actions, text="Export List", command=lambda: export_contacts("list")).pack(side="left", padx=5)

    grid_frame = ttk.Frame(frame)
    grid_frame.grid(row=4, column=1, sticky="nsew")
    contact_tree = build_tree(
        grid_frame,
        CONTACT_COLUMNS,
        headings=(
            "#",
            "Email",
            "First Name",
            "Last Name",
            "Company",
            "Phone",
            "City",
            "State",
            "Verification",
            "Suppressed",
            "Last Sent",
            "Last Verified",
        ),
        height=18,
    )
    contact_tree.configure(selectmode="extended")
    contact_tree.column("id", width=42, stretch=False)
    contact_tree.column("suppressed_label", width=88, stretch=False)
    contact_tree.column("verification_status", width=104, stretch=False)

    def refresh_lists(select_id: int | None = None) -> None:
        rows = app.contact_list_service.list_lists()
        _clear_tree(list_tree)
        for row in rows:
            item_id = list_tree.insert(
                "",
                "end",
                values=[
                    row.get("id", ""),
                    row.get("name", ""),
                    row.get("total_contacts", 0),
                    row.get("last_imported_at") or "-",
                    row.get("last_verified_at") or "-",
                ],
            )
            if select_id and int(row["id"]) == select_id:
                list_tree.selection_set(item_id)
                list_tree.focus(item_id)
                list_tree.see(item_id)
        if select_id:
            selected_list_id.set(select_id)
        elif rows and not selected_list_id.get():
            selected_list_id.set(int(rows[0]["id"]))
            list_tree.selection_set(list_tree.get_children()[0])
        refresh_contacts()

    def refresh_contacts() -> None:
        nonlocal current_contacts
        current_contacts = app.contact_service.list_contacts(
            selected_list_id.get() or None,
            search_var.get(),
            verification_var.get(),
            suppressed_var.get(),
            sort_state["column"],
            sort_state["descending"],
        )
        _clear_tree(contact_tree)
        for contact in current_contacts:
            row = dict(contact)
            row["suppressed_label"] = "Yes" if row.get("suppressed") else "No"
            contact_tree.insert("", "end", values=[row.get(column, "") or "" for column in CONTACT_COLUMNS])
        _update_stats(stat_labels, app.contact_list_service.stats(selected_list_id.get() or None))
        app.status.set(f"{len(current_contacts)} contacts shown")

    def list_selected(_event=None) -> None:
        selection = list_tree.selection()
        if not selection:
            return
        values = list_tree.item(selection[0], "values")
        selected_list_id.set(int(values[0]))
        refresh_contacts()

    def edit_list(list_id: int = 0) -> None:
        existing = app.contact_list_service.get_list(list_id) if list_id else None
        name = simpledialog.askstring("Contact list", "List name:", initialvalue=(existing or {}).get("name", ""), parent=frame)
        if name is None:
            return
        notes = simpledialog.askstring("Contact list notes", "Notes/internal label:", initialvalue=(existing or {}).get("notes", ""), parent=frame)
        if notes is None:
            notes = (existing or {}).get("notes", "")
        try:
            if existing:
                app.contact_list_service.rename_list(list_id, name, notes)
                refresh_lists(list_id)
            else:
                new_id = app.contact_list_service.create_list(name, notes)
                refresh_lists(new_id)
        except Exception as exc:
            messagebox.showerror("Contact list", str(exc))

    def duplicate_list() -> None:
        if not selected_list_id.get():
            messagebox.showinfo("Duplicate list", "Select a contact list first.")
            return
        try:
            new_id = app.contact_list_service.duplicate_list(selected_list_id.get())
            refresh_lists(new_id)
        except Exception as exc:
            messagebox.showerror("Duplicate list", str(exc))

    def archive_list() -> None:
        if not selected_list_id.get():
            messagebox.showinfo("Archive list", "Select a contact list first.")
            return
        app.contact_list_service.archive_list(selected_list_id.get(), True)
        selected_list_id.set(0)
        refresh_lists()

    def delete_list() -> None:
        if not selected_list_id.get():
            messagebox.showinfo("Delete list", "Select a contact list first.")
            return
        selected = app.contact_list_service.get_list(selected_list_id.get())
        if not selected:
            return
        if not messagebox.askyesno("Delete list", f"Delete {selected['name']} and all contacts in it?"):
            return
        app.contact_list_service.delete_list(selected_list_id.get())
        selected_list_id.set(0)
        refresh_lists()

    def selected_contact_ids() -> list[int]:
        ids = []
        for item in contact_tree.selection():
            values = contact_tree.item(item, "values")
            if values:
                ids.append(int(values[0]))
        return ids

    def edit_contact(contact_id: int = 0) -> None:
        if not selected_list_id.get() and not contact_id:
            messagebox.showinfo("New contact", "Create or select a contact list first.")
            return
        ContactEditor(frame, app, selected_list_id.get(), contact_id, on_save=lambda: (refresh_lists(selected_list_id.get()), refresh_contacts()))

    def open_selected_contact(_event=None) -> None:
        ids = selected_contact_ids()
        if ids:
            contact = app.contact_service.get_contact(ids[0])
            edit_contact(ids[0] if contact else 0)

    def delete_selected() -> None:
        ids = selected_contact_ids()
        if not ids:
            messagebox.showinfo("Delete contacts", "Select one or more contacts.")
            return
        if not messagebox.askyesno("Delete contacts", f"Delete {len(ids)} selected contacts?"):
            return
        app.contact_service.delete_contacts(ids)
        refresh_lists(selected_list_id.get())

    def suppress_selected() -> None:
        ids = selected_contact_ids()
        if not ids:
            messagebox.showinfo("Suppress contacts", "Select one or more contacts.")
            return
        changed = app.contact_service.suppress_contacts(ids)
        refresh_contacts()
        app.status.set(f"Suppressed {changed} contacts.")

    def unsuppress_selected() -> None:
        ids = selected_contact_ids()
        if not ids:
            messagebox.showinfo("Unsuppress contacts", "Select one or more contacts.")
            return
        changed = app.contact_service.unsuppress_contacts(ids)
        refresh_contacts()
        app.status.set(f"Unsuppressed {changed} contacts.")

    def move_or_copy(action: str) -> None:
        ids = selected_contact_ids()
        if not ids:
            messagebox.showinfo(action.title(), "Select one or more contacts.")
            return
        target_id = choose_target_list(frame, app, selected_list_id.get())
        if not target_id:
            return
        result = app.contact_service.move_contacts(ids, target_id) if action == "move" else app.contact_service.copy_contacts(ids, target_id)
        refresh_lists(selected_list_id.get())
        messagebox.showinfo(action.title(), ", ".join(f"{key}: {value}" for key, value in result.items()))

    def export_contacts(scope: str) -> None:
        if scope == "selected":
            ids = set(selected_contact_ids())
            contacts = [contact for contact in current_contacts if int(contact["id"]) in ids]
        elif scope == "list":
            contacts = app.contact_service.list_contacts(selected_list_id.get() or None, "", "All", "All")
        else:
            contacts = current_contacts
        if not contacts:
            messagebox.showinfo("Export contacts", "No contacts to export.")
            return
        path = filedialog.asksaveasfilename(
            title="Export contacts",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        count = app.export_service.export_contacts(contacts, path)
        messagebox.showinfo("Export complete", f"Exported {count} contacts.")

    def open_import_wizard() -> None:
        if not selected_list_id.get():
            messagebox.showinfo("Import CSV", "Create or select a contact list before importing.")
            return
        ImportWizard(frame, app, selected_list_id.get(), on_complete=lambda list_id: refresh_lists(list_id))

    def sort_column(column: str) -> None:
        if column == "id":
            return
        sort_column_name = "is_suppressed" if column == "suppressed_label" else column
        if sort_state["column"] == sort_column_name:
            sort_state["descending"] = not sort_state["descending"]
        else:
            sort_state["column"] = sort_column_name
            sort_state["descending"] = False
        refresh_contacts()

    for column in CONTACT_COLUMNS:
        contact_tree.heading(column, command=lambda col=column: sort_column(col))
    list_tree.bind("<<TreeviewSelect>>", list_selected)
    contact_tree.bind("<Double-1>", open_selected_contact)
    search_var.trace_add("write", lambda *_: refresh_contacts())
    verification_var.trace_add("write", lambda *_: refresh_contacts())
    suppressed_var.trace_add("write", lambda *_: refresh_contacts())
    refresh_lists()


class ContactEditor:
    def __init__(self, parent: tk.Widget, app, list_id: int, contact_id: int = 0, on_save=None) -> None:
        self.app = app
        self.list_id = list_id
        self.contact_id = contact_id
        self.on_save = on_save
        self.window = tk.Toplevel(parent)
        self.window.title("Edit Contact" if contact_id else "New Contact")
        self.window.geometry("620x520")
        self.vars = {field: tk.StringVar() for field in [
            "email", "first_name", "last_name", "company", "phone", "address", "city", "state", "zip",
            "country", "custom1", "custom2", "custom3", "verification_status", "last_sent_at", "last_verified_at"
        ]}
        self.suppressed = tk.BooleanVar(value=False)
        self._build()
        if contact_id:
            self._load(contact_id)

    def _build(self) -> None:
        body = ttk.Frame(self.window, padding=16)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(3, weight=1)
        fields = [
            ("email", "Email", 0, 0),
            ("first_name", "First name", 1, 0),
            ("last_name", "Last name", 1, 2),
            ("company", "Company", 2, 0),
            ("phone", "Phone", 2, 2),
            ("address", "Address", 3, 0),
            ("city", "City", 4, 0),
            ("state", "State", 4, 2),
            ("zip", "Zip", 5, 0),
            ("country", "Country", 5, 2),
            ("custom1", "Custom1", 6, 0),
            ("custom2", "Custom2", 6, 2),
            ("custom3", "Custom3", 7, 0),
            ("last_sent_at", "Last sent", 8, 0),
            ("last_verified_at", "Last verified", 8, 2),
        ]
        for key, label, row, col in fields:
            ttk.Label(body, text=label).grid(row=row, column=col, sticky="w", pady=5, padx=(0, 8))
            ttk.Entry(body, textvariable=self.vars[key]).grid(row=row, column=col + 1, sticky="ew", pady=5)
        ttk.Label(body, text="Verification").grid(row=7, column=2, sticky="w", pady=5, padx=(8, 8))
        ttk.Combobox(
            body,
            textvariable=self.vars["verification_status"],
            values=["Deliverable", "Risky", "Unknown", "Undeliverable"],
            state="readonly",
        ).grid(row=7, column=3, sticky="ew", pady=5)
        ttk.Checkbutton(body, text="Suppressed", variable=self.suppressed).grid(row=9, column=1, sticky="w", pady=8)
        buttons = ttk.Frame(body)
        buttons.grid(row=10, column=0, columnspan=4, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Save Contact", command=self.save).pack(side="left", padx=5)
        if self.contact_id:
            ttk.Button(buttons, text="Delete", command=self.delete).pack(side="left", padx=5)
        ttk.Button(buttons, text="Cancel", command=self.window.destroy).pack(side="left", padx=5)

    def _load(self, contact_id: int) -> None:
        contact = self.app.contact_service.get_contact(contact_id)
        if not contact:
            return
        self.list_id = int(contact["list_id"])
        for key, var in self.vars.items():
            var.set(str(contact.get(key) or ""))
        self.suppressed.set(bool(contact.get("suppressed")))

    def save(self) -> None:
        try:
            contact_id = self.app.contact_service.save_contact(
                self.list_id,
                {key: var.get() for key, var in self.vars.items()},
                self.contact_id or None,
            )
            if self.suppressed.get():
                self.app.contact_service.suppress_contacts([contact_id])
            else:
                self.app.contact_service.unsuppress_contacts([contact_id])
            if self.on_save:
                self.on_save()
            self.window.destroy()
        except Exception as exc:
            messagebox.showerror("Contact", str(exc), parent=self.window)

    def delete(self) -> None:
        if messagebox.askyesno("Delete contact", "Delete this contact?", parent=self.window):
            self.app.contact_service.delete_contacts([self.contact_id])
            if self.on_save:
                self.on_save()
            self.window.destroy()


class ImportWizard:
    def __init__(self, parent: tk.Widget, app, list_id: int, on_complete=None) -> None:
        self.app = app
        self.list_id = list_id
        self.on_complete = on_complete
        self.window = tk.Toplevel(parent)
        self.window.title("CSV Import Wizard")
        self.window.geometry("980x650")
        self.path = tk.StringVar()
        self.headers: list[str] = []
        self.rows: list[dict[str, str]] = []
        self.mapping = {field: tk.StringVar() for field in SUPPORTED_FIELDS}
        self.options = {
            "skip_duplicates": tk.BooleanVar(value=True),
            "update_existing": tk.BooleanVar(value=False),
            "ignore_blank_emails": tk.BooleanVar(value=True),
            "validate_email_format": tk.BooleanVar(value=True),
            "suppress_invalid_emails": tk.BooleanVar(value=False),
        }
        self.summary_text = tk.StringVar(value="Select a CSV file to begin.")
        self._build()

    def _build(self) -> None:
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=14, pady=14)
        self.file_tab = ttk.Frame(notebook, padding=12)
        self.preview_tab = ttk.Frame(notebook, padding=12)
        self.map_tab = ttk.Frame(notebook, padding=12)
        self.summary_tab = ttk.Frame(notebook, padding=12)
        notebook.add(self.file_tab, text="1. File")
        notebook.add(self.preview_tab, text="2. Preview")
        notebook.add(self.map_tab, text="3. Map")
        notebook.add(self.summary_tab, text="4. Summary")

        self.file_tab.columnconfigure(1, weight=1)
        ttk.Label(self.file_tab, text="CSV file").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(self.file_tab, textvariable=self.path).grid(row=0, column=1, sticky="ew", pady=6, padx=8)
        ttk.Button(self.file_tab, text="Browse", command=self.browse).grid(row=0, column=2, pady=6)
        ttk.Label(self.file_tab, textvariable=self.summary_text, style="Muted.TLabel").grid(row=1, column=1, sticky="w", pady=10)

        self.preview_table = build_tree(self.preview_tab, ("row",), headings=("Preview",), height=18)

        map_frame = ttk.Frame(self.map_tab)
        map_frame.pack(fill="both", expand=True)
        for idx, field in enumerate(SUPPORTED_FIELDS):
            row = idx // 2
            col = (idx % 2) * 2
            label = f"{field} *" if field == "email" else field
            ttk.Label(map_frame, text=label).grid(row=row, column=col, sticky="w", pady=5, padx=(0, 8))
            ttk.Combobox(map_frame, textvariable=self.mapping[field], values=self.headers, state="readonly", width=28).grid(
                row=row, column=col + 1, sticky="ew", pady=5, padx=(0, 16)
            )
        options_frame = ttk.LabelFrame(self.map_tab, text="Import Options", padding=10)
        options_frame.pack(fill="x", pady=(14, 0))
        for idx, (key, var) in enumerate(self.options.items()):
            ttk.Checkbutton(options_frame, text=key.replace("_", " ").title(), variable=var).grid(row=idx // 3, column=idx % 3, sticky="w", padx=8, pady=4)

        ttk.Label(self.summary_tab, textvariable=self.summary_text, justify="left").pack(anchor="nw")
        buttons = ttk.Frame(self.window)
        buttons.pack(fill="x", padx=14, pady=(0, 14))
        ttk.Button(buttons, text="Import Contacts", command=self.import_now).pack(side="right")
        ttk.Button(buttons, text="Close", command=self.window.destroy).pack(side="right", padx=8)

    def browse(self) -> None:
        path = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")], parent=self.window)
        if not path:
            return
        self.path.set(path)
        preview = self.app.import_service.preview_csv(path)
        self.headers = preview["headers"]
        self.rows = preview["rows"]
        self.mapping["email"].set(preview["email_column"])
        self._refresh_mapping_combos()
        self._refresh_preview()
        self.summary_text.set(f"Loaded {len(self.rows)} preview rows. Map columns, then import.")

    def import_now(self) -> None:
        if not self.path.get():
            messagebox.showerror("Import CSV", "Select a CSV file first.", parent=self.window)
            return
        try:
            summary = self.app.import_service.import_into_list(
                self.path.get(),
                self.list_id,
                {field: var.get() for field, var in self.mapping.items()},
                {key: var.get() for key, var in self.options.items()},
            )
            self.summary_text.set("\n".join(f"{key}: {value}" for key, value in summary.items()))
            if self.on_complete:
                self.on_complete(self.list_id)
            messagebox.showinfo("Import complete", f"Inserted {summary['inserted']} contacts. Duplicates: {summary['duplicates']}.", parent=self.window)
        except Exception as exc:
            messagebox.showerror("Import CSV", str(exc), parent=self.window)

    def _refresh_mapping_combos(self) -> None:
        for child in self.map_tab.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, ttk.Combobox):
                    widget.configure(values=self.headers)

    def _refresh_preview(self) -> None:
        _clear_tree(self.preview_table)
        self.preview_table.configure(columns=tuple(["row", *self.headers]))
        for column in ["row", *self.headers]:
            self.preview_table.heading(column, text=column)
            self.preview_table.column(column, width=120, stretch=True)
        for idx, row in enumerate(self.rows, start=1):
            self.preview_table.insert("", "end", values=[idx, *[row.get(header, "") for header in self.headers]])


def choose_target_list(parent: tk.Widget, app, current_list_id: int) -> int:
    choices = [row for row in app.contact_list_service.list_lists() if int(row["id"]) != current_list_id]
    if not choices:
        messagebox.showinfo("Choose list", "Create another contact list first.", parent=parent)
        return 0
    window = tk.Toplevel(parent)
    window.title("Choose Target List")
    window.geometry("380x140")
    selected = tk.StringVar(value=f"{choices[0]['id']} - {choices[0]['name']}")
    result = tk.IntVar(value=0)
    ttk.Label(window, text="Target list").pack(anchor="w", padx=14, pady=(14, 4))
    ttk.Combobox(window, textvariable=selected, values=[f"{row['id']} - {row['name']}" for row in choices], state="readonly").pack(
        fill="x", padx=14
    )
    buttons = ttk.Frame(window)
    buttons.pack(anchor="e", padx=14, pady=14)
    ttk.Button(buttons, text="Cancel", command=window.destroy).pack(side="left", padx=4)
    ttk.Button(buttons, text="Use List", command=lambda: (result.set(int(selected.get().split(" - ", 1)[0])), window.destroy())).pack(side="left")
    window.transient(parent)
    window.grab_set()
    parent.wait_window(window)
    return result.get()


def _build_stats(parent: ttk.Frame) -> dict[str, ttk.Label]:
    labels = {}
    for idx, key in enumerate(["total", "Deliverable", "Risky", "Unknown", "Undeliverable", "suppressed", "duplicates"]):
        card = ttk.Frame(parent, padding=12, style="Card.TFrame")
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 7, 0))
        value = ttk.Label(card, text="0", font=("Segoe UI Semibold", 18), style="PanelTitle.TLabel")
        value.pack(anchor="w")
        ttk.Label(card, text=key, style="CardMuted.TLabel").pack(anchor="w")
        labels[key] = value
        parent.columnconfigure(idx, weight=1)
    return labels


def _update_stats(labels: dict[str, ttk.Label], stats: dict[str, int]) -> None:
    for key, label in labels.items():
        label.configure(text=str(stats.get(key, 0)))


def _clear_tree(tree: ttk.Treeview) -> None:
    for item in tree.get_children():
        tree.delete(item)
