import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from app.design_system.customtkinter_adapter import combobox as ctk_combobox
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.components import PageHeader, table as design_table
from app.design_system.icons import icon_text as design_icon_text
from app.design_system.layout import LAYOUT
from app.design_system.tables import TABLE_TAGS
from app.design_system.theme import active_theme
from app.design_system.tooltips import help_text, tooltip
from app.help.page_intros import get_page_intro
from app.help.preferences import guided_configuration_enabled, learning_mode_enabled
from app.services.operation_tracker import OperationSnapshot
from app.ui.components.help_icon import HelpIcon, attach_help
from app.ui.components.modern_table import ModernTable
from app.ui.components.recommendation_panel import RecommendationPanel


def clear_frame(frame: tk.Widget) -> None:
    for child in frame.winfo_children():
        child.destroy()


def section(parent: tk.Widget, title: str, subtitle: str = "") -> ctk.CTkFrame:
    theme = active_theme()
    frame = ctk_frame(parent, theme, "background")
    frame.columnconfigure(0, weight=1)
    intro = get_page_intro(title) if learning_mode_enabled() else ""
    PageHeader(frame, title, subtitle, theme=theme, intro=intro).grid(
        row=0,
        column=0,
        sticky="ew",
        padx=theme.spacing.page_padding,
        pady=(16, 12),
    )
    return frame


def labeled_entry(
    parent: tk.Widget,
    label: str,
    row: int,
    column: int = 0,
    width: int = 28,
    show: str = "",
    recommended: str = "",
    explanation: str = "",
) -> tk.StringVar:
    theme = active_theme()
    var = tk.StringVar()
    label_widget = ctk_label(parent, theme, label, role="body", variant="surface")
    label_widget.grid(row=row, column=column, sticky="w", padx=(0, theme.spacing.md), pady=theme.spacing.sm)
    entry = ctk_entry(parent, theme, var, width=max(180, width * 8), show=show)
    entry.grid(row=row, column=column + 1, sticky="ew", pady=theme.spacing.sm)
    attach_help(entry, label)
    tooltip(label_widget, help_text(label, recommended, explanation or f"Enter {label.lower()}."))
    HelpIcon(parent, label).grid(row=row, column=column + 2, sticky="w", padx=(theme.spacing.sm, 0), pady=theme.spacing.sm)
    return var


def labeled_combo(
    parent: tk.Widget,
    label: str,
    row: int,
    values: list[str],
    column: int = 0,
    recommended: str = "",
    explanation: str = "",
) -> tk.StringVar:
    theme = active_theme()
    var = tk.StringVar(value=values[0] if values else "")
    label_widget = ctk_label(parent, theme, label, role="body", variant="surface")
    label_widget.grid(row=row, column=column, sticky="w", padx=(0, theme.spacing.md), pady=theme.spacing.sm)
    combo = ctk_combobox(parent, theme, var, values)
    combo.grid(row=row, column=column + 1, sticky="ew", pady=theme.spacing.sm)
    attach_help(combo, label)
    tooltip(label_widget, help_text(label, recommended, explanation or f"Choose {label.lower()}."))
    HelpIcon(parent, label).grid(row=row, column=column + 2, sticky="w", padx=(theme.spacing.sm, 0), pady=theme.spacing.sm)
    return var


def build_tree(parent: tk.Widget, columns: tuple[str, ...], headings: tuple[str, ...] | None = None, height: int = 12) -> ModernTable:
    tree = design_table(parent, columns, headings=headings, height=height)
    for column in columns:
        tree.column(column, width=LAYOUT.default_table_column_width, minwidth=LAYOUT.min_table_column_width, stretch=True)
    tree.grid(row=0, column=0, sticky="nsew")
    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)
    return tree


def clear_tree(tree: ttk.Treeview) -> None:
    if hasattr(tree, "clear"):
        tree.clear()
        return
    for item in tree.get_children():
        tree.delete(item)


def insert_table_row(tree: ttk.Treeview, values: list | tuple) -> str:
    tag = TABLE_TAGS["even"] if len(tree.get_children()) % 2 == 0 else TABLE_TAGS["odd"]
    return tree.insert("", "end", values=list(values), tags=(tag,))


def insert_empty_row(tree: ttk.Treeview, message: str, columns: tuple[str, ...]) -> str:
    values = [""] * len(columns)
    if values:
        values[min(1, len(values) - 1)] = message
    return tree.insert("", "end", values=values, tags=(TABLE_TAGS["empty"],))


def fill_tree(tree: ttk.Treeview, rows: list[dict], columns: tuple[str, ...], empty_message: str = "") -> None:
    clear_tree(tree)
    if not rows:
        insert_empty_row(tree, empty_message or "No records to show yet.", columns)
        return
    for row in rows:
        insert_table_row(tree, [row.get(column, "") for column in columns])


def icon_text(icon_key: str, text: str) -> str:
    return design_icon_text(icon_key, text)


class StatusBar(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget) -> None:
        theme = active_theme()
        self.theme = theme
        super().__init__(
            parent,
            fg_color=theme.palette.surface,
            corner_radius=0,
        )
        self.columnconfigure(0, weight=1)
        self.label = ctk.CTkLabel(
            self,
            text="Ready",
            anchor="w",
            fg_color=theme.palette.surface,
            text_color=theme.palette.text_muted,
            font=(theme.typography.family, theme.typography.caption),
        )
        self.label.grid(row=0, column=0, sticky="ew", padx=(12, 8), pady=3)
        self.progress = ctk.CTkProgressBar(
            self,
            height=6,
            corner_radius=3,
            progress_color=theme.palette.primary,
            fg_color=theme.palette.border_soft,
            mode="determinate",
        )
        self.progress.grid(row=0, column=1, sticky="e", padx=(0, 12), pady=3)
        self.progress.set(0)
        self.progress.grid_remove()
        self._indeterminate = False

    def set(self, message: str) -> None:
        self.label.configure(text=message)

    def show_operation(self, snapshot: OperationSnapshot) -> None:
        if not snapshot.active:
            self.clear_operation()
            return
        self.label.configure(text=snapshot.label)
        self.progress.grid()
        percent = snapshot.percent
        if percent is None or snapshot.indeterminate:
            if not self._indeterminate:
                self.progress.configure(mode="indeterminate")
                self.progress.start()
                self._indeterminate = True
            return
        if self._indeterminate:
            self.progress.stop()
            self.progress.configure(mode="determinate")
            self._indeterminate = False
        self.progress.set(percent)

    def clear_operation(self) -> None:
        if self._indeterminate:
            self.progress.stop()
            self.progress.configure(mode="determinate")
            self._indeterminate = False
        self.progress.set(0)
        self.progress.grid_remove()
        self.label.configure(text="Ready")
