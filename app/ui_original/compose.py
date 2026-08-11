import re
import tkinter as tk
from html import escape
from tkinter import colorchooser, messagebox, simpledialog, ttk

from app.ui.shared import build_tree, section

MERGE_TAGS = ["{{FirstName}}", "{{LastName}}", "{{Company}}", "{{Email}}", "{{State}}", "{{City}}", "{{Custom1}}", "{{Custom2}}", "{{Custom3}}", "{{Unsubscribe}}"]
FONTS = ["Segoe UI", "Arial", "Calibri", "Georgia", "Times New Roman", "Courier New"]
SIZES = ["10", "11", "12", "14", "16", "18", "22", "28", "36"]


def build(parent: tk.Widget, app) -> None:
    state = {
        "template_id": 0,
        "source_mode": False,
        "dirty": False,
        "autosave_job": None,
        "zoom": 1.0,
    }
    vars_ = {
        "name": tk.StringVar(),
        "from_name": tk.StringVar(),
        "from_email": tk.StringVar(),
        "reply_to_email": tk.StringVar(),
        "subject": tk.StringVar(),
        "preheader": tk.StringVar(),
        "search": tk.StringVar(),
        "sort": tk.StringVar(value="updated_at DESC"),
        "favorite": tk.BooleanVar(value=False),
        "font": tk.StringVar(value="Segoe UI"),
        "size": tk.StringVar(value="12"),
        "signature": tk.StringVar(),
        "subject_entry": tk.StringVar(),
    }

    frame = section(parent, "Compose", "Email Composer & Template Builder")
    frame.pack(fill="both", expand=True)
    frame.rowconfigure(2, weight=1)
    frame.columnconfigure(0, weight=1)

    root_pane = ttk.PanedWindow(frame, orient="horizontal")
    root_pane.grid(row=2, column=0, sticky="nsew")

    library = ttk.Frame(root_pane, padding=10, style="Card.TFrame")
    composer = ttk.Frame(root_pane, padding=10)
    right = ttk.Frame(root_pane, padding=10, style="Card.TFrame")
    root_pane.add(library, weight=1)
    root_pane.add(composer, weight=4)
    root_pane.add(right, weight=2)

    library.rowconfigure(4, weight=1)
    library.columnconfigure(0, weight=1)
    ttk.Label(library, text="Template Library", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Entry(library, textvariable=vars_["search"]).grid(row=1, column=0, sticky="ew", pady=(8, 6))
    ttk.Combobox(
        library,
        textvariable=vars_["sort"],
        values=["updated_at DESC", "name ASC", "name DESC", "created_at DESC", "favorite DESC", "times_used DESC"],
        state="readonly",
    ).grid(row=2, column=0, sticky="ew", pady=(0, 6))
    lib_buttons = ttk.Frame(library)
    lib_buttons.grid(row=3, column=0, sticky="ew", pady=(0, 8))
    template_table = ttk.Frame(library)
    template_table.grid(row=4, column=0, sticky="nsew")
    template_table.rowconfigure(0, weight=1)
    template_table.columnconfigure(0, weight=1)
    template_tree = build_tree(
        template_table,
        ("id", "fav", "name", "subject", "updated_at", "times_used"),
        headings=("#", "*", "Name", "Subject", "Modified", "Used"),
        height=18,
    )
    template_tree.column("id", width=38, stretch=False)
    template_tree.column("fav", width=28, stretch=False)
    template_tree.column("times_used", width=48, stretch=False)

    for label, command in [
        ("New", lambda: new_template()),
        ("Duplicate", lambda: duplicate_template()),
        ("Rename", lambda: rename_template()),
        ("Delete", lambda: delete_template()),
        ("Archive", lambda: archive_template()),
        ("Favorite", lambda: favorite_template()),
    ]:
        ttk.Button(lib_buttons, text=label, command=command).pack(side="left", padx=(0, 4), pady=2)

    composer.rowconfigure(4, weight=1)
    composer.columnconfigure(0, weight=1)
    header = ttk.Frame(composer, padding=10, style="Card.TFrame")
    header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    for col in (1, 3):
        header.columnconfigure(col, weight=1)
    _field(header, "Template", vars_["name"], 0, 0)
    ttk.Checkbutton(header, text="Favorite", variable=vars_["favorite"], command=lambda: mark_dirty()).grid(row=0, column=4, sticky="w", padx=8)
    _field(header, "From Name", vars_["from_name"], 1, 0)
    _field(header, "From Email", vars_["from_email"], 1, 2)
    _field(header, "Reply-To", vars_["reply_to_email"], 2, 0)
    _field(header, "Subject", vars_["subject"], 3, 0, columnspan=3)
    _field(header, "Preheader", vars_["preheader"], 4, 0, columnspan=3)

    ribbon = ttk.Frame(composer, padding=(8, 7), style="Card.TFrame")
    ribbon.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    source_label = tk.StringVar(value="HTML Source")
    ttk.Button(ribbon, text="B", command=lambda: apply_tag("bold")).pack(side="left", padx=2)
    ttk.Button(ribbon, text="I", command=lambda: apply_tag("italic")).pack(side="left", padx=2)
    ttk.Button(ribbon, text="U", command=lambda: apply_tag("underline")).pack(side="left", padx=2)
    ttk.Combobox(ribbon, textvariable=vars_["font"], values=FONTS, state="readonly", width=14).pack(side="left", padx=(10, 2))
    ttk.Combobox(ribbon, textvariable=vars_["size"], values=SIZES, state="readonly", width=5).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Color", command=lambda: color_text("fg")).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Highlight", command=lambda: color_text("bg")).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Left", command=lambda: wrap_selection("div", ' style="text-align:left"')).pack(side="left", padx=(10, 2))
    ttk.Button(ribbon, text="Center", command=lambda: wrap_selection("div", ' style="text-align:center"')).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Right", command=lambda: wrap_selection("div", ' style="text-align:right"')).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Bullets", command=lambda: list_wrap("ul")).pack(side="left", padx=(10, 2))
    ttk.Button(ribbon, text="Numbers", command=lambda: list_wrap("ol")).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Table", command=lambda: insert_table()).pack(side="left", padx=(10, 2))
    ttk.Button(ribbon, text="Rule", command=lambda: insert_html("<hr>")).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Link", command=lambda: insert_link()).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Image", command=lambda: insert_image()).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Undo", command=lambda: active_editor().event_generate("<<Undo>>")).pack(side="left", padx=(10, 2))
    ttk.Button(ribbon, text="Redo", command=lambda: active_editor().event_generate("<<Redo>>")).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Find", command=lambda: find_text()).pack(side="left", padx=(10, 2))
    ttk.Button(ribbon, text="Replace", command=lambda: replace_text()).pack(side="left", padx=2)
    ttk.Button(ribbon, text="Zoom +", command=lambda: zoom(0.1)).pack(side="left", padx=(10, 2))
    ttk.Button(ribbon, text="Zoom -", command=lambda: zoom(-0.1)).pack(side="left", padx=2)
    ttk.Button(ribbon, textvariable=source_label, command=lambda: toggle_source()).pack(side="right", padx=2)

    editor_frame = ttk.Frame(composer)
    editor_frame.grid(row=4, column=0, sticky="nsew")
    editor_frame.rowconfigure(0, weight=1)
    editor_frame.columnconfigure(0, weight=1)
    visual = tk.Text(editor_frame, wrap="word", undo=True, font=("Segoe UI", 12), padx=14, pady=12)
    source = tk.Text(editor_frame, wrap="none", undo=True, font=("Consolas", 11), padx=12, pady=12)
    visual.grid(row=0, column=0, sticky="nsew")
    _configure_text_tags(visual)

    bottom = ttk.Frame(composer)
    bottom.grid(row=5, column=0, sticky="ew", pady=(8, 0))
    status_text = tk.StringVar(value="Ready")
    ttk.Label(bottom, textvariable=status_text, style="Muted.TLabel").pack(side="left")
    ttk.Button(bottom, text="Save Template", command=lambda: save_template()).pack(side="right", padx=4)
    ttk.Button(bottom, text="Manual Draft Save", command=lambda: save_draft("Manual draft saved.")).pack(side="right", padx=4)
    ttk.Button(bottom, text="Restore Draft", command=lambda: restore_draft()).pack(side="right", padx=4)
    ttk.Button(bottom, text="Restore Version", command=lambda: restore_version()).pack(side="right", padx=4)

    right.rowconfigure(2, weight=1)
    right.columnconfigure(0, weight=1)
    notebook = ttk.Notebook(right)
    notebook.grid(row=0, column=0, sticky="nsew")
    tags_tab = ttk.Frame(notebook, padding=10)
    preview_tab = ttk.Frame(notebook, padding=10)
    score_tab = ttk.Frame(notebook, padding=10)
    subject_tab = ttk.Frame(notebook, padding=10)
    signature_tab = ttk.Frame(notebook, padding=10)
    notebook.add(tags_tab, text="Merge")
    notebook.add(preview_tab, text="Preview")
    notebook.add(score_tab, text="Spam")
    notebook.add(subject_tab, text="Subjects")
    notebook.add(signature_tab, text="Signatures")

    ttk.Label(tags_tab, text="Double-click to insert", style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
    tag_list = tk.Listbox(tags_tab, height=12)
    tag_list.pack(fill="both", expand=True)
    for tag in MERGE_TAGS:
        tag_list.insert("end", tag)
    tag_list.bind("<Double-1>", lambda _event: insert_selected_merge_tag())
    ttk.Button(tags_tab, text="Insert Merge Field", command=lambda: insert_selected_merge_tag()).pack(fill="x", pady=(8, 0))

    preview_tab.rowconfigure(1, weight=1)
    preview_tab.rowconfigure(3, weight=1)
    preview_tab.columnconfigure(0, weight=1)
    ttk.Label(preview_tab, text="Desktop Preview", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
    desktop_preview = tk.Text(preview_tab, height=12, wrap="word", state="disabled", padx=10, pady=10)
    desktop_preview.grid(row=1, column=0, sticky="nsew", pady=(4, 10))
    ttk.Label(preview_tab, text="Mobile Preview", style="PanelTitle.TLabel").grid(row=2, column=0, sticky="w")
    mobile_preview = tk.Text(preview_tab, height=10, width=36, wrap="word", state="disabled", padx=10, pady=10)
    mobile_preview.grid(row=3, column=0, sticky="nsew", pady=(4, 0))

    spam_score = tk.StringVar(value="Score: 0")
    ttk.Label(score_tab, textvariable=spam_score, font=("Segoe UI Semibold", 22), style="PanelTitle.TLabel").pack(anchor="w")
    spam_details = tk.Text(score_tab, height=24, wrap="word", state="disabled")
    spam_details.pack(fill="both", expand=True, pady=(8, 0))

    _build_subject_lab(subject_tab, app, state, vars_, lambda: load_subjects(), lambda: mark_dirty())
    subject_table = ttk.Frame(subject_tab)
    subject_table.grid(row=5, column=0, columnspan=4, sticky="nsew", pady=(8, 0))
    subject_table.rowconfigure(0, weight=1)
    subject_table.columnconfigure(0, weight=1)
    subject_tree = build_tree(subject_table, ("id", "preferred", "subject", "label", "ab_group", "updated_at"), headings=("#", "Preferred", "Subject", "Label", "A/B", "Modified"), height=8)
    subject_tree.column("id", width=36, stretch=False)
    subject_tree.column("preferred", width=70, stretch=False)
    subject_tab.rowconfigure(5, weight=1)
    subject_tab.columnconfigure(0, weight=1)

    _build_signature_tab(signature_tab, app, vars_, lambda: load_signatures(), lambda html: (insert_html(html), mark_dirty()))
    signature_table = ttk.Frame(signature_tab)
    signature_table.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
    signature_table.rowconfigure(0, weight=1)
    signature_table.columnconfigure(0, weight=1)
    signature_tree = build_tree(signature_table, ("id", "default", "name", "updated_at"), headings=("#", "Default", "Name", "Modified"), height=8)
    signature_tab.rowconfigure(4, weight=1)
    signature_tab.columnconfigure(0, weight=1)

    def refresh_templates(select_id: int | None = None) -> None:
        _clear_tree(template_tree)
        for item in app.template_service.list_templates(vars_["search"].get(), False, vars_["sort"].get()):
            row = [item["id"], "*" if item["favorite"] else "", item["name"], item.get("subject") or "", item.get("updated_at") or "", item.get("times_used") or 0]
            tree_item = template_tree.insert("", "end", values=row)
            if select_id and int(item["id"]) == select_id:
                template_tree.selection_set(tree_item)
                template_tree.focus(tree_item)
                template_tree.see(tree_item)
        if select_id:
            load_template(select_id)

    def selected_template_id() -> int:
        selection = template_tree.selection()
        if not selection:
            return state["template_id"]
        values = template_tree.item(selection[0], "values")
        return int(values[0]) if values else 0

    def load_template(template_id: int) -> None:
        template = app.template_service.get_template(template_id)
        if not template:
            return
        state["template_id"] = template_id
        for key in ["name", "from_name", "from_email", "reply_to_email", "subject", "preheader"]:
            vars_[key].set(template.get(key) or "")
        vars_["favorite"].set(bool(template.get("favorite")))
        set_editor_html(template.get("html_body") or "<p></p>")
        state["dirty"] = False
        load_subjects()
        load_signatures()
        update_all()
        status_text.set(f"Loaded template: {template['name']}")

    def new_template() -> None:
        if not confirm_unsaved():
            return
        template_id = app.template_service.create_template("Untitled Template")
        refresh_templates(template_id)

    def duplicate_template() -> None:
        template_id = selected_template_id()
        if not template_id:
            return
        refresh_templates(app.template_service.duplicate_template(template_id))

    def rename_template() -> None:
        template_id = selected_template_id()
        if not template_id:
            return
        name = simpledialog.askstring("Rename Template", "Template name:", initialvalue=vars_["name"].get(), parent=frame)
        if name:
            app.template_service.rename_template(template_id, name)
            refresh_templates(template_id)

    def delete_template() -> None:
        template_id = selected_template_id()
        if template_id and messagebox.askyesno("Delete Template", "Delete this template and its versions?", parent=frame):
            app.template_service.delete_template(template_id)
            state["template_id"] = 0
            clear_editor()
            refresh_templates()

    def archive_template() -> None:
        template_id = selected_template_id()
        if template_id:
            app.template_service.archive_template(template_id, True)
            state["template_id"] = 0
            clear_editor()
            refresh_templates()

    def favorite_template() -> None:
        template_id = selected_template_id()
        if template_id:
            app.template_service.toggle_favorite(template_id)
            refresh_templates(template_id)

    def save_template() -> int:
        values = current_values()
        template_id = app.template_service.save_template(values, state["template_id"] or None)
        state["template_id"] = template_id
        state["dirty"] = False
        refresh_templates(template_id)
        status_text.set("Template saved.")
        return template_id

    def save_draft(message: str = "Autosaved draft.") -> None:
        app.draft_service.save_draft(current_values(), state["template_id"] or None)
        status_text.set(message)

    def restore_draft() -> None:
        drafts = app.draft_service.list_drafts(state["template_id"] or None)
        if not drafts:
            messagebox.showinfo("Restore Draft", "No drafts are available.", parent=frame)
            return
        labels = [f"{draft['id']} - {draft['saved_at']} - {draft.get('name') or 'Untitled'}" for draft in drafts]
        choice = simpledialog.askstring("Restore Draft", "Draft ID to restore:\n" + "\n".join(labels[:10]), parent=frame)
        if not choice:
            return
        draft = app.draft_service.get_draft(int(choice.split(" - ", 1)[0]))
        if draft:
            apply_values(draft)
            status_text.set("Draft restored.")

    def restore_version() -> None:
        template_id = state["template_id"]
        if not template_id:
            messagebox.showinfo("Restore Version", "Save or select a template first.", parent=frame)
            return
        versions = app.template_service.versions(template_id)
        if not versions:
            messagebox.showinfo("Restore Version", "No previous versions are available.", parent=frame)
            return
        labels = [f"{v['id']} - v{v['version_number']} - {v['created_at']}" for v in versions]
        choice = simpledialog.askstring("Restore Version", "Version ID to restore:\n" + "\n".join(labels[:10]), parent=frame)
        if choice:
            restored_id = app.template_service.restore_version(int(choice.split(" - ", 1)[0]))
            refresh_templates(restored_id)

    def current_html() -> str:
        return source.get("1.0", "end").strip() if state["source_mode"] else visual_to_html()

    def current_values() -> dict:
        html = current_html()
        return {
            "name": vars_["name"].get(),
            "from_name": vars_["from_name"].get(),
            "from_email": vars_["from_email"].get(),
            "reply_to_email": vars_["reply_to_email"].get(),
            "subject": vars_["subject"].get(),
            "preheader": vars_["preheader"].get(),
            "html_body": html,
            "plain_text_body": app.template_service.html_to_text(html),
            "favorite": vars_["favorite"].get(),
            "source_mode": state["source_mode"],
        }

    def apply_values(values: dict) -> None:
        for key in ["name", "from_name", "from_email", "reply_to_email", "subject", "preheader"]:
            vars_[key].set(values.get(key) or "")
        set_editor_html(values.get("html_body") or "<p></p>")
        mark_dirty()

    def clear_editor() -> None:
        state["template_id"] = 0
        for key in ["name", "from_name", "from_email", "reply_to_email", "subject", "preheader"]:
            vars_[key].set("")
        vars_["favorite"].set(False)
        set_editor_html("<p></p>")
        state["dirty"] = False
        update_all()

    def confirm_unsaved() -> bool:
        if not state["dirty"]:
            return True
        return messagebox.askyesno("Unsaved Changes", "Discard unsaved changes?", parent=frame)

    def set_editor_html(html: str) -> None:
        if state["source_mode"]:
            source.delete("1.0", "end")
            source.insert("1.0", html)
        else:
            visual.delete("1.0", "end")
            visual.insert("1.0", app.template_service.html_to_text(html) or "")
            visual.edit_reset()
            source.delete("1.0", "end")
            source.insert("1.0", html)

    def visual_to_html() -> str:
        text = visual.get("1.0", "end").strip()
        if not text:
            return "<p></p>"
        return "\n".join(f"<p>{escape(line) or '<br>'}</p>" for line in text.splitlines())

    def toggle_source() -> None:
        if state["source_mode"]:
            html = source.get("1.0", "end").strip()
            source.grid_remove()
            visual.grid(row=0, column=0, sticky="nsew")
            state["source_mode"] = False
            source_label.set("HTML Source")
            set_editor_html(html)
        else:
            source.delete("1.0", "end")
            source.insert("1.0", visual_to_html())
            visual.grid_remove()
            source.grid(row=0, column=0, sticky="nsew")
            state["source_mode"] = True
            source_label.set("Visual Editor")
        update_all()

    def active_editor() -> tk.Text:
        return source if state["source_mode"] else visual

    def apply_tag(tag: str) -> None:
        editor = active_editor()
        try:
            if state["source_mode"]:
                wrappers = {"bold": ("<strong>", "</strong>"), "italic": ("<em>", "</em>"), "underline": ("<u>", "</u>")}
                start, end = wrappers[tag]
                wrap_raw_selection(start, end)
            else:
                editor.tag_add(tag, "sel.first", "sel.last")
        except tk.TclError:
            return
        mark_dirty()

    def color_text(kind: str) -> None:
        color = colorchooser.askcolor(parent=frame)[1]
        if not color:
            return
        if state["source_mode"]:
            css = f"color:{color}" if kind == "fg" else f"background-color:{color}"
            wrap_raw_selection(f'<span style="{css}">', "</span>")
        else:
            tag = f"{kind}_{color}"
            visual.tag_configure(tag, foreground=color if kind == "fg" else None, background=color if kind == "bg" else None)
            try:
                visual.tag_add(tag, "sel.first", "sel.last")
            except tk.TclError:
                pass
        mark_dirty()

    def wrap_selection(tag: str, attrs: str = "") -> None:
        wrap_raw_selection(f"<{tag}{attrs}>", f"</{tag}>")

    def list_wrap(tag: str) -> None:
        editor = active_editor()
        text = selected_text() or editor.get("insert linestart", "insert lineend")
        items = "".join(f"<li>{escape(line.strip())}</li>" for line in text.splitlines() if line.strip())
        insert_html(f"<{tag}>{items}</{tag}>")

    def wrap_raw_selection(before: str, after: str) -> None:
        editor = active_editor()
        try:
            text = editor.get("sel.first", "sel.last")
            editor.delete("sel.first", "sel.last")
        except tk.TclError:
            text = ""
        editor.insert("insert", f"{before}{text}{after}")
        mark_dirty()

    def selected_text() -> str:
        try:
            return active_editor().get("sel.first", "sel.last")
        except tk.TclError:
            return ""

    def insert_html(html: str) -> None:
        if state["source_mode"]:
            source.insert("insert", html)
        else:
            visual.insert("insert", app.template_service.html_to_text(html) or html)
            source.insert("end", html)
        mark_dirty()

    def insert_table() -> None:
        insert_html("<table border=\"1\" cellpadding=\"6\"><tr><td>Column 1</td><td>Column 2</td></tr><tr><td>Value</td><td>Value</td></tr></table>")

    def insert_link() -> None:
        text = simpledialog.askstring("Insert Link", "Display text:", parent=frame) or "Link"
        url = simpledialog.askstring("Insert Link", "URL:", parent=frame) or ""
        if not re.match(r"^https?://", url):
            messagebox.showerror("Link", "URL must start with http:// or https://", parent=frame)
            return
        insert_html(f'<a href="{escape(url)}">{escape(text)}</a>')

    def insert_image() -> None:
        url = simpledialog.askstring("Insert Image", "Image URL:", parent=frame) or ""
        if not re.match(r"^https?://", url):
            messagebox.showerror("Image", "Image URL must start with http:// or https://", parent=frame)
            return
        alt = simpledialog.askstring("Insert Image", "Alt text:", parent=frame) or ""
        width = simpledialog.askstring("Insert Image", "Width in pixels:", initialvalue="600", parent=frame) or "600"
        align = simpledialog.askstring("Insert Image", "Alignment: left, center, right", initialvalue="center", parent=frame) or "center"
        insert_html(f'<p style="text-align:{escape(align)}"><img src="{escape(url)}" alt="{escape(alt)}" width="{escape(width)}"></p>')

    def insert_selected_merge_tag() -> None:
        selection = tag_list.curselection()
        tag = tag_list.get(selection[0]) if selection else MERGE_TAGS[0]
        active_editor().insert("insert", tag)
        mark_dirty()

    def find_text() -> None:
        needle = simpledialog.askstring("Find", "Find text:", parent=frame)
        if not needle:
            return
        editor = active_editor()
        idx = editor.search(needle, "insert", stopindex="end", nocase=True)
        if idx:
            end = f"{idx}+{len(needle)}c"
            editor.tag_remove("sel", "1.0", "end")
            editor.tag_add("sel", idx, end)
            editor.mark_set("insert", end)
            editor.see(idx)

    def replace_text() -> None:
        needle = simpledialog.askstring("Replace", "Find text:", parent=frame)
        if needle is None:
            return
        repl = simpledialog.askstring("Replace", "Replace with:", parent=frame)
        if repl is None:
            return
        editor = active_editor()
        content = editor.get("1.0", "end")
        editor.delete("1.0", "end")
        editor.insert("1.0", content.replace(needle, repl))
        mark_dirty()

    def zoom(delta: float) -> None:
        state["zoom"] = max(0.7, min(1.8, state["zoom"] + delta))
        visual.configure(font=("Segoe UI", int(12 * state["zoom"])))
        source.configure(font=("Consolas", int(11 * state["zoom"])))

    def update_all(_event=None) -> None:
        html = current_html()
        text = app.template_service.html_to_text(html)
        word_count = len(text.split())
        char_count = len(text)
        status_text.set(f"Words: {word_count}  Characters: {char_count}  {'Unsaved' if state['dirty'] else 'Saved'}")
        preview = f"Subject: {vars_['subject'].get()}\nPreheader: {vars_['preheader'].get()}\n\n{text}"
        _set_text(desktop_preview, preview)
        _set_text(mobile_preview, preview[:1200])
        analysis = app.spam_analysis_service.analyze(vars_["subject"].get(), html, vars_["preheader"].get())
        spam_score.set(f"Score: {analysis.score}/100")
        details = ["Warnings:", *(analysis.warnings or ["None"]), "", "Suggestions:", *analysis.suggestions]
        _set_text(spam_details, "\n".join(details))

    def mark_dirty(_event=None) -> None:
        state["dirty"] = True
        update_all()

    def schedule_autosave() -> None:
        if state["dirty"] or any(vars_[key].get().strip() for key in ["name", "subject", "from_email"]):
            save_draft("Autosaved draft.")
        state["autosave_job"] = frame.after(30000, schedule_autosave)

    def load_subjects() -> None:
        _clear_tree(subject_tree)
        for row in app.subject_service.list_subjects(state["template_id"] or None):
            subject_tree.insert("", "end", values=[row["id"], "Yes" if row["is_preferred"] else "No", row["subject"], row.get("label") or "", row.get("ab_group") or "", row.get("updated_at") or ""])

    def load_signatures() -> None:
        signatures = app.signature_service.list_signatures()
        vars_["signature"].set(f"{signatures[0]['id']} - {signatures[0]['name']}" if signatures else "")
        _clear_tree(signature_tree)
        for row in signatures:
            signature_tree.insert("", "end", values=[row["id"], "Yes" if row["is_default"] else "No", row["name"], row.get("updated_at") or ""])

    def selected_subject_id() -> int:
        selection = subject_tree.selection()
        if not selection:
            return 0
        return int(subject_tree.item(selection[0], "values")[0])

    def selected_signature_id() -> int:
        selection = signature_tree.selection()
        if not selection:
            return 0
        return int(signature_tree.item(selection[0], "values")[0])

    def subject_actions(action: str) -> None:
        if action == "add":
            app.subject_service.save_subject(vars_["subject_entry"].get(), state["template_id"] or None)
            vars_["subject"].set(vars_["subject_entry"].get())
            vars_["subject_entry"].set("")
        elif action == "duplicate" and selected_subject_id():
            app.subject_service.duplicate_subject(selected_subject_id())
        elif action == "preferred" and selected_subject_id():
            row = next((r for r in app.subject_service.list_subjects(state["template_id"] or None) if r["id"] == selected_subject_id()), None)
            if row:
                app.subject_service.save_subject(row["subject"], row["template_id"], row.get("label") or "", row.get("ab_group") or "", True, row["id"])
                vars_["subject"].set(row["subject"])
        elif action == "random":
            subject = app.subject_service.random_subject(state["template_id"] or None)
            if subject:
                vars_["subject"].set(subject)
        elif action == "delete" and selected_subject_id():
            app.subject_service.delete_subject(selected_subject_id())
        load_subjects()
        mark_dirty()

    def signature_actions(action: str) -> None:
        if action == "add":
            name = simpledialog.askstring("Signature", "Signature name:", parent=frame)
            if not name:
                return
            html = simpledialog.askstring("Signature", "Signature HTML:", parent=frame) or ""
            app.signature_service.save_signature(name, html, app.template_service.html_to_text(html), False)
        elif action == "default" and selected_signature_id():
            sig = app.signature_service.get_signature(selected_signature_id())
            if sig:
                app.signature_service.save_signature(sig["name"], sig.get("html_body") or "", sig.get("plain_text_body") or "", True, sig["id"])
        elif action == "insert" and selected_signature_id():
            sig = app.signature_service.get_signature(selected_signature_id())
            if sig:
                insert_html(sig.get("html_body") or sig.get("plain_text_body") or "")
        elif action == "archive" and selected_signature_id():
            app.signature_service.archive_signature(selected_signature_id())
        load_signatures()

    template_tree.bind("<<TreeviewSelect>>", lambda _event: load_template(selected_template_id()) if confirm_unsaved() else None)
    vars_["search"].trace_add("write", lambda *_: refresh_templates())
    vars_["sort"].trace_add("write", lambda *_: refresh_templates())
    for key in ["name", "from_name", "from_email", "reply_to_email", "subject", "preheader"]:
        vars_[key].trace_add("write", lambda *_: mark_dirty())
    visual.bind("<<Modified>>", lambda event: (visual.edit_modified(False), mark_dirty()))
    source.bind("<<Modified>>", lambda event: (source.edit_modified(False), mark_dirty()))

    subject_tab.subject_actions = subject_actions
    signature_tab.signature_actions = signature_actions
    refresh_templates()
    load_signatures()
    schedule_autosave()


def _field(parent: ttk.Frame, label: str, variable: tk.StringVar, row: int, col: int, columnspan: int = 1) -> None:
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(parent, textvariable=variable).grid(row=row, column=col + 1, columnspan=columnspan, sticky="ew", pady=4)


def _configure_text_tags(text: tk.Text) -> None:
    text.tag_configure("bold", font=("Segoe UI", 12, "bold"))
    text.tag_configure("italic", font=("Segoe UI", 12, "italic"))
    text.tag_configure("underline", underline=True)


def _set_text(widget: tk.Text, value: str) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", value)
    widget.configure(state="disabled")


def _clear_tree(tree: ttk.Treeview) -> None:
    for item in tree.get_children():
        tree.delete(item)


def _build_subject_lab(parent: ttk.Frame, app, state: dict, vars_: dict, load_subjects, mark_dirty) -> None:
    ttk.Label(parent, text="Subject Line Lab", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
    ttk.Entry(parent, textvariable=vars_["subject_entry"]).grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 8))
    for idx, (label, action) in enumerate([
        ("Save", "add"),
        ("Duplicate", "duplicate"),
        ("Random", "random"),
        ("Preferred", "preferred"),
        ("Delete", "delete"),
    ]):
        ttk.Button(parent, text=label, command=lambda a=action: parent.subject_actions(a)).grid(row=2 + idx // 3, column=idx % 3, sticky="ew", padx=3, pady=3)


def _build_signature_tab(parent: ttk.Frame, app, vars_: dict, load_signatures, insert_signature) -> None:
    ttk.Label(parent, text="Signatures", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
    for idx, (label, action) in enumerate([
        ("Create", "add"),
        ("Default", "default"),
        ("Insert", "insert"),
        ("Archive", "archive"),
    ]):
        ttk.Button(parent, text=label, command=lambda a=action: parent.signature_actions(a)).grid(row=1 + idx // 3, column=idx % 3, sticky="ew", padx=3, pady=3)
