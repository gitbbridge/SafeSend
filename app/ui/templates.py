import re
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox

import customtkinter as ctk

from app.design_system import components as ds
from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import combobox as ctk_combobox
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.customtkinter_adapter import textbox as ctk_textbox
from app.ui.email_authoring import MERGE_TAGS
from app.ui.shared import build_tree, clear_tree, insert_empty_row, insert_table_row


TABLE_COLUMNS = ("favorite", "name", "category", "subject", "status", "updated_at", "last_used_at", "actions")
SORTS = {
    "Newest": "updated_at DESC",
    "Oldest": "updated_at ASC",
    "Recently Used": "last_used_at DESC",
    "Name A-Z": "name ASC",
    "Usage Count": "times_used DESC",
}
FOLDERS = ["All Templates", "Favorites", "Recently Used", "Drafts", "Archived", "Sales", "Events", "Follow-Up", "Introductions", "Custom"]
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
IMG_RE = re.compile(r"<img\b", re.I)


def build(parent: tk.Widget, app) -> None:
    theme = app.theme
    root = ctk_frame(parent, theme, "background")
    root.pack(fill="both", expand=True)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    state = {
        "mode": "library",
        "selected_id": None,
        "current_rows": [],
        "folder": "All Templates",
        "editor_id": None,
        "editor_dirty": False,
        "placeholder_visible": False,
        "last_autosaved": "Not yet",
        "autosave_job": None,
        "autosave_active": False,
    }
    filters = {
        "search": tk.StringVar(),
        "category": tk.StringVar(value="All"),
        "status": tk.StringVar(value="All"),
        "sort": tk.StringVar(value="Newest"),
    }

    def clear_root() -> None:
        job = state.get("autosave_job")
        if job:
            try:
                root.after_cancel(job)
            except tk.TclError:
                pass
            state["autosave_job"] = None
        state["autosave_active"] = False
        for child in root.winfo_children():
            child.destroy()

    def show_library() -> None:
        state["mode"] = "library"
        state["editor_id"] = None
        state["editor_dirty"] = False
        clear_root()
        _build_library(root, app, state, filters, show_editor, refresh_library_actions)

    def show_editor(template_id: int | None = None) -> None:
        state["mode"] = "editor"
        state["editor_id"] = template_id
        state["editor_dirty"] = False
        clear_root()
        _build_editor(root, app, state, show_library, use_in_compose)

    def use_in_compose(template_id: int) -> None:
        template = app.template_service.get_template(template_id)
        if not template:
            messagebox.showerror("Use In Compose", "Template was not found.", parent=root)
            return
        app.template_service.increment_used(template_id)
        app.navigate("Compose")
        compose_host = app.page_cache.get("Compose")
        loader = getattr(compose_host, "_safesend_load_template", None)
        if callable(loader):
            loader(template)
            app.status.set(f"Loaded {template['name']} into Compose as a working copy.")
        else:
            app.status.set("Opened Compose. Use Template is available from the Compose header.")

    def refresh_library_actions() -> None:
        if state["mode"] == "library":
            show_library()

    for variable in filters.values():
        variable.trace_add("write", lambda *_: refresh_library_actions())
    show_library()


