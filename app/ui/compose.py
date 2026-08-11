import re
import tkinter as tk
from tkinter import colorchooser, messagebox

import customtkinter as ctk

from app.design_system import components as ds
from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import combobox as ctk_combobox
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.customtkinter_adapter import textbox as ctk_textbox
from app.design_system.dialogs import choose_option
from app.ui.email_authoring import MERGE_TAGS
from app.ui.shared import build_tree, clear_tree, insert_empty_row, insert_table_row


TEMPLATE_COLUMNS = ("favorite", "name", "category", "subject", "updated_at", "times_used")
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
IMG_RE = re.compile(r"<img\b", re.I)


def build(parent: tk.Widget, app) -> None:
    theme = app.theme
    palette = theme.palette
    space = theme.spacing
    frame = ctk_frame(parent, theme, "background")
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)

    state = {
        "source_template_id": None,
        "placeholder_visible": True,
        "last_autosaved": "Not yet",
        "autosave_job": None,
        "autosave_active": False,
    }
    fields = {
        "subject": tk.StringVar(),
        "preheader": tk.StringVar(),
        "from_email": tk.StringVar(),
        "from_name": tk.StringVar(value="SafeSend Workspace"),
    }
    metrics = {
        "saved": tk.StringVar(value="Unsaved"),
        "words": tk.StringVar(value="0 words"),
        "characters": tk.StringVar(value="0 characters"),
        "health": tk.StringVar(value="Health 21%"),
        "autosaved": tk.StringVar(value="Last autosaved: Not yet"),
    }
    smart_panels: dict[str, ctk.CTkFrame | ctk.CTkTextbox] = {}
    tabs_ref: dict[str, ctk.CTkTabview] = {}

    header = ctk_frame(frame, theme, "background")
    header.grid(row=0, column=0, sticky="ew", padx=space.page_padding, pady=(16, 10))
    header.columnconfigure(0, weight=1)
    title_row = ctk_frame(header, theme, "background")
    title_row.grid(row=0, column=0, sticky="w")
    ds.icon_label(title_row, "compose", theme=theme, text_color=palette.primary, size=28, surface="transparent").pack(side="left", padx=(0, space.sm))
    ctk_label(title_row, theme, "Compose", role="page_title", variant="background").pack(side="left")
    ctk_label(header, theme, "Email Composer", role="caption", variant="background", text_color=palette.text_muted).grid(row=1, column=0, sticky="w", pady=(2, 0))

    action_row = ctk_frame(header, theme, "background")
    action_row.pack(in_=title_row, side="left", padx=(42, 0))
    action_specs = [
        ("Restore Draft", lambda: restore_draft(), "restore", "secondary", 122),
        ("Save Draft", lambda: save_draft("Draft saved."), "save", "primary", 112),
        ("Send Test", lambda: messagebox.showinfo("Send Test", "Test sending will be connected when the sending engine is added.", parent=frame), "send", "secondary", 104),
        ("Preview", lambda: set_sidebar_tab("Preview"), "preview", "secondary", 92),
        ("Use Template", lambda: TemplatePicker(frame, app, load_template), "templates", "secondary", 124),
    ]
    for label, command, icon, variant, width in reversed(action_specs):
        ctk_button(action_row, theme, label, command=command, icon=icon, variant=variant, width=width, height=34).pack(side="left", padx=(0, 6))

    content = ctk_frame(frame, theme, "background")
    content.grid(row=1, column=0, sticky="nsew", padx=space.page_padding, pady=(0, space.page_padding))
    content.columnconfigure(0, weight=3, uniform="compose_regions")
    content.columnconfigure(1, weight=1, uniform="compose_regions")
    content.rowconfigure(0, weight=1)

    composer = ctk.CTkFrame(
        content,
        fg_color=palette.surface,
        corner_radius=4,
        border_width=1,
        border_color=palette.border_soft,
    )
    composer.grid(row=0, column=0, sticky="nsew", padx=(0, space.md))
    composer.columnconfigure(0, weight=1)
    composer.rowconfigure(2, weight=1)

    field_header = ctk.CTkFrame(composer, fg_color=palette.surface, corner_radius=0)
    field_header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
    field_header.columnconfigure(0, weight=1)
    field_intro = ctk.CTkFrame(field_header, fg_color="transparent", corner_radius=0)
    field_intro.grid(row=0, column=0, sticky="ew", padx=space.md, pady=(space.md, space.sm))
    field_intro.columnconfigure(0, weight=1)
    ctk_label(field_intro, theme, "Message Details", role="panel_title", variant="card", fg_color="transparent").grid(row=0, column=0, sticky="w")
    ctk_label(
        field_intro,
        theme,
        "Keep sender identity, subject, and inbox preview text close to the editor.",
        role="caption",
        variant="card",
        text_color=palette.text_muted,
        fg_color="transparent",
    ).grid(row=1, column=0, sticky="w", pady=(2, 0))
    field_grid = ctk.CTkFrame(field_header, fg_color=palette.surface_alt, corner_radius=4, border_width=1, border_color=palette.border_soft)
    field_grid.grid(row=1, column=0, sticky="ew", padx=space.md, pady=(0, space.md))
    for col in range(4):
        field_grid.columnconfigure(col, weight=1 if col in {1, 3} else 0)
    _compact_field(field_grid, theme, "Subject", fields["subject"], 0, 0)
    _compact_field(field_grid, theme, "Preheader", fields["preheader"], 0, 2)
    _compact_field(field_grid, theme, "From Email", fields["from_email"], 1, 0)
    _compact_field(field_grid, theme, "From Name", fields["from_name"], 1, 2)

    toolbar = ctk.CTkFrame(composer, fg_color=palette.surface_alt, corner_radius=0, border_width=0)
    toolbar.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 0))
    toolbar.grid_columnconfigure(99, weight=1)
    font_var = tk.StringVar(value="Segoe UI")
    size_var = tk.StringVar(value="14")
    toolbar_left = ctk.CTkFrame(toolbar, fg_color="transparent", corner_radius=0)
    toolbar_left.grid(row=0, column=0, sticky="w", padx=space.md, pady=8)
    ctk_combobox(toolbar_left, theme, font_var, ["Segoe UI", "Arial", "Georgia", "Tahoma", "Verdana"], width=118, height=34).pack(side="left", padx=(0, 4))
    ctk_combobox(toolbar_left, theme, size_var, ["12", "14", "16", "18", "22"], width=60, height=34).pack(side="left", padx=(0, 8))
    toolbar_actions = [
        ("B", lambda: wrap_selection("<strong>", "</strong>"), 38),
        ("I", lambda: wrap_selection("<em>", "</em>"), 38),
        ("U", lambda: wrap_selection("<u>", "</u>"), 38),
        ("Color", lambda: pick_color(), 48),
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
        ("Sig", lambda: insert_default_signature(), 40),
        ("Undo", lambda: undo(), 48),
        ("Redo", lambda: redo(), 46),
    ]
    for label, command, width in toolbar_actions:
        ctk_button(toolbar_left, theme, label, command=command, width=width, height=34).pack(side="left", padx=(0, 4))
    ctk_combobox(
        toolbar,
        theme,
        tk.StringVar(value="Insert"),
        ["CTA", "Table", "Divider", "Countdown", "Social", "Signature", "Recent Block"],
        command=lambda value: quick_insert(value),
        width=86,
        height=34,
    ).grid(row=0, column=99, sticky="e", padx=(2, space.md), pady=8)

    editor_shell = ctk.CTkFrame(composer, fg_color=palette.surface, corner_radius=0)
    editor_shell.grid(row=2, column=0, sticky="nsew", padx=space.md, pady=(space.md, 0))
    editor_shell.columnconfigure(0, weight=1)
    editor_shell.rowconfigure(1, weight=1)
    ctk_label(editor_shell, theme, "Message Body", role="panel_title", variant="card", fg_color="transparent").grid(row=0, column=0, sticky="w", pady=(0, space.sm))
    editor = ctk_textbox(
        editor_shell,
        theme,
        height=500,
        wrap="word",
        undo=True,
        fg_color=palette.surface,
        border_width=1,
        border_color=palette.border_soft,
    )
    editor.grid(row=1, column=0, sticky="nsew")
    editor.insert("1.0", "Write your email here...")
    editor.configure(text_color=palette.placeholder)

    status = ctk.CTkFrame(composer, fg_color=palette.surface_alt, corner_radius=0, height=34)
    status.grid(row=3, column=0, sticky="ew", padx=0, pady=(space.sm, 0))
    status.grid_propagate(False)
    status.columnconfigure(5, weight=1)
    for index, key in enumerate(["saved", "words", "characters", "health", "autosaved"]):
        ctk_label(status, theme, textvariable=metrics[key], role="caption", variant="surface", text_color=palette.text_muted).grid(
            row=0,
            column=index,
            sticky="w",
            padx=(space.md if index == 0 else 0, space.md),
            pady=7,
        )

    sidebar = ctk.CTkFrame(
        content,
        fg_color=palette.surface,
        corner_radius=4,
        border_width=1,
        border_color=palette.border_soft,
    )
    sidebar.grid(row=0, column=1, sticky="nsew")
    sidebar.columnconfigure(0, weight=1)
    sidebar.rowconfigure(1, weight=1)
    ctk_label(sidebar, theme, "Smart Sidebar", role="panel_title", variant="card").grid(row=0, column=0, sticky="w", padx=space.md, pady=(space.md, 2))
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
    tabs.grid(row=1, column=0, sticky="nsew", padx=space.md, pady=(space.xs, space.md))
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
            smart_panels[tab_name] = preview
        else:
            panel = ctk.CTkScrollableFrame(tab, fg_color=palette.surface, corner_radius=0)
            panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            panel.columnconfigure(0, weight=1)
            smart_panels[tab_name] = panel
    _sync_tab_text(tabs, theme)

    def focus_editor(_event=None) -> None:
        if state["placeholder_visible"]:
            editor.delete("1.0", "end")
            editor.configure(text_color=palette.text)
            state["placeholder_visible"] = False

    def restore_placeholder(_event=None) -> None:
        if not editor.get("1.0", "end-1c").strip():
            state["placeholder_visible"] = True
            editor.delete("1.0", "end")
            editor.insert("1.0", "Write your email here...")
            editor.configure(text_color=palette.placeholder)

    def body_html() -> str:
        return "" if state["placeholder_visible"] else editor.get("1.0", "end-1c")

    def mark_dirty(_event=None) -> None:
        metrics["saved"].set("Unsaved")
        refresh_analysis()

    def current_values() -> dict:
        html = body_html()
        return {
            "name": "Working Compose Draft",
            "subject": fields["subject"].get(),
            "preheader": fields["preheader"].get(),
            "from_email": fields["from_email"].get(),
            "from_name": fields["from_name"].get(),
            "reply_to_email": "",
            "html_body": html,
            "plain_text_body": app.template_service.html_to_text(html),
        }

    def load_template(template: dict) -> None:
        state["source_template_id"] = template["id"]
        app.template_service.increment_used(template["id"])
        for key in fields:
            fields[key].set(template.get(key) or "")
        state["placeholder_visible"] = False
        editor.configure(text_color=palette.text)
        editor.delete("1.0", "end")
        editor.insert("1.0", template.get("html_body") or template.get("plain_text_body") or "")
        metrics["saved"].set("Working copy")
        refresh_analysis()
        app.status.set(f"Loaded working copy from {template['name']}.")

    parent._safesend_load_template = load_template

    def save_draft(message: str) -> None:
        app.draft_service.save_draft(current_values(), state["source_template_id"])
        metrics["saved"].set("Saved")
        state["last_autosaved"] = "Saved just now"
        metrics["autosaved"].set("Last autosaved: just now")
        app.status.set(message)

    def restore_draft() -> None:
        drafts = app.draft_service.list_drafts(state["source_template_id"])
        if not drafts:
            messagebox.showinfo("Restore Draft", "No drafts are available.", parent=frame)
            return
        labels = [f"{draft['id']} - {draft['saved_at']} - {draft.get('name') or 'Untitled'}" for draft in drafts]
        choice = choose_option(frame, "Restore Draft", "Choose a saved draft to restore.", labels)
        if not choice:
            return
        draft = app.draft_service.get_draft(int(choice.split(" - ", 1)[0]))
        if not draft:
            return
        for key in fields:
            fields[key].set(draft.get(key) or "")
        state["placeholder_visible"] = False
        editor.configure(text_color=palette.text)
        editor.delete("1.0", "end")
        editor.insert("1.0", draft.get("html_body") or "")
        metrics["saved"].set("Saved")
        refresh_analysis()
        app.status.set("Draft restored.")

    def insert_html(html: str) -> None:
        focus_editor()
        editor.insert("insert", html)
        mark_dirty()

    def quick_insert(value: str) -> None:
        snippets = {
            "CTA": '<a class="button" href="https://example.com">Start now</a>',
            "Table": "<table><tr><td>Feature</td><td>Benefit</td></tr></table>",
            "Divider": "<hr>",
            "Countdown": "{{Countdown}}",
            "Social": "{{SocialLinks}}",
            "Signature": "{{Signature}}",
            "Recent Block": "<p>Thanks for taking a look.</p>",
        }
        insert_html(snippets.get(value, ""))

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
        color = colorchooser.askcolor(parent=frame)[1]
        if color:
            wrap_selection(f'<span style="color:{color};">', "</span>")

    def insert_default_signature() -> None:
        signature = app.signature_service.default_signature()
        if signature:
            insert_html(signature.get("html_body") or signature.get("plain_text_body") or "")
        else:
            messagebox.showinfo("Signature", "No default signature is configured.", parent=frame)

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
        _render_smart_panels(app, theme, smart_panels, fields, html, text, analysis, health)

    def autosave() -> None:
        state["autosave_job"] = None
        if not state.get("autosave_active") or not frame.winfo_exists():
            return
        try:
            values = current_values()
            if any((values.get(key) or "").strip() for key in ["subject", "from_email", "html_body"]):
                app.draft_service.save_draft(values, state["source_template_id"])
                state["last_autosaved"] = "just now"
                metrics["autosaved"].set("Last autosaved: just now")
                metrics["saved"].set("Autosaved")
        finally:
            schedule_autosave()

    def schedule_autosave() -> None:
        if state.get("autosave_job") or not state.get("autosave_active") or not frame.winfo_exists():
            return
        state["autosave_job"] = frame.after(120000, autosave)

    def cancel_autosave() -> None:
        job = state.get("autosave_job")
        if job:
            try:
                frame.after_cancel(job)
            except tk.TclError:
                pass
            state["autosave_job"] = None

    def on_show() -> None:
        state["autosave_active"] = True
        schedule_autosave()

    def on_hide() -> None:
        state["autosave_active"] = False
        cancel_autosave()

    frame.on_show = on_show
    frame.on_hide = on_hide
    frame.cleanup = on_hide

    for variable in fields.values():
        variable.trace_add("write", lambda *_: mark_dirty())
    editor.bind("<FocusIn>", focus_editor, add="+")
    editor.bind("<FocusOut>", restore_placeholder, add="+")
    editor.bind("<KeyRelease>", mark_dirty, add="+")
    on_show()
    refresh_analysis()


