import tkinter as tk

import customtkinter as ctk

from app.help.field_help import get_field_help
from app.design_system.theme import active_theme
from app.design_system.tooltips import tooltip
from app.ui.components.recommendation_panel import set_active_recommendation


class HelpIcon(ctk.CTkLabel):
    def __init__(self, parent: tk.Widget, setting_key: str) -> None:
        self.help = get_field_help(setting_key)
        theme = active_theme()
        super().__init__(parent, text="?", width=24, height=24, corner_radius=12, fg_color="transparent", text_color=theme.palette.info, cursor="question_arrow")
        tooltip(self, self.help.tooltip_text())
        self.bind("<Enter>", self._activate, add="+")
        self.bind("<Button-1>", self._activate, add="+")

    def _activate(self, _event=None) -> None:
        set_active_recommendation(self.help.setting_name)


def attach_help(widget: tk.Widget, setting_key: str) -> tk.Widget:
    if getattr(widget, "_safesend_help_attached", False):
        return widget
    field = get_field_help(setting_key)
    tooltip(widget, field.tooltip_text())
    widget.bind("<FocusIn>", lambda _event: set_active_recommendation(field.setting_name), add="+")
    widget.bind("<Enter>", lambda _event: set_active_recommendation(field.setting_name), add="+")
    setattr(widget, "_safesend_help_attached", True)
    return widget


def enhance_configurable_controls(root: tk.Widget) -> None:
    for child in root.winfo_children():
        setting = _setting_name_for(child)
        if setting:
            attach_help(child, setting)
        enhance_configurable_controls(child)


def _setting_name_for(widget: tk.Widget) -> str:
    widget_type = widget.winfo_class()
    if widget_type in {"TCombobox", "TEntry", "TSpinbox", "Spinbox", "Entry"}:
        label = _nearby_label(widget)
        return label or "Configuration setting"
    if widget_type in {"TCheckbutton", "TRadiobutton", "Checkbutton", "Radiobutton"}:
        try:
            text = widget.cget("text")
        except tk.TclError:
            text = ""
        return text or "Configuration toggle"
    return ""


def _nearby_label(widget: tk.Widget) -> str:
    try:
        info = widget.grid_info()
        row = int(info.get("row", -1))
        column = int(info.get("column", -1))
        parent = widget.master
        for sibling in parent.winfo_children():
            sibling_info = sibling.grid_info()
            if int(sibling_info.get("row", -2)) == row and int(sibling_info.get("column", -2)) == column - 1:
                if sibling.winfo_class() == "TLabel":
                    return str(sibling.cget("text"))
    except (tk.TclError, ValueError, TypeError):
        return ""
    return ""