def _build_library(parent: tk.Widget, app, state: dict, filters: dict, show_editor, refresh_library) -> None:
    theme = app.theme
    palette = theme.palette
    space = theme.spacing
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(2, weight=1)

    header = ctk_frame(parent, theme, "background")
    header.grid(row=0, column=0, sticky="ew", padx=space.page_padding, pady=(16, 8))
    header.columnconfigure(0, weight=1)
    title_row = ctk_frame(header, theme, "background")
    title_row.grid(row=0, column=0, sticky="w")
    ds.icon_label(title_row, "templates", theme=theme, text_color=palette.primary, size=28, surface="transparent").pack(side="left", padx=(0, space.sm))
    ctk_label(title_row, theme, "Templates", role="page_title", variant="background").pack(side="left")
    title_actions = ctk_frame(title_row, theme, "background")
    title_actions.pack(side="left", padx=(28, 0))
    ctk_button(title_actions, theme, "Import", command=lambda: _import_template(parent, app, show_editor), icon="import", width=92, height=34).pack(side="left", padx=(0, 6))
    ctk_button(title_actions, theme, "Export", command=lambda: _export_selected(parent, app, state), icon="export", width=92, height=34).pack(side="left", padx=(0, 6))
    ctk_button(title_actions, theme, "New Template", command=lambda: show_editor(None), variant="primary", icon="new", width=138, height=34).pack(side="left")
    ctk_label(
        header,
        theme,
        "Create, organize, preview, and reuse approved campaign templates.",
        role="caption",
        variant="background",
        text_color=palette.text_muted,
    ).grid(row=1, column=0, sticky="w", pady=(2, 0))

    command = ctk_frame(parent, theme, "card", fg_color=palette.surface)
    command.grid(row=1, column=0, sticky="ew", padx=space.page_padding, pady=(0, space.md))
    command.columnconfigure(0, weight=1)

    filters_row = ctk_frame(command, theme, "card", fg_color="transparent", border_width=0)
    filters_row.grid(row=0, column=0, sticky="ew", padx=space.md, pady=(space.md, space.xs))
    filters_row.columnconfigure(0, weight=1)
    ctk_entry(filters_row, theme, filters["search"], placeholder_text="Search by template, subject, category...", width=330).grid(row=0, column=0, sticky="ew", padx=(0, 8))
    ds.select_dropdown_button(filters_row, filters["category"], ["All", *app.template_service.categories()], theme=theme, width=146).grid(row=0, column=1, padx=4)
    ds.select_dropdown_button(filters_row, filters["status"], ["All", "Draft", "Active", "Archived"], theme=theme, width=120).grid(row=0, column=2, padx=4)
    ds.select_dropdown_button(filters_row, filters["sort"], list(SORTS), theme=theme, width=136).grid(row=0, column=3, padx=4)
    ctk_button(filters_row, theme, "Clear", command=lambda: _clear_filters(filters), icon="clear", width=82, height=34).grid(row=0, column=4, padx=(6, 0))

    selected_actions = ctk_frame(command, theme, "card", fg_color="transparent", border_width=0)
    selected_actions.grid(row=1, column=0, sticky="ew", padx=space.md, pady=(0, space.md))
    ctk_button(selected_actions, theme, "Open", command=lambda: _open_selected(parent, state, show_editor), icon="edit", width=86, height=32).pack(side="left", padx=(0, 6))
    ctk_button(selected_actions, theme, "Duplicate", command=lambda: _duplicate_selected(parent, app, state, refresh_library), icon="duplicate", width=106, height=32).pack(side="left", padx=6)
    ctk_button(selected_actions, theme, "Archive", command=lambda: _archive_selected(parent, app, state, refresh_library), icon="archive", width=96, height=32).pack(side="left", padx=6)
    ctk_button(selected_actions, theme, "Delete", command=lambda: _delete_selected(parent, app, state, refresh_library), icon="delete", variant="danger", width=90, height=32).pack(side="left", padx=6)
    ctk_button(selected_actions, theme, "Use In Compose", command=lambda: _use_selected_in_compose(parent, app, state), icon="compose", variant="success", width=142, height=32).pack(side="left", padx=6)

    workspace = ctk_frame(parent, theme, "background")
    workspace.grid(row=2, column=0, sticky="nsew", padx=space.page_padding, pady=(0, space.page_padding))
    workspace.columnconfigure(1, weight=1)
    workspace.columnconfigure(2, weight=0)
    workspace.rowconfigure(0, weight=1)

    folders = ctk.CTkFrame(workspace, fg_color=palette.surface, corner_radius=4, border_width=1, border_color=palette.border_soft, width=176)
    folders.grid(row=0, column=0, sticky="nsw", padx=(0, space.md))
    folders.grid_propagate(False)
    ctk_label(folders, theme, "Folders", role="panel_title", variant="card").pack(anchor="w", padx=space.md, pady=(space.md, space.sm))
    counts = _folder_counts(app.template_service.list_templates("", include_archived=True))
    for folder in FOLDERS:
        selected = folder == state["folder"]
        row = ctk.CTkButton(
            folders,
            text=f"{folder}  {counts.get(folder, 0)}",
            command=lambda value=folder: _set_folder(state, value, refresh_library),
            height=32,
            corner_radius=4,
            fg_color=palette.selection if selected else "transparent",
            hover_color=palette.hover,
            text_color=palette.primary if selected else palette.text,
            font=(theme.typography.family, 10),
            anchor="w",
        )
        row.pack(fill="x", padx=space.sm, pady=1)

    rows = _filtered_rows(app, state, filters)
    state["current_rows"] = rows
    row_ids = {int(row["id"]) for row in rows}
    if rows and state.get("selected_id") not in row_ids:
        state["selected_id"] = int(rows[0]["id"])
    elif not rows:
        state["selected_id"] = None

    library = ctk.CTkFrame(workspace, fg_color=palette.surface, corner_radius=4, border_width=1, border_color=palette.border_soft)
    library.grid(row=0, column=1, sticky="nsew", padx=(0, space.md))
    library.columnconfigure(0, weight=1)
    library.rowconfigure(1, weight=1)
    library_header = ctk_frame(library, theme, "card", fg_color=palette.surface, border_width=0)
    library_header.grid(row=0, column=0, sticky="ew", padx=space.md, pady=(space.md, space.sm))
    library_header.columnconfigure(0, weight=1)
    ctk_label(library_header, theme, "Template Library", role="panel_title", variant="card").grid(row=0, column=0, sticky="w")
    ctk_label(
        library_header,
        theme,
        f"{len(rows)} template{'s' if len(rows) != 1 else ''} in {state['folder']}",
        role="caption",
        variant="card",
        text_color=palette.text_muted,
    ).grid(row=1, column=0, sticky="w", pady=(2, 0))
    _library_summary(library_header, theme, rows).grid(row=0, column=1, rowspan=2, sticky="e")

    list_body = ctk_frame(library, theme, "card", fg_color=palette.surface, border_width=0)
    list_body.grid(row=1, column=0, sticky="nsew", padx=space.md, pady=(0, space.md))
    list_body.columnconfigure(0, weight=1)
    list_body.rowconfigure(0, weight=1)

    inspector = ctk.CTkFrame(workspace, fg_color=palette.surface, corner_radius=4, border_width=1, border_color=palette.border_soft, width=292)
    inspector.grid(row=0, column=2, sticky="nsew")
    inspector.grid_propagate(False)

    def render_inspector(template_id: int | None = None) -> None:
        if template_id:
            state["selected_id"] = template_id
        _render_template_inspector(inspector, app, state, show_editor)

    if not rows:
        empty = ds.EmptyState(
            list_body,
            "No Templates Yet",
            "Create reusable email templates for your campaigns.",
            action_text="Create First Template",
            action_command=lambda: show_editor(None),
            theme=theme,
        )
        empty.grid(row=0, column=0, sticky="nsew", padx=space.md, pady=space.md)
    else:
        _render_card_view(list_body, app, state, rows, show_editor, render_inspector)
    render_inspector()