class TemplatePicker:
    def __init__(self, parent: tk.Widget, app, on_use) -> None:
        self.app = app
        self.theme = app.theme
        self.on_use = on_use
        self.search = tk.StringVar()
        self.category = tk.StringVar(value="All")
        self.mode = tk.StringVar(value="Recent")
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Use Template")
        self.window.geometry("920x620")
        self.window.minsize(760, 480)
        self.window.configure(fg_color=self.theme.palette.background)
        self.window.transient(parent)
        self.window.grab_set()
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = ctk_frame(self.window, self.theme, "background")
        root.pack(fill="both", expand=True, padx=self.theme.spacing.page_padding, pady=self.theme.spacing.page_padding)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)
        ctk_label(root, self.theme, "Use Template", role="page_title").grid(row=0, column=0, sticky="w")
        ctk_label(root, self.theme, "Pick a reusable template, then continue editing a working copy in Compose.", role="caption").grid(row=1, column=0, sticky="w", pady=(2, 12))
        toolbar = ds.Toolbar(root, theme=self.theme)
        toolbar.grid(row=2, column=0, sticky="new")
        ctk_entry(toolbar, self.theme, self.search, placeholder_text="Search templates...", width=260).pack(side="left", padx=(self.theme.spacing.sm, 6), pady=self.theme.spacing.sm)
        ctk_combobox(toolbar, self.theme, self.category, ["All", *self.app.template_service.categories()], width=180).pack(side="left", padx=6, pady=self.theme.spacing.sm)
        ctk_combobox(toolbar, self.theme, self.mode, ["Recent", "Favorites"], width=132).pack(side="left", padx=6, pady=self.theme.spacing.sm)
        ctk_button(toolbar, self.theme, "Clear", command=self.clear_filters, icon="clear", width=82).pack(side="left", padx=6, pady=self.theme.spacing.sm)
        ctk_button(toolbar, self.theme, "Use Template", command=self.use_selected, variant="primary", icon="templates", width=128).pack(side="right", padx=(6, self.theme.spacing.sm), pady=self.theme.spacing.sm)

        table_frame = ctk_frame(root, self.theme, "card")
        table_frame.grid(row=3, column=0, sticky="nsew", pady=(self.theme.spacing.md, 0))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.table = build_tree(table_frame, TEMPLATE_COLUMNS, headings=("Star", "Template Name", "Category", "Subject", "Last Modified", "Used"), height=10)
        self.table.column("favorite", width=56, stretch=False)
        self.table.column("times_used", width=70, stretch=False)
        self.table.bind("<Double-1>", lambda _event: self.use_selected())
        self.search.trace_add("write", lambda *_: self.refresh())
        self.category.trace_add("write", lambda *_: self.refresh())
        self.mode.trace_add("write", lambda *_: self.refresh())

    def clear_filters(self) -> None:
        self.search.set("")
        self.category.set("All")
        self.mode.set("Recent")

    def refresh(self) -> None:
        clear_tree(self.table)
        sort = "favorite DESC" if self.mode.get() == "Favorites" else "last_used_at DESC"
        rows = self.app.template_service.filtered_templates(self.search.get(), self.category.get(), "All", include_archived=False, sort_by=sort)
        if self.mode.get() == "Favorites":
            rows = [row for row in rows if row.get("favorite")]
        if not rows:
            insert_empty_row(self.table, "No templates found. Create reusable templates from the Templates screen.", TEMPLATE_COLUMNS)
            return
        for row in rows:
            insert_table_row(self.table, [
                "Star" if row.get("favorite") else "",
                row.get("name") or "",
                row.get("category") or "General",
                row.get("subject") or "",
                row.get("updated_at") or "",
                row.get("times_used") or 0,
            ])

    def selected_template(self) -> dict | None:
        selection = self.table.selection()
        if not selection:
            return None
        values = self.table.item(selection[0], "values")
        if not values or values[1].startswith("No templates"):
            return None
        rows = self.app.template_service.filtered_templates(self.search.get(), self.category.get(), "All", include_archived=False)
        return next((row for row in rows if row.get("name") == values[1]), None)

    def use_selected(self) -> None:
        template = self.selected_template()
        if not template:
            messagebox.showinfo("Use Template", "Select a template first.", parent=self.window)
            return
        self.on_use(template)
        self.window.destroy()


