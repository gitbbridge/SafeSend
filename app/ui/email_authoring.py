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
from app.design_system.theme import active_theme


MERGE_TAGS = [
    "{{FirstName}}",
    "{{LastName}}",
    "{{Company}}",
    "{{Email}}",
    "{{State}}",
    "{{City}}",
    "{{Custom1}}",
    "{{Custom2}}",
    "{{Custom3}}",
    "{{Unsubscribe}}",
]

URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
IMG_RE = re.compile(r"<img\b", re.I)


class EmailAuthoringWorkspace(ctk.CTkFrame):
    def __init__(
        self,
        parent: tk.Widget,
        app,
        *,
        include_template_fields: bool = False,
        show_smart_sidebar: bool = True,
        editor_height: int = 450,
    ) -> None:
        self.theme = active_theme()
        self.app = app
        self.include_template_fields = include_template_fields
        self.show_smart_sidebar = show_smart_sidebar
        self.vars = {
            "name": tk.StringVar(),
            "category": tk.StringVar(value="General"),
            "status": tk.StringVar(value="Draft"),
            "favorite": tk.BooleanVar(value=False),
            "subject": tk.StringVar(),
            "preheader": tk.StringVar(),
            "from_email": tk.StringVar(),
            "from_name": tk.StringVar(),
        }
        self.metric_vars = {
            "words": tk.StringVar(value="0 words"),
            "characters": tk.StringVar(value="0 characters"),
            "health": tk.StringVar(value="21%"),
            "saved": tk.StringVar(value="Unsaved"),
        }
        self.preview_box: ctk.CTkTextbox | None = None
        self.health_list: ctk.CTkFrame | None = None
        self.personalization_list: ctk.CTkFrame | None = None
        self.links_list: ctk.CTkFrame | None = None
        self.spam_list: ctk.CTkFrame | None = None
        self.sidebar_tabs: ctk.CTkTabview | None = None
        super().__init__(parent, fg_color=self.theme.palette.background, corner_radius=0)
        self.columnconfigure(0, weight=3)
        if show_smart_sidebar:
            self.columnconfigure(1, weight=1, minsize=320)
        self.rowconfigure(3, weight=1)
        self._build(editor_height)
        for variable in self.vars.values():
            variable.trace_add("write", lambda *_: self.mark_dirty())

    def _build(self, editor_height: int) -> None:
        left = ctk_frame(self, self.theme, "background")
        left.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=(0, self.theme.spacing.md))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(3, weight=1)

        self._build_details(left).grid(row=0, column=0, sticky="ew", pady=(0, self.theme.spacing.md))
        self._build_toolbar(left).grid(row=1, column=0, sticky="ew", pady=(0, self.theme.spacing.md))
        self._build_quick_insert(left).grid(row=2, column=0, sticky="ew", pady=(0, self.theme.spacing.md))
        self._build_editor(left, editor_height).grid(row=3, column=0, sticky="nsew")

        if self.show_smart_sidebar:
            sidebar = ds.Card(self, theme=self.theme, title="Smart Sidebar", subtitle="Preview, validate and improve the message.")
            sidebar.grid(row=0, column=1, rowspan=4, sticky="nsew")
            sidebar.rowconfigure(sidebar.content_row, weight=1)
            sidebar.columnconfigure(0, weight=1)
            self._build_smart_sidebar(sidebar).grid(
                row=sidebar.content_row,
                column=0,
                sticky="nsew",
                padx=self.theme.spacing.card_padding,
                pady=(0, self.theme.spacing.card_padding),
            )

    def _build_details(self, parent: tk.Widget) -> ds.Card:
        card = ds.Card(parent, theme=self.theme, title="Message Details", subtitle="Keep sender, subject and preview text close to the editor.")
        for col in range(4):
            card.columnconfigure(col, weight=1)
        row = card.content_row
        if self.include_template_fields:
            _field(card, "Template Name", self.vars["name"], row, 0)
            _combo_field(card, "Category", self.vars["category"], ["General", "Sales", "Follow Up", "Events", "Introductions", "Re-engagement", "Custom"], row, 2)
            row += 1
            _combo_field(card, "Status", self.vars["status"], ["Draft", "Active"], row, 0)
            ds.checkbox(card, "Favorite", self.vars["favorite"], theme=self.theme).grid(row=row, column=2, sticky="w", padx=(0, self.theme.spacing.md), pady=6)
            row += 1
        _field(card, "Subject", self.vars["subject"], row, 0)
        _field(card, "Preheader", self.vars["preheader"], row, 2)
        _field(card, "From Email", self.vars["from_email"], row + 1, 0)
        _field(card, "From Name", self.vars["from_name"], row + 1, 2)
        return card

    def _build_toolbar(self, parent: tk.Widget) -> ds.Card:
        card = ds.Card(parent, theme=self.theme, title="Email Toolbar", subtitle="Single toolbar for formatting and inserts.")
        body = ctk_frame(card, self.theme, "card", fg_color="transparent", border_width=0)
        body.grid(row=card.content_row, column=0, sticky="ew", padx=self.theme.spacing.card_padding, pady=(0, self.theme.spacing.card_padding))
        for idx in range(14):
            body.columnconfigure(idx, weight=0)
        font_var = tk.StringVar(value="Segoe UI")
        size_var = tk.StringVar(value="14")
        ctk_combobox(body, self.theme, font_var, ["Segoe UI", "Arial", "Georgia", "Tahoma", "Verdana"], width=140).grid(row=0, column=0, padx=(0, 6), pady=4)
        ctk_combobox(body, self.theme, size_var, ["12", "14", "16", "18", "22"], width=72).grid(row=0, column=1, padx=(0, 6), pady=4)
        actions = [
            ("B", lambda: self.wrap_selection("<strong>", "</strong>")),
            ("I", lambda: self.wrap_selection("<em>", "</em>")),
            ("U", lambda: self.wrap_selection("<u>", "</u>")),
            ("Color", self.pick_color),
            ("Left", lambda: self.insert_html('<p style="text-align:left;"></p>')),
            ("Center", lambda: self.insert_html('<p style="text-align:center;"></p>')),
            ("Right", lambda: self.insert_html('<p style="text-align:right;"></p>')),
            ("Bullets", lambda: self.insert_html("<ul><li>List item</li></ul>")),
            ("Link", lambda: self.insert_html('<a href="https://example.com">Link text</a>')),
            ("Image", lambda: self.insert_html('<img src="https://example.com/image.png" alt="">')),
            ("Table", lambda: self.insert_html("<table><tr><td>Column 1</td><td>Column 2</td></tr></table>")),
            ("Button", lambda: self.insert_html('<a class="button" href="https://example.com">Call to action</a>')),
            ("Divider", lambda: self.insert_html("<hr>")),
            ("Signature", self.insert_default_signature),
            ("Undo", self.undo),
            ("Redo", self.redo),
        ]
        col = 2
        for label, command in actions:
            width = 76 if len(label) > 5 else 50
            ctk_button(body, self.theme, label, command=command, width=width, height=34).grid(row=0, column=col, padx=(0, 6), pady=4)
            col += 1
        return card

    def _build_quick_insert(self, parent: tk.Widget) -> ds.Card:
        card = ds.Card(parent, theme=self.theme, title="Quick Insert", subtitle="Reusable content blocks are inserted at the cursor.")
        body = ctk_frame(card, self.theme, "card", fg_color="transparent", border_width=0)
        body.grid(row=card.content_row, column=0, sticky="ew", padx=self.theme.spacing.card_padding, pady=(0, self.theme.spacing.card_padding))
        inserts = [
            ("CTA", '<a class="button" href="https://example.com">Start now</a>'),
            ("Table", "<table><tr><td>Feature</td><td>Benefit</td></tr></table>"),
            ("Divider", "<hr>"),
            ("Countdown", "{{Countdown}}"),
            ("Social", "{{SocialLinks}}"),
            ("Signature", "{{Signature}}"),
            ("Recent Block", "<p>Thanks for taking a look.</p>"),
        ]
        for idx, (label_text, html) in enumerate(inserts):
            ctk_button(body, self.theme, label_text, command=lambda value=html: self.insert_html(value), icon="new", width=122).grid(row=0, column=idx, padx=(0, 6), pady=4)
        return card

    def _build_editor(self, parent: tk.Widget, editor_height: int) -> ds.Card:
        card = ds.Card(parent, theme=self.theme, title="Email Editor", subtitle="Start writing immediately. Use merge fields to personalize every message.")
        card.rowconfigure(card.content_row, weight=1)
        editor = ctk_textbox(card, self.theme, height=editor_height, wrap="word", undo=True)
        editor.grid(row=card.content_row, column=0, sticky="nsew", padx=self.theme.spacing.card_padding, pady=(0, 0))
        editor.bind("<KeyRelease>", lambda _event: self.mark_dirty(), add="+")
        self.editor = editor
        footer = ctk_frame(card, self.theme, "surface")
        footer.grid(row=card.content_row + 1, column=0, sticky="ew", padx=self.theme.spacing.card_padding, pady=self.theme.spacing.card_padding)
        footer.columnconfigure(4, weight=1)
        for idx, key in enumerate(["saved", "words", "characters", "health"]):
            ctk_label(footer, self.theme, textvariable=self.metric_vars[key], role="caption", variant="surface").grid(row=0, column=idx, sticky="w", padx=(self.theme.spacing.sm, self.theme.spacing.md), pady=6)
        return card

    def _build_smart_sidebar(self, parent: tk.Widget) -> ctk.CTkTabview:
        tabs = ctk.CTkTabview(
            parent,
            fg_color=self.theme.palette.surface,
            segmented_button_selected_color=self.theme.palette.primary,
            segmented_button_selected_hover_color=self.theme.palette.primary_dark,
            segmented_button_unselected_color=self.theme.palette.surface_alt,
            segmented_button_unselected_hover_color=self.theme.palette.hover,
            text_color=self.theme.palette.text,
            segmented_button_fg_color=self.theme.palette.surface_alt,
        )
        self.sidebar_tabs = tabs
        health = tabs.add("Health")
        preview = tabs.add("Preview")
        spam = tabs.add("Spam")
        personalization = tabs.add("Personalization")
        links = tabs.add("Links")
        for tab in [health, preview, spam, personalization, links]:
            tab.configure(fg_color=self.theme.palette.surface)
            tab.columnconfigure(0, weight=1)
        self.health_list = _list_panel(health, self.theme)
        self.health_list.grid(row=0, column=0, sticky="nsew")
        self.preview_box = ctk_textbox(preview, self.theme, height=520, wrap="word")
        self.preview_box.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.preview_box.configure(state="disabled")
        self.spam_list = _list_panel(spam, self.theme)
        self.spam_list.grid(row=0, column=0, sticky="nsew")
        self.personalization_list = _list_panel(personalization, self.theme)
        self.personalization_list.grid(row=0, column=0, sticky="nsew")
        merge_box = ctk_frame(personalization, self.theme, "card")
        merge_box.grid(row=1, column=0, sticky="ew", padx=4, pady=(8, 4))
        merge_box.columnconfigure(0, weight=1)
        for idx, tag in enumerate(MERGE_TAGS):
            ctk_button(merge_box, self.theme, tag, command=lambda value=tag: self.insert_html(value), variant="ghost", height=28, anchor="w").grid(row=idx, column=0, sticky="ew", padx=6, pady=1)
        self.links_list = _list_panel(links, self.theme)
        self.links_list.grid(row=0, column=0, sticky="nsew")
        try:
            tabs._segmented_button.configure(command=self._sidebar_tab_changed)
            self.after_idle(lambda: self._sidebar_tab_changed(tabs.get()))
        except (AttributeError, tk.TclError):
            pass
        return tabs

    def _sidebar_tab_changed(self, selected: str) -> None:
        if not self.sidebar_tabs:
            return
        try:
            self.sidebar_tabs.set(selected)
            button_dict = getattr(self.sidebar_tabs._segmented_button, "_buttons_dict", {})
            for label_text, button in button_dict.items():
                button.configure(text_color=self.theme.palette.surface if label_text == selected else self.theme.palette.text)
        except (AttributeError, tk.TclError):
            pass

    def get_values(self) -> dict:
        html = self.editor.get("1.0", "end-1c")
        return {
            "name": self.vars["name"].get().strip() or "Untitled Template",
            "category": self.vars["category"].get() or "General",
            "status": self.vars["status"].get() or "Draft",
            "favorite": bool(self.vars["favorite"].get()),
            "subject": self.vars["subject"].get(),
            "preheader": self.vars["preheader"].get(),
            "from_email": self.vars["from_email"].get(),
            "from_name": self.vars["from_name"].get(),
            "reply_to_email": "",
            "html_body": html,
            "plain_text_body": self.app.template_service.html_to_text(html),
        }

    def set_values(self, values: dict | None) -> None:
        values = values or {}
        for key in ["name", "category", "status", "subject", "preheader", "from_email", "from_name"]:
            if key in self.vars:
                self.vars[key].set(str(values.get(key) or ("General" if key == "category" else "Draft" if key == "status" else "")))
        self.vars["favorite"].set(bool(values.get("favorite")))
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", values.get("html_body") or values.get("plain_text_body") or "")
        self.metric_vars["saved"].set("Saved")
        self.update_analysis()

    def clear(self) -> None:
        self.set_values({"category": "General", "status": "Draft", "html_body": ""})
        self.metric_vars["saved"].set("Unsaved")

    def mark_dirty(self) -> None:
        self.metric_vars["saved"].set("Unsaved")
        self.update_analysis()

    def update_analysis(self) -> None:
        html = self.editor.get("1.0", "end-1c")
        text = self.app.template_service.html_to_text(html)
        words = len([word for word in text.split() if word.strip()])
        chars = len(text)
        self.metric_vars["words"].set(f"{words} words")
        self.metric_vars["characters"].set(f"{chars} characters")
        analysis = self.app.spam_analysis_service.analyze(self.vars["subject"].get(), html, self.vars["preheader"].get())
        health = max(0, min(100, 100 - analysis.score))
        self.metric_vars["health"].set(f"Health {health}%")
        self._render_sidebar(html, text, analysis, health)

    def _render_sidebar(self, html: str, text: str, analysis, health: int) -> None:
        if self.preview_box:
            self.preview_box.configure(state="normal")
            self.preview_box.delete("1.0", "end")
            self.preview_box.insert("1.0", f"Subject: {self.vars['subject'].get()}\nPreheader: {self.vars['preheader'].get()}\n\n{text}")
            self.preview_box.configure(state="disabled")
        links = URL_RE.findall(html)
        merge_fields = re.findall(r"{{[^}]+}}", html + self.vars["subject"].get() + self.vars["preheader"].get())
        _render_list(self.health_list, self.theme, [
            ("Overall Score", f"{health}%", "success" if health >= 75 else "warning"),
            ("Subject Score", "Good" if 24 <= len(self.vars["subject"].get()) <= 60 else "Needs review", "success" if 24 <= len(self.vars["subject"].get()) <= 60 else "warning"),
            ("Spam Score", str(analysis.score), "success" if analysis.score < 25 else "warning"),
            ("Readability", f"{len(text.splitlines()) or 1} sections", "info"),
            ("Missing Merge Fields", "None" if merge_fields else "Personalization optional", "success" if merge_fields else "warning"),
            ("Link Validation", f"{len(links)} links found", "success" if links else "warning"),
        ])
        warnings = analysis.warnings or ["No spam warnings detected."]
        _render_list(self.spam_list, self.theme, [(item, "", "warning" if analysis.warnings else "success") for item in warnings])
        _render_list(self.personalization_list, self.theme, [
            ("Available Merge Fields", f"{len(MERGE_TAGS)} fields", "info"),
            ("Detected", ", ".join(sorted(set(merge_fields))) if merge_fields else "None yet", "success" if merge_fields else "warning"),
        ])
        _render_list(self.links_list, self.theme, [
            ("Tracking Status", "Placeholder until sending engine is connected", "info"),
            ("Links Found", str(len(links)), "success" if links else "warning"),
            ("Images Found", str(len(IMG_RE.findall(html))), "info"),
        ])

    def insert_html(self, html: str) -> None:
        self.editor.insert("insert", html)
        self.mark_dirty()

    def wrap_selection(self, before: str, after: str) -> None:
        try:
            selected = self.editor.get("sel.first", "sel.last")
            self.editor.delete("sel.first", "sel.last")
            self.editor.insert("insert", f"{before}{selected}{after}")
        except tk.TclError:
            self.editor.insert("insert", f"{before}{after}")
        self.mark_dirty()

    def pick_color(self) -> None:
        color = colorchooser.askcolor(parent=self)[1]
        if color:
            self.wrap_selection(f'<span style="color:{color};">', "</span>")

    def insert_default_signature(self) -> None:
        signature = self.app.signature_service.default_signature()
        if signature:
            self.insert_html(signature.get("html_body") or signature.get("plain_text_body") or "")
        else:
            messagebox.showinfo("Signature", "No default signature is configured.", parent=self)

    def undo(self) -> None:
        try:
            self.editor.edit_undo()
        except tk.TclError:
            pass

    def redo(self) -> None:
        try:
            self.editor.edit_redo()
        except tk.TclError:
            pass