def _build_editor(parent: tk.Widget, app, state: dict, show_library, use_in_compose) -> None:
    theme = app.theme
    palette = theme.palette
    space = theme.spacing
    values = app.template_service.get_template(state["editor_id"]) if state["editor_id"] else None
    editor_state = {
        "placeholder_visible": False,
    }
    fields = {
        "name": tk.StringVar(value=(values or {}).get("name") or "Untitled Template"),
        "category": tk.StringVar(value=(values or {}).get("category") or "General"),
        "status": tk.StringVar(value=(values or {}).get("status") or "Draft"),
        "favorite": tk.BooleanVar(value=bool((values or {}).get("favorite"))),
        "subject": tk.StringVar(value=(values or {}).get("subject") or ""),
        "preheader": tk.StringVar(value=(values or {}).get("preheader") or ""),
        "from_email": tk.StringVar(value=(values or {}).get("from_email") or ""),
        "from_name": tk.StringVar(value=(values or {}).get("from_name") or ""),
    }
    metrics = {
        "saved": tk.StringVar(value="Saved" if values else "Unsaved"),
        "words": tk.StringVar(value="0 words"),
        "characters": tk.StringVar(value="0 characters"),
        "health": tk.StringVar(value="Health 21%"),
        "autosaved": tk.StringVar(value="Last autosaved: Not yet"),
    }
    panels: dict[str, ctk.CTkFrame | ctk.CTkTextbox] = {}
    tabs_ref: dict[str, ctk.CTkTabview] = {}

    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(1, weight=1)
    header = ctk_frame(parent, theme, "background")
    header.grid(row=0, column=0, sticky="ew", padx=space.page_padding, pady=(16, 10))
    header.columnconfigure(0, weight=1)
    crumb = ctk_frame(header, theme, "background")
    crumb.grid(row=0, column=0, sticky="w")
    ctk_button(crumb, theme, "Templates", command=show_library, variant="ghost", icon="templates", width=98, height=28).pack(side="left")
    ctk_label(crumb, theme, ">", role="caption", variant="background", text_color=palette.text_muted).pack(side="left", padx=space.xs)
    ctk_label(crumb, theme, fields["name"].get() or "Untitled Template", role="page_title", variant="background").pack(side="left")

    actions = ctk_frame(header, theme, "background")
    actions.grid(row=0, column=1, sticky="e")
    action_specs = [
        ("Save", lambda: save(False), "save", "primary", 82),
        ("Save & Close", lambda: save(True), "save", "secondary", 118),
        ("Preview", lambda: set_sidebar_tab("Preview"), "preview", "secondary", 88),
        ("Send Test", lambda: messagebox.showinfo("Send Test", "Test sending will be connected when the sending engine is added.", parent=parent), "send", "secondary", 102),
        ("Duplicate", lambda: duplicate_current(), "duplicate", "secondary", 104),
        ("Delete", lambda: delete_current(), "delete", "danger", 84),
        ("Use In Compose", lambda: use_current(), "compose", "success", 132),
    ]
    for label, command, icon, variant, width in action_specs:
        ctk_button(actions, theme, label, command=command, icon=icon, variant=variant, width=width, height=34).pack(side="left", padx=(6, 0))

    content = ctk_frame(parent, theme, "background")
    content.grid(row=1, column=0, sticky="nsew", padx=space.page_padding, pady=(0, space.page_padding))
    content.columnconfigure(0, weight=3, uniform="template_editor")
    content.columnconfigure(1, weight=1, uniform="template_editor")
    content.rowconfigure(0, weight=1)

    composer = ctk.CTkFrame(content, fg_color=palette.surface, corner_radius=4, border_width=1, border_color=palette.border_soft)
    composer.grid(row=0, column=0, sticky="nsew", padx=(0, space.md))
    composer.columnconfigure(0, weight=1)
    composer.rowconfigure(3, weight=1)

    meta = ctk.CTkFrame(composer, fg_color=palette.surface, corner_radius=0)
    meta.grid(row=0, column=0, sticky="ew", padx=space.md, pady=(space.md, space.xs))
    for col in range(6):
        meta.columnconfigure(col, weight=1 if col in {1, 3, 5} else 0)
    _compact_field(meta, theme, "Template Name", fields["name"], 0, 0)
    _combo_field(meta, theme, "Category", fields["category"], ["General", "Sales", "Follow Up", "Events", "Introductions", "Re-engagement", "Custom"], 0, 2)
    _combo_field(meta, theme, "Status", fields["status"], ["Draft", "Active"], 0, 4)
    ds.checkbox(meta, "Favorite", fields["favorite"], theme=theme).grid(row=1, column=0, sticky="w", padx=(0, space.md), pady=4)

    message = ctk.CTkFrame(composer, fg_color=palette.surface, corner_radius=0)
    message.grid(row=1, column=0, sticky="ew", padx=space.md, pady=(0, space.xs))
    for col in range(4):
        message.columnconfigure(col, weight=1 if col in {1, 3} else 0)
    _compact_field(message, theme, "Subject", fields["subject"], 0, 0)
    _compact_field(message, theme, "Preheader", fields["preheader"], 0, 2)
    _compact_field(message, theme, "From Email", fields["from_email"], 1, 0)
    _compact_field(message, theme, "From Name", fields["from_name"], 1, 2)

    toolbar = _editor_toolbar(composer, theme, insert_html=lambda html: insert_html(html), wrap_selection=lambda b, a: wrap_selection(b, a), pick_color=lambda: pick_color(), insert_signature=lambda: insert_default_signature(), undo=lambda: undo(), redo=lambda: redo())
    toolbar.grid(row=2, column=0, sticky="ew")

    editor_shell = ctk.CTkFrame(composer, fg_color=palette.surface, corner_radius=0)
    editor_shell.grid(row=3, column=0, sticky="nsew", padx=space.md, pady=(space.sm, 0))
    editor_shell.columnconfigure(0, weight=1)
    editor_shell.rowconfigure(0, weight=1)
    editor = ctk_textbox(editor_shell, theme, height=500, wrap="word", undo=True, fg_color=palette.surface)
    editor.grid(row=0, column=0, sticky="nsew")
    editor.insert("1.0", (values or {}).get("html_body") or "Write your template here...")
    if not values:
        editor.configure(text_color=palette.placeholder)
        editor_state["placeholder_visible"] = True

    status = ctk.CTkFrame(composer, fg_color=palette.surface_alt, corner_radius=0, height=34)
    status.grid(row=4, column=0, sticky="ew")
    status.grid_propagate(False)
    for index, key in enumerate(["saved", "words", "characters", "health", "autosaved"]):
        ctk_label(status, theme, textvariable=metrics[key], role="caption", variant="surface", text_color=palette.text_muted).grid(
            row=0,
            column=index,
            sticky="w",
            padx=(space.md if index == 0 else 0, space.md),
            pady=7,
        )

    sidebar = _smart_sidebar(content, theme, panels, tabs_ref)

    def focus_editor(_event=None) -> None:
        if editor_state["placeholder_visible"]:
            editor.delete("1.0", "end")
            editor.configure(text_color=palette.text)
            editor_state["placeholder_visible"] = False

    def body_html() -> str:
        return "" if editor_state["placeholder_visible"] else editor.get("1.0", "end-1c")

    def current_values() -> dict:
        html = body_html()
        return {
            "name": fields["name"].get().strip() or "Untitled Template",
            "category": fields["category"].get() or "General",
            "status": fields["status"].get() or "Draft",
            "favorite": bool(fields["favorite"].get()),
            "subject": fields["subject"].get(),
            "preheader": fields["preheader"].get(),
            "from_name": fields["from_name"].get(),
            "from_email": fields["from_email"].get(),
            "reply_to_email": "",
            "html_body": html,
            "plain_text_body": app.template_service.html_to_text(html),
        }

    def mark_dirty(_event=None) -> None:
        state["editor_dirty"] = True
        metrics["saved"].set("Unsaved")
        refresh_analysis()

    def save(close_after: bool) -> None:
        try:
            template_id = app.template_service.save_template(current_values(), state["editor_id"])
            state["editor_id"] = template_id
            state["editor_dirty"] = False
            metrics["saved"].set("Saved")
            app.status.set("Template saved.")
            if close_after:
                show_library()
        except ValueError as exc:
            messagebox.showerror("Save Template", str(exc), parent=parent)

    def duplicate_current() -> None:
        if state["editor_id"]:
            state["editor_id"] = app.template_service.duplicate_template(state["editor_id"])
            loaded = app.template_service.get_template(state["editor_id"])
            if loaded:
                for key in fields:
                    if key != "favorite":
                        fields[key].set(loaded.get(key) or fields[key].get())
                fields["favorite"].set(bool(loaded.get("favorite")))
            app.status.set("Template duplicated.")
        else:
            save(False)

    def delete_current() -> None:
        if not state["editor_id"]:
            show_library()
            return
        if messagebox.askyesno("Delete Template?", "Deleting this template cannot be undone.\n\nCampaigns already created from this template will not be affected.", parent=parent):
            app.template_service.delete_template(state["editor_id"])
            app.status.set("Template deleted.")
            show_library()

    def use_current() -> None:
        if state["editor_dirty"] or not state["editor_id"]:
            save(False)
        if state["editor_id"]:
            use_in_compose(state["editor_id"])

    def insert_html(html: str) -> None:
        focus_editor()
        editor.insert("insert", html)
        mark_dirty()

    def wrap_selection(before: str, after: str) -> None:
        focus_editor()
        try:
            selected = editor.get("sel.first", "sel.last")
            editor.delete("sel.first", "sel.last")
            editor.insert("insert", f"{before}{selected}{after}")
        except tk.TclError:
            editor.insert("insert", f"{before}{after}")
        mark_dirty()

    def pick_color() -> None:
        color = colorchooser.askcolor(parent=parent)[1]
        if color:
            wrap_selection(f'<span style="color:{color};">', "</span>")

    def insert_default_signature() -> None:
        signature = app.signature_service.default_signature()
        if signature:
            insert_html(signature.get("html_body") or signature.get("plain_text_body") or "")
        else:
            messagebox.showinfo("Signature", "No default signature is configured.", parent=parent)

    def undo() -> None:
        try:
            editor.edit_undo()
        except tk.TclError:
            pass

    def redo() -> None:
        try:
            editor.edit_redo()
        except tk.TclError:
            pass

    def set_sidebar_tab(name: str) -> None:
        tabs = tabs_ref.get("tabs")
        if tabs:
            tabs.set(name)
            _sync_tab_text(tabs, theme)

    def refresh_analysis() -> None:
        html = body_html()
        text = app.template_service.html_to_text(html)
        words = len([word for word in text.split() if word.strip()])
        chars = len(text)
        analysis = app.spam_analysis_service.analyze(fields["subject"].get(), html, fields["preheader"].get())
        health = max(0, min(100, 100 - analysis.score))
        metrics["words"].set(f"{words} words")
        metrics["characters"].set(f"{chars} characters")
        metrics["health"].set(f"Health {health}%")
        _render_smart_panels(theme, panels, fields, html, text, analysis, health)

    def autosave() -> None:
        state["autosave_job"] = None
        if not state.get("autosave_active") or not parent.winfo_exists():
            return
        try:
            if state["editor_id"] and state["editor_dirty"]:
                app.template_service.save_template(current_values(), state["editor_id"])
                state["editor_dirty"] = False
                metrics["saved"].set("Autosaved")
                metrics["autosaved"].set("Last autosaved: just now")
        finally:
            schedule_autosave()

    def schedule_autosave() -> None:
        if state.get("autosave_job") or not state.get("autosave_active") or not parent.winfo_exists():
            return
        state["autosave_job"] = parent.after(90000, autosave)

    def cancel_autosave() -> None:
        job = state.get("autosave_job")
        if job:
            try:
                parent.after_cancel(job)
            except tk.TclError:
                pass
            state["autosave_job"] = None

    def on_show() -> None:
        state["autosave_active"] = True
        schedule_autosave()

    def on_hide() -> None:
        state["autosave_active"] = False
        cancel_autosave()

    parent.on_show = on_show
    parent.on_hide = on_hide
    parent.cleanup = on_hide

    for variable in fields.values():
        variable.trace_add("write", lambda *_: mark_dirty())
    editor.bind("<FocusIn>", focus_editor, add="+")
    editor.bind("<KeyRelease>", mark_dirty, add="+")
    on_show()
    refresh_analysis()


