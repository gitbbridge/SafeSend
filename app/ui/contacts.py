import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import checkbox as ctk_checkbox
from app.design_system.customtkinter_adapter import combobox as ctk_combobox
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.customtkinter_adapter import toplevel as ctk_toplevel
from app.design_system.dialogs import choose_option, prompt_fields
from app.design_system import components as ds
from app.services.import_service import SUPPORTED_FIELDS
from app.ui.shared import build_tree, clear_tree, icon_text, insert_empty_row, insert_table_row, section

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
    theme = app.theme

    list_panel = ctk_frame(frame, theme, "card")
    list_panel.grid(row=2, column=0, rowspan=3, sticky="nsew", padx=(theme.spacing.page_padding, 12))
    list_panel.columnconfigure(0, weight=1)
    list_panel.rowconfigure(2, weight=1)
    ctk_label(list_panel, theme, "Contact Lists", "panel_title", "card").grid(row=0, column=0, sticky="w", padx=16, pady=(16, 4))
    list_toolbar = ctk_frame(list_panel, theme, "surface", corner_radius=10, border_width=0)
    list_toolbar.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
    list_toolbar.columnconfigure((0, 1), weight=1)

    list_tree = build_tree(
        list_panel,
        ("id", "name", "total_contacts", "last_imported_at", "last_verified_at"),
        headings=("ID", "List", "Count", "Imported", "Verified"),
        height=12,
    )
    list_tree.column("id", width=36, stretch=False)
    list_tree.column("total_contacts", width=62, stretch=False)

    ctk_button(list_toolbar, theme, icon_text("new", "New"), command=lambda: edit_list(), width=128).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=4)
    ctk_button(list_toolbar, theme, icon_text("edit", "Rename"), command=lambda: edit_list(selected_list_id.get()), width=128).grid(row=0, column=1, sticky="ew", pady=4)
    ctk_button(list_toolbar, theme, icon_text("duplicate", "Duplicate"), command=lambda: duplicate_list(), width=128).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=4)
    ctk_button(list_toolbar, theme, icon_text("archive", "Archive"), command=lambda: archive_list(), width=128).grid(row=1, column=1, sticky="ew", pady=4)
    ctk_button(list_toolbar, theme, icon_text("delete", "Delete"), command=lambda: delete_list(), variant="danger", width=260).grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)

    stats_panel = ctk_frame(frame, theme, "background")
    stats_panel.grid(row=2, column=1, sticky="ew", padx=(0, theme.spacing.page_padding), pady=(0, 10))
    stat_labels = _build_stats(stats_panel, theme)

    toolbar = ctk_frame(frame, theme, "toolbar")
    toolbar.grid(row=3, column=1, sticky="ew", padx=(0, theme.spacing.page_padding), pady=(0, 10))
    toolbar.columnconfigure(1, weight=1)
    ctk_label(toolbar, theme, "Search", "caption", "card").grid(row=0, column=0, sticky="w", padx=(12, 8), pady=(12, 6))
    search_entry = ctk_entry(toolbar, theme, search_var, placeholder_text="Name, company, email, or state")
    search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(12, 6))
    ctk_label(toolbar, theme, "Verification", "caption", "card").grid(row=0, column=2, sticky="w", padx=(0, 8), pady=(12, 6))
    ctk_combobox(toolbar, theme, verification_var, ["All", "Deliverable", "Risky", "Unknown", "Undeliverable"], width=150).grid(row=0, column=3, sticky="w", padx=(0, 8), pady=(12, 6))
    ctk_label(toolbar, theme, "Suppression", "caption", "card").grid(row=0, column=4, sticky="w", padx=(0, 8), pady=(12, 6))
    ctk_combobox(toolbar, theme, suppressed_var, ["All", "Suppressed", "Not suppressed"], width=170).grid(row=0, column=5, sticky="w", padx=(0, 12), pady=(12, 6))

    actions = ctk_frame(toolbar, theme, "surface", corner_radius=10, border_width=0)
    actions.grid(row=1, column=0, columnspan=6, sticky="ew", padx=12, pady=(4, 12))
    for column in range(5):
        actions.columnconfigure(column, weight=1, uniform="contact_actions")
    action_specs = [
        (0, 0, icon_text("import", "Import CSV"), lambda: open_import_wizard(), "primary", None, 132),
        (0, 1, icon_text("new", "New Contact"), lambda: edit_contact(), "secondary", None, 132),
        (0, 2, "Suppress", lambda: suppress_selected(), "secondary", "suppression", 118),
        (0, 3, "Unsuppress", lambda: unsuppress_selected(), "secondary", "success", 132),
        (0, 4, icon_text("delete", "Delete"), lambda: delete_selected(), "danger", None, 104),
        (1, 0, "Move", lambda: move_or_copy("move"), "secondary", "move", 92),
        (1, 1, "Copy", lambda: move_or_copy("copy"), "secondary", "copy", 92),
        (1, 2, "Export List", lambda: export_contacts("list"), "secondary", "export", 126),
        (1, 3, "Export Filtered", lambda: export_contacts("filtered"), "secondary", "export", 146),
        (1, 4, "Export Selected", lambda: export_contacts("selected"), "secondary", "export", 150),
    ]
    for row, column, text, command, variant, icon, width in action_specs:
        kwargs = {"icon": icon} if icon else {}
        ctk_button(actions, theme, text, command=command, variant=variant, width=width, **kwargs).grid(row=row, column=column, sticky="ew", padx=4, pady=4)

    grid_frame = ctk_frame(frame, theme, "card")
    grid_frame.grid(row=4, column=1, sticky="nsew", padx=(0, theme.spacing.page_padding))
    contact_tree = build_tree(
        grid_frame,
        CONTACT_COLUMNS,
        headings=(
            "ID",
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
        clear_tree(list_tree)
        for row in rows:
            item_id = insert_table_row(
                list_tree,
                [
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
        if not rows:
            insert_empty_row(list_tree, "No contact lists yet. Create a list to begin.", ("id", "name", "total_contacts", "last_imported_at", "last_verified_at"))
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
        clear_tree(contact_tree)
        for contact in current_contacts:
            row = dict(contact)
            row["suppressed_label"] = "Yes" if row.get("suppressed") else "No"
            insert_table_row(contact_tree, [row.get(column, "") or "" for column in CONTACT_COLUMNS])
        if not current_contacts:
            insert_empty_row(contact_tree, "No contacts imported yet. Import a CSV to begin.", CONTACT_COLUMNS)
        _update_stats(stat_labels, app.contact_list_service.stats(selected_list_id.get() or None))
        app.status.set(f"{len(current_contacts)} contacts shown")

    def list_selected(_event=None) -> None:
        selection = list_tree.selection()
        if not selection:
            return
        values = list_tree.item(selection[0], "values")
        try:
            selected_list_id.set(int(values[0]))
        except (TypeError, ValueError):
            return
        refresh_contacts()

    def edit_list(list_id: int = 0) -> None:
        existing = app.contact_list_service.get_list(list_id) if list_id else None
        result = _contact_list_dialog(frame, theme, "Rename Contact List" if existing else "New Contact List", (existing or {}).get("name", ""), (existing or {}).get("notes", ""))
        if result is None:
            return
        name, notes = result
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
            try:
                if values:
                    ids.append(int(values[0]))
            except (TypeError, ValueError):
                continue
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

        def worker(handle):
            def report(current: int, total: int) -> None:
                if handle.cancel_requested():
                    raise RuntimeError("Export cancelled safely.")
                handle.update("Exporting contacts", current=current, total=total)

            return app.export_service.export_contacts(
                contacts,
                path,
                progress_callback=report,
            )

        app.run_background_operation(
            "Exporting contacts",
            worker,
            detail="Exporting contacts...",
            total=len(contacts),
            on_success=lambda count: messagebox.showinfo("Export complete", f"Exported {count} contacts."),
        )

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
        self.theme = app.theme
        self.window = ctk_toplevel(parent, "Edit Contact" if contact_id else "New Contact", "620x520")
        self.vars = {field: tk.StringVar() for field in [
            "email", "first_name", "last_name", "company", "phone", "address", "city", "state", "zip",
            "country", "custom1", "custom2", "custom3", "verification_status", "last_sent_at", "last_verified_at"
        ]}
        self.suppressed = tk.BooleanVar(value=False)
        self._build()
        if contact_id:
            self._load(contact_id)

    def _build(self) -> None:
        body = ctk_frame(self.window, self.theme, "background")
        body.pack(fill="both", expand=True)
        card = ctk_frame(body, self.theme, "card")
        card.pack(fill="both", expand=True, padx=self.theme.spacing.page_padding, pady=self.theme.spacing.page_padding)
        card.columnconfigure(1, weight=1)
        card.columnconfigure(3, weight=1)
        ctk_label(card, self.theme, "Contact Details", "panel_title", "card").grid(row=0, column=0, columnspan=4, sticky="w", padx=18, pady=(18, 8))
        fields = [
            ("email", "Email", 1, 0),
            ("first_name", "First name", 2, 0),
            ("last_name", "Last name", 2, 2),
            ("company", "Company", 3, 0),
            ("phone", "Phone", 3, 2),
            ("address", "Address", 4, 0),
            ("city", "City", 5, 0),
            ("state", "State", 5, 2),
            ("zip", "Zip", 6, 0),
            ("country", "Country", 6, 2),
            ("custom1", "Custom1", 7, 0),
            ("custom2", "Custom2", 7, 2),
            ("custom3", "Custom3", 8, 0),
            ("last_sent_at", "Last sent", 9, 0),
            ("last_verified_at", "Last verified", 9, 2),
        ]
        for key, label, row, col in fields:
            ctk_label(card, self.theme, label, "caption", "card").grid(row=row, column=col, sticky="w", pady=6, padx=(18 if col == 0 else 10, 8))
            ctk_entry(card, self.theme, self.vars[key]).grid(row=row, column=col + 1, sticky="ew", pady=6, padx=(0, 18))
        ctk_label(card, self.theme, "Verification", "caption", "card").grid(row=8, column=2, sticky="w", pady=6, padx=(10, 8))
        ctk_combobox(card, self.theme, self.vars["verification_status"], ["Deliverable", "Risky", "Unknown", "Undeliverable"]).grid(row=8, column=3, sticky="ew", pady=6, padx=(0, 18))
        ctk_checkbox(card, self.theme, "Suppressed", self.suppressed).grid(row=10, column=1, sticky="w", pady=8)
        buttons = ctk_frame(card, self.theme, "toolbar")
        buttons.grid(row=11, column=0, columnspan=4, sticky="e", padx=18, pady=(16, 18))
        ctk_button(buttons, self.theme, "Save Contact", command=self.save, variant="primary", icon="save", width=140).pack(side="left", padx=(12, 4), pady=10)
        if self.contact_id:
            ctk_button(buttons, self.theme, "Delete", command=self.delete, variant="danger", icon="delete", width=112).pack(side="left", padx=4, pady=10)
        ctk_button(buttons, self.theme, "Cancel", command=self.window.destroy, icon="close", width=112).pack(side="left", padx=(4, 12), pady=10)

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
        self.theme = app.theme
        self.window = ctk_toplevel(parent, "CSV Import Wizard", "980x650")
        self.path = tk.StringVar()
        self.headers: list[str] = []
        self.rows: list[dict[str, str]] = []
        self.mapping = {field: tk.StringVar() for field in SUPPORTED_FIELDS}
        self.mapping_widgets: list[tk.Widget] = []
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
        shell = ctk_frame(self.window, self.theme, "background")
        shell.pack(fill="both", expand=True, padx=18, pady=18)
        notebook = ctk.CTkTabview(
            shell,
            fg_color=self.theme.palette.surface,
            segmented_button_fg_color=self.theme.palette.surface_alt,
            segmented_button_selected_color=self.theme.palette.primary,
            segmented_button_selected_hover_color=self.theme.palette.primary_dark,
            segmented_button_unselected_color=self.theme.palette.button_background,
            segmented_button_unselected_hover_color=self.theme.palette.button_hover,
            text_color=self.theme.palette.text,
        )
        notebook.pack(fill="both", expand=True)
        self.file_tab = notebook.add("1. File")
        self.preview_tab = notebook.add("2. Preview")
        self.map_tab = notebook.add("3. Map")
        self.summary_tab = notebook.add("4. Summary")

        self.file_tab.columnconfigure(1, weight=1)
        ctk_label(self.file_tab, self.theme, "CSV file", "caption").grid(row=0, column=0, sticky="w", padx=(14, 8), pady=14)
        ctk_entry(self.file_tab, self.theme, self.path).grid(row=0, column=1, sticky="ew", pady=14, padx=8)
        ctk_button(self.file_tab, self.theme, "Browse", command=self.browse, icon="import", width=122).grid(row=0, column=2, padx=(0, 14), pady=14)
        ctk_label(self.file_tab, self.theme, "", "caption", textvariable=self.summary_text).grid(row=1, column=1, sticky="w", pady=10)

        self.preview_table = build_tree(self.preview_tab, ("row",), headings=("Preview",), height=18)

        map_frame = ctk_frame(self.map_tab, self.theme, "card")
        map_frame.pack(fill="both", expand=True, padx=14, pady=14)
        for idx, field in enumerate(SUPPORTED_FIELDS):
            row = idx // 2
            col = (idx % 2) * 2
            label = f"{field} *" if field == "email" else field
            ctk_label(map_frame, self.theme, label, "caption", "card").grid(row=row, column=col, sticky="w", pady=6, padx=(14 if col == 0 else 8, 8))
            combo = ctk_combobox(map_frame, self.theme, self.mapping[field], self.headers, width=220)
            combo.grid(row=row, column=col + 1, sticky="ew", pady=6, padx=(0, 16))
            self.mapping_widgets.append(combo)
        options_frame = ctk_frame(self.map_tab, self.theme, "card")
        options_frame.pack(fill="x", padx=14, pady=(0, 14))
        ctk_label(options_frame, self.theme, "Import Options", "panel_title", "card").grid(row=0, column=0, columnspan=3, sticky="w", padx=14, pady=(14, 4))
        for idx, (key, var) in enumerate(self.options.items()):
            ctk_checkbox(options_frame, self.theme, key.replace("_", " ").title(), var).grid(row=1 + idx // 3, column=idx % 3, sticky="w", padx=14, pady=6)

        ctk_label(self.summary_tab, self.theme, "", "body", textvariable=self.summary_text, justify="left").pack(anchor="nw", padx=14, pady=14)
        buttons = ctk_frame(shell, self.theme, "toolbar")
        buttons.pack(fill="x", pady=(14, 0))
        ctk_button(buttons, self.theme, "Import Contacts", command=self.import_now, variant="primary", icon="import", width=164).pack(side="right", padx=(4, 12), pady=10)
        ctk_button(buttons, self.theme, "Close", command=self.window.destroy, icon="close", width=112).pack(side="right", padx=4, pady=10)

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
        self.summary_text.set("Importing contacts...")

        def worker(handle):
            def report(current: int, total: int) -> None:
                if handle.cancel_requested():
                    raise RuntimeError("Import cancelled safely.")
                handle.update("Importing contacts", current=current, total=total)

            return self.app.import_service.import_into_list(
                self.path.get(),
                self.list_id,
                {field: var.get() for field, var in self.mapping.items()},
                {key: var.get() for key, var in self.options.items()},
                progress_callback=report,
            )

        def done(summary) -> None:
            self.summary_text.set("\n".join(f"{key}: {value}" for key, value in summary.items()))
            if self.on_complete:
                self.on_complete(self.list_id)
            messagebox.showinfo("Import complete", f"Inserted {summary['inserted']} contacts. Duplicates: {summary['duplicates']}.", parent=self.window)

        self.app.run_background_operation(
            "Importing contacts",
            worker,
            detail="Importing contacts...",
            on_success=done,
            on_error=lambda exc: messagebox.showerror("Import CSV", str(exc), parent=self.window),
        )

    def _refresh_mapping_combos(self) -> None:
        for widget in self.mapping_widgets:
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
    options = [f"{row['id']} - {row['name']}" for row in choices]
    selected = choose_option(parent, "Choose Target List", "Select where the selected contacts should go.", options, submit_text="Use List")
    return int(selected.split(" - ", 1)[0]) if selected else 0


def _contact_list_dialog(parent: tk.Widget, theme, title: str, initial_name: str = "", initial_notes: str = "") -> tuple[str, str] | None:
    result = prompt_fields(
        parent,
        title,
        "Enter list details. Notes are internal only and help keep imports organized.",
        (
            ("name", "List name", initial_name),
            ("notes", "Notes/internal label", initial_notes),
        ),
        submit_text="Save List",
    )
    return (result["name"], result["notes"]) if result else None


def _build_stats(parent: tk.Widget, theme) -> dict[str, tk.Widget]:
    labels = {}
    for idx, key in enumerate(["total", "Deliverable", "Risky", "Unknown", "Undeliverable", "suppressed", "duplicates"]):
        level = {
            "Deliverable": "success",
            "Risky": "warning",
            "Undeliverable": "danger",
            "suppressed": "danger",
        }.get(key, "default")
        card = ds.MetricCard(parent, key, "0", theme=theme, level=level)
        row = idx // 4
        column = idx % 4
        card.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0), pady=(0 if row == 0 else 8, 0))
        labels[key] = card.value_label
    for column in range(4):
        parent.columnconfigure(column, weight=1)
    return labels


def _update_stats(labels: dict[str, tk.Widget], stats: dict[str, int]) -> None:
    for key, label in labels.items():
        label.configure(text=str(stats.get(key, 0)))


def _clear_tree(tree: ttk.Treeview) -> None:
    for item in tree.get_children():
        tree.delete(item)