def _field(parent: tk.Widget, label_text: str, variable: tk.StringVar, row: int, column: int) -> None:
    theme = active_theme()
    ctk_label(parent, theme, label_text, role="caption", variant="card").grid(row=row, column=column, sticky="w", padx=(theme.spacing.card_padding, theme.spacing.sm), pady=6)
    ctk_entry(parent, theme, variable, width=260).grid(row=row, column=column + 1, sticky="ew", padx=(0, theme.spacing.card_padding), pady=6)


def _combo_field(parent: tk.Widget, label_text: str, variable: tk.StringVar, values: list[str], row: int, column: int) -> None:
    theme = active_theme()
    ctk_label(parent, theme, label_text, role="caption", variant="card").grid(row=row, column=column, sticky="w", padx=(theme.spacing.card_padding, theme.spacing.sm), pady=6)
    ctk_combobox(parent, theme, variable, values, width=220).grid(row=row, column=column + 1, sticky="ew", padx=(0, theme.spacing.card_padding), pady=6)


def _list_panel(parent: tk.Widget, theme) -> ctk.CTkFrame:
    frame = ctk_frame(parent, theme, "card", fg_color=theme.palette.surface)
    frame.columnconfigure(0, weight=1)
    return frame


def _render_list(parent: ctk.CTkFrame | None, theme, rows: list[tuple[str, str, str]]) -> None:
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