def _render_table_view(parent: tk.Widget, state: dict, rows: list[dict], show_editor, on_select=None) -> None:
    theme = parent.theme if hasattr(parent, "theme") else None
    table = build_tree(parent, TABLE_COLUMNS, headings=("Star", "Template Name", "Category", "Subject", "Status", "Modified", "Last Used", "Actions"), height=14)
    table.column("favorite", width=52, stretch=False)
    table.column("status", width=88, stretch=False)
    table.column("actions", width=132, stretch=False)
    for row in rows:
        status = "Archived" if row.get("archived") else (row.get("status") or "Draft")
        insert_table_row(table, [
            "Star" if row.get("favorite") else "",
            row.get("name") or "",
            row.get("category") or "General",
            row.get("subject") or "",
            status,
            row.get("updated_at") or "",
            row.get("last_used_at") or "-",
            "Open / Use",
        ])

    def select(_event=None) -> None:
        state["selected_id"] = _table_selected_id(table, rows)
        if callable(on_select):
            on_select(state["selected_id"])

    table.bind("<<TreeviewSelect>>", select)
    table.bind("<Double-1>", lambda _event: show_editor(_table_selected_id(table, rows)))


def _library_summary(parent: tk.Widget, theme, rows: list[dict]) -> tk.Widget:
    summary = ctk_frame(parent, theme, "card", fg_color="transparent", border_width=0)
    values = [
        ("Active", sum(1 for row in rows if (row.get("status") or "Draft") == "Active" and not row.get("archived")), "success"),
        ("Draft", sum(1 for row in rows if (row.get("status") or "Draft") == "Draft" and not row.get("archived")), "draft"),
        ("Fav", sum(1 for row in rows if row.get("favorite")), "warning"),
    ]
    for label_text, value, level in values:
        chip = ctk_frame(summary, theme, "surface")
        chip.pack(side="left", padx=(6, 0))
        ds.status_dot(chip, level=level, theme=theme).pack(side="left", padx=(8, 4), pady=7)
        ctk_label(chip, theme, f"{label_text} {value}", role="caption", variant="surface").pack(side="left", padx=(0, 8), pady=6)
    return summary