def _compact_field(parent: tk.Widget, theme, label_text: str, variable: tk.StringVar, row: int, column: int) -> None:
    ctk_label(
        parent,
        theme,
        label_text,
        role="caption",
        variant="surface",
        text_color=theme.palette.text_muted,
        fg_color="transparent",
    ).grid(
        row=row,
        column=column,
        sticky="w",
        padx=(theme.spacing.md if column == 0 else theme.spacing.lg, theme.spacing.sm),
        pady=(8, 8),
    )
    ctk_entry(parent, theme, variable, height=34).grid(row=row, column=column + 1, sticky="ew", padx=(0, theme.spacing.md), pady=(8, 8))


def _render_smart_panels(app, theme, panels: dict, fields: dict, html: str, text: str, analysis, health: int) -> None:
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
    personalization_rows = [("Available Merge Fields", f"{len(MERGE_TAGS)} fields", "info"), ("Detected", ", ".join(sorted(set(merge_fields))) if merge_fields else "None yet", "success" if merge_fields else "warning")]
    _render_rows(panels.get("Personalization"), theme, personalization_rows + [(tag, "Insert from toolbar", "info") for tag in MERGE_TAGS])
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


def _sync_tab_text(tabs: ctk.CTkTabview, theme) -> None:
    try:
        selected = tabs.get()
        tabs._segmented_button.configure(command=lambda value: (tabs.set(value), _sync_tab_text(tabs, theme)))
        for label_text, button in getattr(tabs._segmented_button, "_buttons_dict", {}).items():
            button.configure(text_color=theme.palette.surface if label_text == selected else theme.palette.text)
    except (AttributeError, tk.TclError):
        pass