def _render_template_inspector(parent: tk.Widget, app, state: dict, show_editor) -> None:
    theme = app.theme
    palette = theme.palette
    space = theme.spacing
    for child in parent.winfo_children():
        child.destroy()
    parent.columnconfigure(0, weight=1)
    selected_id = state.get("selected_id")
    template = app.template_service.get_template(selected_id) if selected_id else None
    ctk_label(parent, theme, "Template Details", role="panel_title", variant="card").grid(row=0, column=0, sticky="w", padx=space.md, pady=(space.md, 2))
    ctk_label(
        parent,
        theme,
        "Preview the selected template before opening it.",
        role="caption",
        variant="card",
        text_color=palette.text_muted,
        wraplength=240,
    ).grid(row=1, column=0, sticky="w", padx=space.md, pady=(0, space.md))
    if not template:
        empty = ds.EmptyState(parent, "No Template Selected", "Select a template to preview details.", theme=theme)
        empty.grid(row=2, column=0, sticky="nsew", padx=space.md, pady=(0, space.md))
        return

    status = "Archived" if template.get("archived") else (template.get("status") or "Draft")
    badge_row = ctk_frame(parent, theme, "card", fg_color="transparent", border_width=0)
    badge_row.grid(row=2, column=0, sticky="ew", padx=space.md, pady=(0, space.sm))
    ds.status_badge(badge_row, status, level="success" if status == "Active" else "draft", theme=theme).pack(side="left")
    if template.get("favorite"):
        ds.status_badge(badge_row, "Favorite", level="warning", theme=theme).pack(side="left", padx=(6, 0))

    preview = ctk_frame(parent, theme, "surface")
    preview.grid(row=3, column=0, sticky="ew", padx=space.md, pady=(0, space.md))
    preview.columnconfigure(0, weight=1)
    ctk_label(preview, theme, template.get("name") or "Untitled Template", role="panel_title", variant="surface", wraplength=230).grid(row=0, column=0, sticky="w", padx=space.md, pady=(space.md, 2))
    ctk_label(preview, theme, template.get("subject") or "No subject", role="body", variant="surface", wraplength=230).grid(row=1, column=0, sticky="w", padx=space.md, pady=(2, space.sm))
    ctk_label(
        preview,
        theme,
        app.template_service.html_to_text(template.get("html_body") or "")[:420] or "No body content yet.",
        role="caption",
        variant="surface",
        text_color=palette.text_muted,
        wraplength=230,
        justify="left",
    ).grid(row=2, column=0, sticky="ew", padx=space.md, pady=(0, space.md))

    facts = [
        ("Category", template.get("category") or "General"),
        ("Modified", template.get("updated_at") or "-"),
        ("Last Used", template.get("last_used_at") or "-"),
        ("Times Used", template.get("times_used") or 0),
    ]
    details = ctk_frame(parent, theme, "card", fg_color="transparent", border_width=0)
    details.grid(row=4, column=0, sticky="ew", padx=space.md, pady=(0, space.md))
    details.columnconfigure(1, weight=1)
    for idx, (label_text, value) in enumerate(facts):
        ctk_label(details, theme, label_text, role="caption", variant="card", text_color=palette.text_muted).grid(row=idx, column=0, sticky="w", pady=4)
        ctk_label(details, theme, str(value), role="caption", variant="card", wraplength=165).grid(row=idx, column=1, sticky="e", pady=4)

    ctk_button(parent, theme, "Open Template", command=lambda: show_editor(template["id"]), variant="primary", icon="edit", height=34).grid(row=5, column=0, sticky="ew", padx=space.md, pady=(0, 6))
    ctk_button(parent, theme, "Use In Compose", command=lambda: _use_id_in_compose(app, template["id"]), variant="success", icon="compose", height=34).grid(row=6, column=0, sticky="ew", padx=space.md, pady=(0, space.md))


def _render_card_view(parent: tk.Widget, app, state: dict, rows: list[dict], show_editor, on_select=None) -> None:
    theme = app.theme
    palette = theme.palette
    space = theme.spacing
    scroll = ctk.CTkScrollableFrame(parent, fg_color=palette.surface, corner_radius=0)
    scroll.grid(row=0, column=0, sticky="nsew", padx=theme.spacing.md, pady=theme.spacing.md)
    scroll.columnconfigure(0, weight=1)

    def select_template(template_id: int) -> None:
        state["selected_id"] = template_id
        if callable(on_select):
            on_select(template_id)

    def bind_select(widget: tk.Widget, template_id: int) -> None:
        widget.bind("<Button-1>", lambda _event, tid=template_id: select_template(tid), add="+")
        for child in widget.winfo_children():
            bind_select(child, template_id)

    for index, row in enumerate(rows):
        selected = int(row["id"]) == state.get("selected_id")
        card = ctk.CTkFrame(
            scroll,
            fg_color=palette.selection if selected else palette.surface_alt,
            corner_radius=4,
            border_width=1,
            border_color=palette.primary if selected else palette.border_soft,
        )
        card.grid(row=index, column=0, sticky="ew", padx=0, pady=(0, space.sm))
        card.columnconfigure(1, weight=1)
        card.columnconfigure(2, weight=1)
        status = "Archived" if row.get("archived") else (row.get("status") or "Draft")
        accent = palette.primary if status == "Active" else palette.warning if status == "Draft" else palette.text_muted
        ctk.CTkFrame(card, fg_color=accent, width=4, corner_radius=2).grid(row=0, column=0, rowspan=2, sticky="ns", padx=(space.md, 0), pady=space.md)
        title_cell = ctk_frame(card, theme, "surface", fg_color="transparent", border_width=0)
        title_cell.grid(row=0, column=1, rowspan=2, sticky="ew", padx=(space.md, space.sm), pady=space.md)
        title_cell.columnconfigure(0, weight=1)
        ctk_label(title_cell, theme, row.get("name") or "Untitled Template", role="panel_title", variant="surface", wraplength=360, fg_color="transparent").grid(row=0, column=0, sticky="w")
        ctk_label(title_cell, theme, row.get("subject") or "No subject yet", role="caption", variant="surface", text_color=palette.text_muted, wraplength=420, fg_color="transparent").grid(row=1, column=0, sticky="w", pady=(4, 0))

        meta_cell = ctk_frame(card, theme, "surface", fg_color="transparent", border_width=0)
        meta_cell.grid(row=0, column=2, rowspan=2, sticky="ew", padx=space.sm, pady=space.md)
        ctk_label(meta_cell, theme, row.get("category") or "General", role="caption", variant="surface", text_color=palette.text, fg_color="transparent").pack(anchor="w")
        ctk_label(meta_cell, theme, f"Modified {row.get('updated_at') or '-'}", role="caption", variant="surface", text_color=palette.text_muted, fg_color="transparent").pack(anchor="w", pady=(5, 0))
        ctk_label(meta_cell, theme, f"Last used {row.get('last_used_at') or 'never'}", role="caption", variant="surface", text_color=palette.text_muted, fg_color="transparent").pack(anchor="w", pady=(2, 0))

        badge_cell = ctk_frame(card, theme, "surface", fg_color="transparent", border_width=0)
        badge_cell.grid(row=0, column=3, sticky="e", padx=space.sm, pady=(space.md, 4))
        ds.status_badge(badge_cell, status, level="success" if status == "Active" else "draft", theme=theme).pack(side="left")
        if row.get("favorite"):
            ds.status_badge(badge_cell, "Favorite", level="warning", theme=theme).pack(side="left", padx=(6, 0))

        action_cell = ctk_frame(card, theme, "surface", fg_color="transparent", border_width=0)
        action_cell.grid(row=1, column=3, sticky="e", padx=space.sm, pady=(0, space.md))
        ctk_button(action_cell, theme, "Open", command=lambda tid=row["id"]: show_editor(tid), icon="edit", width=78, height=30).pack(side="left", padx=(0, 6))
        ctk_button(action_cell, theme, "Use", command=lambda tid=row["id"]: _use_id_in_compose(app, tid), icon="compose", variant="success", width=78, height=30).pack(side="left")
        bind_select(card, int(row["id"]))
        card.bind("<Double-1>", lambda _event, tid=row["id"]: show_editor(tid), add="+")


def _editor_toolbar(parent: tk.Widget, theme, *, insert_html, wrap_selection, pick_color, insert_signature, undo, redo) -> ctk.CTkFrame:
    palette = theme.palette
    space = theme.spacing
    toolbar = ctk.CTkFrame(parent, fg_color=palette.surface_alt, corner_radius=0, border_width=0)
    toolbar.grid_columnconfigure(99, weight=1)
    font_var = tk.StringVar(value="Segoe UI")
    size_var = tk.StringVar(value="14")
    ctk_combobox(toolbar, theme, font_var, ["Segoe UI", "Arial", "Georgia", "Tahoma", "Verdana"], width=104, height=30).grid(row=0, column=0, padx=(space.sm, 2), pady=6)
    ctk_combobox(toolbar, theme, size_var, ["12", "14", "16", "18", "22"], width=54, height=30).grid(row=0, column=1, padx=2, pady=6)
    actions = [
        ("B", lambda: wrap_selection("<strong>", "</strong>"), 38),
        ("I", lambda: wrap_selection("<em>", "</em>"), 38),
        ("U", lambda: wrap_selection("<u>", "</u>"), 38),
        ("Color", pick_color, 48),
        ("Left", lambda: insert_html('<p style="text-align:left;"></p>'), 42),
        ("Center", lambda: insert_html('<p style="text-align:center;"></p>'), 52),
        ("Right", lambda: insert_html('<p style="text-align:right;"></p>'), 44),
        ("Bul", lambda: insert_html("<ul><li>List item</li></ul>"), 42),
        ("Num", lambda: insert_html("<ol><li>List item</li></ol>"), 44),
        ("Link", lambda: insert_html('<a href="https://example.com">Link text</a>'), 42),
        ("Img", lambda: insert_html('<img src="https://example.com/image.png" alt="">'), 40),
        ("Tbl", lambda: insert_html("<table><tr><td>Column 1</td><td>Column 2</td></tr></table>"), 40),
        ("Btn", lambda: insert_html('<a class="button" href="https://example.com">Call to action</a>'), 40),
        ("Div", lambda: insert_html("<hr>"), 40),
        ("Sig", insert_signature, 40),
        ("Undo", undo, 48),
        ("Redo", redo, 46),
    ]
    for col, (label, command, width) in enumerate(actions, start=2):
        ctk_button(toolbar, theme, label, command=command, width=width, height=30).grid(row=0, column=col, padx=2, pady=6)
    ctk_combobox(
        toolbar,
        theme,
        tk.StringVar(value="Insert"),
        ["CTA", "Table", "Divider", "Countdown", "Social", "Signature", "Recent Block"],
        command=lambda value: insert_html(_quick_snippet(value)),
        width=86,
        height=30,
    ).grid(row=0, column=99, sticky="e", padx=(2, space.sm), pady=6)
    return toolbar


def _smart_sidebar(parent: tk.Widget, theme, panels: dict, tabs_ref: dict) -> ctk.CTkFrame:
    palette = theme.palette
    sidebar = ctk.CTkFrame(parent, fg_color=palette.surface, corner_radius=4, border_width=1, border_color=palette.border_soft)
    sidebar.grid(row=0, column=1, sticky="nsew")
    sidebar.columnconfigure(0, weight=1)
    sidebar.rowconfigure(1, weight=1)
    ctk_label(sidebar, theme, "Smart Sidebar", role="panel_title", variant="card").grid(row=0, column=0, sticky="w", padx=theme.spacing.md, pady=(theme.spacing.md, 2))
    tabs = ctk.CTkTabview(
        sidebar,
        fg_color=palette.surface,
        segmented_button_selected_color=palette.primary,
        segmented_button_selected_hover_color=palette.primary_dark,
        segmented_button_unselected_color=palette.surface_alt,
        segmented_button_unselected_hover_color=palette.hover,
        segmented_button_fg_color=palette.surface_alt,
        text_color=palette.text,
    )
    tabs.grid(row=1, column=0, sticky="nsew", padx=theme.spacing.md, pady=(theme.spacing.xs, theme.spacing.md))
    tabs_ref["tabs"] = tabs
    for tab_name in ["Health", "Preview", "Spam", "Personalization", "Links"]:
        tab = tabs.add(tab_name)
        tab.configure(fg_color=palette.surface)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        if tab_name == "Preview":
            preview = ctk_textbox(tab, theme, wrap="word")
            preview.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            preview.configure(state="disabled")
            panels[tab_name] = preview
        else:
            panel = ctk.CTkScrollableFrame(tab, fg_color=palette.surface, corner_radius=0)
            panel.grid(row=0, column=0, sticky="nsew")
            panel.columnconfigure(0, weight=1)
            panels[tab_name] = panel
    _sync_tab_text(tabs, theme)
    return sidebar


def _render_smart_panels(theme, panels: dict, fields: dict, html: str, text: str, analysis, health: int) -> None:
    links = URL_RE.findall(html)
    merge_fields = re.findall(r"{{[^}]+}}", html + fields["subject"].get() + fields["preheader"].get())
    _render_rows(panels.get("Health"), theme, [
        ("Overall Score", f"{health}%", "success" if health >= 75 else "warning"),
        ("Subject Score", "Good" if 24 <= len(fields["subject"].get()) <= 60 else "Needs review", "success" if 24 <= len(fields["subject"].get()) <= 60 else "warning"),
        ("Spam Score", str(analysis.score), "success" if analysis.score < 25 else "warning"),
        ("Readability", f"{len(text.splitlines()) or 1} sections", "info"),
        ("Missing Merge Fields", "None" if merge_fields else "Personalization optional", "success" if merge_fields else "warning"),
        ("Link Validation", f"{len(links)} links found", "success" if links else "warning"),
    ])
    preview = panels.get("Preview")
    if isinstance(preview, ctk.CTkTextbox):
        preview.configure(state="normal")
        preview.delete("1.0", "end")
        preview.insert("1.0", f"Subject: {fields['subject'].get()}\nPreheader: {fields['preheader'].get()}\n\n{text}")
        preview.configure(state="disabled")
    warnings = analysis.warnings or ["No spam warnings detected."]
    _render_rows(panels.get("Spam"), theme, [(item, "", "warning" if analysis.warnings else "success") for item in warnings])
    _render_rows(panels.get("Personalization"), theme, [
        ("Available Merge Fields", f"{len(MERGE_TAGS)} fields", "info"),
        ("Detected", ", ".join(sorted(set(merge_fields))) if merge_fields else "None yet", "success" if merge_fields else "warning"),
        *[(tag, "", "info") for tag in MERGE_TAGS],
    ])
    _render_rows(panels.get("Links"), theme, [
        ("Tracking Status", "Placeholder until sending engine is connected", "info"),
        ("Links Found", str(len(links)), "success" if links else "warning"),
        ("Images Found", str(len(IMG_RE.findall(html))), "info"),
    ])


def _render_rows(parent: tk.Widget | None, theme, rows: list[tuple[str, str, str]]) -> None:
    if parent is None:
        return
    for child in parent.winfo_children():
        child.destroy()
    for idx, (title, value, level) in enumerate(rows):
        row = ctk_frame(parent, theme, "surface")
        row.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
        row.columnconfigure(1, weight=1)
        ds.status_dot(row, level=level, theme=theme).grid(row=0, column=0, padx=(8, 6), pady=8)
        ctk_label(row, theme, title, role="caption", variant="surface").grid(row=0, column=1, sticky="w", pady=8)
        if value:
            ctk_label(row, theme, value, role="caption", variant="surface", text_color=theme.palette.text_muted).grid(row=0, column=2, sticky="e", padx=(6, 8), pady=8)


def _compact_field(parent: tk.Widget, theme, label_text: str, variable: tk.StringVar, row: int, column: int) -> None:
    ctk_label(parent, theme, label_text, role="caption", variant="card", text_color=theme.palette.text_muted).grid(row=row, column=column, sticky="w", padx=(0 if column == 0 else theme.spacing.md, theme.spacing.xs), pady=4)
    ctk_entry(parent, theme, variable, height=30).grid(row=row, column=column + 1, sticky="ew", padx=(0, theme.spacing.sm), pady=4)


def _combo_field(parent: tk.Widget, theme, label_text: str, variable: tk.StringVar, values: list[str], row: int, column: int) -> None:
    ctk_label(parent, theme, label_text, role="caption", variant="card", text_color=theme.palette.text_muted).grid(row=row, column=column, sticky="w", padx=(theme.spacing.md if column else 0, theme.spacing.xs), pady=4)
    ctk_combobox(parent, theme, variable, values, height=30).grid(row=row, column=column + 1, sticky="ew", padx=(0, theme.spacing.sm), pady=4)


def _filtered_rows(app, state: dict, filters: dict) -> list[dict]:
    folder = state["folder"]
    category = filters["category"].get()
    status = filters["status"].get()
    if folder in {"Sales", "Events", "Introductions", "Custom"}:
        category = folder
    elif folder == "Follow-Up":
        category = "Follow Up"
    elif folder == "Drafts":
        status = "Draft"
    elif folder == "Archived":
        status = "Archived"
    rows = app.template_service.filtered_templates(
        filters["search"].get(),
        category,
        status,
        include_archived=folder == "Archived" or status == "Archived",
        sort_by=SORTS.get(filters["sort"].get(), "updated_at DESC"),
    )
    if folder == "Favorites":
        rows = [row for row in rows if row.get("favorite")]
    elif folder == "Recently Used":
        rows = [row for row in rows if row.get("last_used_at")]
    return rows


def _folder_counts(rows: list[dict]) -> dict[str, int]:
    counts = {folder: 0 for folder in FOLDERS}
    for row in rows:
        category = row.get("category") or "General"
        archived = bool(row.get("archived"))
        status = "Archived" if archived else (row.get("status") or "Draft")
        counts["All Templates"] += 1 if not archived else 0
        counts["Favorites"] += 1 if row.get("favorite") and not archived else 0
        counts["Recently Used"] += 1 if row.get("last_used_at") and not archived else 0
        counts["Drafts"] += 1 if status == "Draft" and not archived else 0
        counts["Archived"] += 1 if archived else 0
        counts["Sales"] += 1 if category == "Sales" and not archived else 0
        counts["Events"] += 1 if category == "Events" and not archived else 0
        counts["Follow-Up"] += 1 if category == "Follow Up" and not archived else 0
        counts["Introductions"] += 1 if category == "Introductions" and not archived else 0
        counts["Custom"] += 1 if category == "Custom" and not archived else 0
    return counts


def _set_folder(state: dict, folder: str, refresh) -> None:
    state["folder"] = folder
    state["selected_id"] = None
    refresh()


def _clear_filters(filters: dict) -> None:
    filters["search"].set("")
    filters["category"].set("All")
    filters["status"].set("All")
    filters["sort"].set("Newest")


def _table_selected_id(table, rows: list[dict]) -> int | None:
    selection = table.selection()
    if not selection:
        return None
    values = table.item(selection[0], "values")
    if not values:
        return None
    name = values[1]
    row = next((item for item in rows if item.get("name") == name), None)
    return int(row["id"]) if row else None


def _open_selected(parent: tk.Widget, state: dict, show_editor) -> None:
    if not state.get("selected_id"):
        messagebox.showinfo("Open Template", "Select a template first.", parent=parent)
        return
    show_editor(state["selected_id"])


def _duplicate_selected(parent: tk.Widget, app, state: dict, refresh) -> None:
    if not state.get("selected_id"):
        messagebox.showinfo("Duplicate Template", "Select a template first.", parent=parent)
        return
    app.template_service.duplicate_template(state["selected_id"])
    refresh()
    app.status.set("Template duplicated.")


def _archive_selected(parent: tk.Widget, app, state: dict, refresh) -> None:
    if not state.get("selected_id"):
        messagebox.showinfo("Archive Template", "Select a template first.", parent=parent)
        return
    app.template_service.archive_template(state["selected_id"], True)
    state["selected_id"] = None
    refresh()
    app.status.set("Template archived.")


def _delete_selected(parent: tk.Widget, app, state: dict, refresh) -> None:
    if not state.get("selected_id"):
        messagebox.showinfo("Delete Template", "Select a template first.", parent=parent)
        return
    if not messagebox.askyesno("Delete Template?", "Deleting this template cannot be undone.\n\nCampaigns already created from this template will not be affected.", parent=parent):
        return
    app.template_service.delete_template(state["selected_id"])
    state["selected_id"] = None
    refresh()
    app.status.set("Template deleted.")


def _use_selected_in_compose(parent: tk.Widget, app, state: dict) -> None:
    if not state.get("selected_id"):
        messagebox.showinfo("Use In Compose", "Select a template first.", parent=parent)
        return
    _use_id_in_compose(app, state["selected_id"])


def _use_id_in_compose(app, template_id: int) -> None:
    template = app.template_service.get_template(template_id)
    if not template:
        return
    app.template_service.increment_used(template_id)
    app.navigate("Compose")
    compose_host = app.page_cache.get("Compose")
    loader = getattr(compose_host, "_safesend_load_template", None)
    if callable(loader):
        loader(template)
    app.status.set(f"Loaded {template['name']} into Compose as a working copy.")


def _export_selected(parent: tk.Widget, app, state: dict) -> None:
    if not state.get("selected_id"):
        messagebox.showinfo("Export Template", "Select a template first.", parent=parent)
        return
    template = app.template_service.get_template(state["selected_id"])
    if not template:
        return
    path = filedialog.asksaveasfilename(
        title="Export Template",
        defaultextension=".json",
        filetypes=[("SafeSend template", "*.json"), ("All files", "*.*")],
        initialfile=f"{template['name']}.json",
        parent=parent,
    )
    if path:
        app.template_service.export_template(template["id"], path)
        app.status.set("Template exported.")


def _import_template(parent: tk.Widget, app, show_editor) -> None:
    path = filedialog.askopenfilename(title="Import Template", filetypes=[("SafeSend template", "*.json"), ("All files", "*.*")], parent=parent)
    if not path:
        return
    try:
        template_id = app.template_service.import_template(path)
        show_editor(template_id)
        app.status.set("Template imported.")
    except (OSError, ValueError) as exc:
        messagebox.showerror("Import Template", str(exc), parent=parent)


def _quick_snippet(value: str) -> str:
    return {
        "CTA": '<a class="button" href="https://example.com">Start now</a>',
        "Table": "<table><tr><td>Feature</td><td>Benefit</td></tr></table>",
        "Divider": "<hr>",
        "Countdown": "{{Countdown}}",
        "Social": "{{SocialLinks}}",
        "Signature": "{{Signature}}",
        "Recent Block": "<p>Thanks for taking a look.</p>",
    }.get(value, "")


def _sync_tab_text(tabs: ctk.CTkTabview, theme) -> None:
    try:
        selected = tabs.get()
        tabs._segmented_button.configure(command=lambda value: (tabs.set(value), _sync_tab_text(tabs, theme)))
        for label_text, button in getattr(tabs._segmented_button, "_buttons_dict", {}).items():
            button.configure(text_color=theme.palette.surface if label_text == selected else theme.palette.text)
    except (AttributeError, tk.TclError):
        pass
