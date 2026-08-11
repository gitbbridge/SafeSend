from __future__ import annotations

import tkinter as tk
from tkinter import messagebox as tk_messagebox
from typing import Literal

import customtkinter as ctk

from app.design_system.components import button
from app.design_system.components import text_area
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import combobox as ctk_combobox
from app.design_system.theme import SafeSendTheme, active_theme
from app.design_system.typography import font


DialogKind = Literal["info", "success", "warning", "error", "confirm"]

_DIALOG_ROOT: tk.Widget | None = None
_INSTALLED = False


def install_dialogs(root: tk.Widget) -> None:
    global _DIALOG_ROOT, _INSTALLED
    _DIALOG_ROOT = root
    if _INSTALLED:
        return
    tk_messagebox.showinfo = lambda title=None, message=None, **kwargs: show_message(
        _parent_from_kwargs(kwargs), title or "Information", message or "", kind="info"
    )
    tk_messagebox.showwarning = lambda title=None, message=None, **kwargs: show_message(
        _parent_from_kwargs(kwargs), title or "Warning", message or "", kind="warning"
    )
    tk_messagebox.showerror = lambda title=None, message=None, **kwargs: show_message(
        _parent_from_kwargs(kwargs), title or "Error", message or "", kind="error"
    )
    tk_messagebox.askyesno = lambda title=None, message=None, **kwargs: ask_yes_no(
        _parent_from_kwargs(kwargs), title or "Confirm", message or ""
    )
    tk_messagebox.askokcancel = lambda title=None, message=None, **kwargs: ask_ok_cancel(
        _parent_from_kwargs(kwargs), title or "Confirm", message or ""
    )
    _INSTALLED = True


def show_message(parent: tk.Widget | None, title: str, message: str, *, kind: DialogKind = "info") -> str:
    _run_dialog(parent, title, message, kind=kind, buttons=(("OK", "primary", True),))
    return "ok"


def ask_yes_no(parent: tk.Widget | None, title: str, message: str) -> bool:
    result = _run_dialog(
        parent,
        title,
        message,
        kind="confirm",
        buttons=(("Yes", "primary", True), ("Cancel", "secondary", False)),
    )
    return bool(result)


def ask_ok_cancel(parent: tk.Widget | None, title: str, message: str) -> bool:
    result = _run_dialog(
        parent,
        title,
        message,
        kind="confirm",
        buttons=(("OK", "primary", True), ("Cancel", "secondary", False)),
    )
    return bool(result)


def ask_stop_processing(parent: tk.Widget | None, active_operation: str = "") -> bool:
    message = "SafeSend is currently processing. Closing now will interrupt the active operation."
    if active_operation:
        message = f"{message}\n\nCurrent operation: {active_operation}"
    result = _run_dialog(
        parent,
        "SafeSend is Processing",
        message,
        kind="warning",
        buttons=(("Keep Running", "primary", False), ("Stop Safely and Exit", "danger", True)),
    )
    return bool(result)


def prompt_text(parent: tk.Widget | None, title: str, prompt: str, initialvalue: str = "", *, multiline: bool = False) -> str | None:
    theme = active_theme()
    palette = theme.palette
    space = theme.spacing
    window = _dialog_window(parent, title, theme, width=560, height=330 if multiline else 260)
    result: dict[str, str | None] = {"value": None}
    value = tk.StringVar(value=initialvalue)

    shell = _shell(window, theme)
    _header(shell, theme, title, prompt, "info")

    field_frame = ctk.CTkFrame(shell, fg_color=palette.surface_alt, corner_radius=4, border_width=0)
    field_frame.grid(row=2, column=0, sticky="ew", padx=space.page_padding, pady=(0, space.md))
    field_frame.columnconfigure(0, weight=1)
    if multiline or "\n" in prompt:
        text = text_area(
            field_frame,
            theme=theme,
            height=96,
            placeholder="Enter details...",
        )
        text.grid(row=0, column=0, sticky="ew", padx=space.md, pady=space.md)
        text.insert("1.0", initialvalue)
        focus_widget = text
    else:
        entry = ctk_entry(field_frame, theme, value, placeholder_text="Placeholder")
        entry.grid(row=0, column=0, sticky="ew", padx=space.md, pady=space.md)
        focus_widget = entry

    def save() -> None:
        result["value"] = text.get("1.0", "end").strip() if multiline or "\n" in prompt else value.get()
        window.destroy()

    _footer(shell, theme, (("OK", "primary", save), ("Cancel", "secondary", window.destroy)))
    focus_widget.focus_set()
    window.bind("<Return>", lambda _event: save())
    window.bind("<Escape>", lambda _event: window.destroy())
    _wait(window, parent)
    return result["value"]


def prompt_fields(
    parent: tk.Widget | None,
    title: str,
    message: str,
    fields: tuple[tuple[str, str, str], ...],
    *,
    submit_text: str = "Save",
) -> dict[str, str] | None:
    theme = active_theme()
    palette = theme.palette
    space = theme.spacing
    window = _dialog_window(parent, title, theme, width=600, height=max(280, 190 + len(fields) * 58))
    result: dict[str, dict[str, str] | None] = {"value": None}
    values = {key: tk.StringVar(value=initial) for key, _label, initial in fields}

    shell = _shell(window, theme)
    _header(shell, theme, title, message, "info")
    form = ctk.CTkFrame(shell, fg_color=palette.surface_alt, corner_radius=4, border_width=0)
    form.grid(row=2, column=0, sticky="ew", padx=space.page_padding, pady=(0, space.md))
    form.columnconfigure(0, weight=1)
    for index, (key, label, _initial) in enumerate(fields):
        label_row = index * 2
        input_row = label_row + 1
        ctk.CTkLabel(form, text=label, fg_color=palette.surface_alt, text_color=palette.text, font=font(theme, "caption", weight="semibold"), anchor="w").grid(
            row=label_row,
            column=0,
            sticky="w",
            padx=space.md,
            pady=(space.md if index == 0 else space.sm, space.xs),
        )
        ctk_entry(form, theme, values[key], placeholder_text="Placeholder").grid(
            row=input_row,
            column=0,
            sticky="ew",
            padx=space.md,
            pady=(0, space.sm),
        )

    def save() -> None:
        result["value"] = {key: value.get() for key, value in values.items()}
        window.destroy()

    _footer(shell, theme, ((submit_text, "primary", save), ("Cancel", "secondary", window.destroy)))
    window.bind("<Return>", lambda _event: save())
    window.bind("<Escape>", lambda _event: window.destroy())
    _wait(window, parent)
    return result["value"]


def choose_option(parent: tk.Widget | None, title: str, message: str, options: list[str], *, submit_text: str = "Use") -> str | None:
    if not options:
        return None
    theme = active_theme()
    palette = theme.palette
    space = theme.spacing
    window = _dialog_window(parent, title, theme, width=520, height=260)
    result: dict[str, str | None] = {"value": None}
    selected = tk.StringVar(value=options[0])

    shell = _shell(window, theme)
    _header(shell, theme, title, message, "info")
    body = ctk.CTkFrame(shell, fg_color=palette.surface_alt, corner_radius=4, border_width=0)
    body.grid(row=2, column=0, sticky="ew", padx=space.page_padding, pady=(0, space.md))
    combo = ctk_combobox(body, theme, selected, options)
    combo.pack(fill="x", padx=space.md, pady=space.md)

    def save() -> None:
        result["value"] = selected.get()
        window.destroy()

    _footer(shell, theme, ((submit_text, "primary", save), ("Cancel", "secondary", window.destroy)))
    window.bind("<Return>", lambda _event: save())
    window.bind("<Escape>", lambda _event: window.destroy())
    _wait(window, parent)
    return result["value"]


def _run_dialog(
    parent: tk.Widget | None,
    title: str,
    message: str,
    *,
    kind: DialogKind,
    buttons: tuple[tuple[str, str, bool], ...],
) -> bool | None:
    theme = active_theme()
    window = _dialog_window(parent, title, theme)
    result: dict[str, bool | None] = {"value": None}
    shell = _shell(window, theme)
    _header(shell, theme, title, message, kind)

    actions = []
    for text, variant, value in buttons:
        actions.append((text, variant, lambda selected=value: (result.update(value=selected), window.destroy())))
    _footer(shell, theme, tuple(actions))
    window.bind("<Escape>", lambda _event: window.destroy())
    _wait(window, parent)
    return result["value"]


def _dialog_window(parent: tk.Widget | None, title: str, theme: SafeSendTheme, *, width: int = 520, height: int = 240) -> ctk.CTkToplevel:
    owner = parent or _DIALOG_ROOT
    master = owner.winfo_toplevel() if owner else None
    window = ctk.CTkToplevel(master)
    window.title(title)
    window.overrideredirect(True)
    window.geometry(f"{width}x{height}")
    window.minsize(460, 220)
    window.configure(fg_color=theme.palette.background)
    if master:
        window.transient(master)
    window.update_idletasks()
    _center(window, owner, width, height)
    return window


def _shell(window: ctk.CTkToplevel, theme: SafeSendTheme) -> ctk.CTkFrame:
    shell = ctk.CTkFrame(
        window,
        fg_color=theme.palette.surface,
        corner_radius=0,
        border_width=1,
        border_color=theme.palette.border,
    )
    shell.pack(fill="both", expand=True)
    shell.columnconfigure(0, weight=1)
    shell.rowconfigure(1, weight=1)
    return shell


def _header(parent: ctk.CTkFrame, theme: SafeSendTheme, title: str, message: str, kind: DialogKind) -> None:
    palette = theme.palette
    space = theme.spacing
    color = {
        "info": palette.success,
        "success": palette.success,
        "warning": palette.warning,
        "error": palette.danger,
        "confirm": palette.success,
    }.get(kind, palette.success)
    header = ctk.CTkFrame(parent, fg_color=color, corner_radius=0, height=64)
    header.grid(row=0, column=0, sticky="ew")
    header.grid_propagate(False)
    header.columnconfigure(0, weight=1)
    ctk.CTkLabel(
        header,
        text=title,
        fg_color=color,
        text_color=palette.sidebar_text,
        font=font(theme, "panel_title", weight="semibold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="nsew", padx=(space.xl, space.md))
    button(
        header,
        "X",
        command=parent.winfo_toplevel().destroy,
        variant="ghost",
        theme=theme,
        width=34,
        height=30,
        fg_color=color,
        hover_color=color,
        text_color=palette.sidebar_text,
        border_width=0,
    ).grid(row=0, column=1, sticky="e", padx=(0, space.md))

    body = ctk.CTkFrame(parent, fg_color=palette.surface, corner_radius=0)
    body.grid(row=1, column=0, sticky="nsew")
    body.columnconfigure(0, weight=1)
    ctk.CTkLabel(
        body,
        text=message,
        fg_color=palette.surface,
        text_color=palette.text,
        font=font(theme, "body"),
        wraplength=430,
        justify="left",
        anchor="nw",
    ).grid(row=0, column=0, sticky="ew", padx=space.xl, pady=(space.xl, space.md))


def _footer(parent: ctk.CTkFrame, theme: SafeSendTheme, actions: tuple[tuple[str, str, object], ...]) -> None:
    footer = ctk.CTkFrame(parent, fg_color=theme.palette.surface, corner_radius=0)
    footer.grid(row=3, column=0, sticky="ew")
    for text, variant, command in actions:
        button(footer, text, command=command, variant=variant, theme=theme, width=112, height=38).pack(side="left", padx=(theme.spacing.xl if text == actions[0][0] else 0, theme.spacing.sm), pady=(0, theme.spacing.xl))


def _wait(window: ctk.CTkToplevel, parent: tk.Widget | None) -> None:
    window.grab_set()
    (parent or _DIALOG_ROOT or window).wait_window(window)


def _center(window: ctk.CTkToplevel, parent: tk.Widget | None, width: int, height: int) -> None:
    try:
        if parent:
            parent.update_idletasks()
            x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
            y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        else:
            x = max((window.winfo_screenwidth() - width) // 2, 0)
            y = max((window.winfo_screenheight() - height) // 2, 0)
        window.geometry(f"{width}x{height}+{x}+{y}")
    except tk.TclError:
        pass


def _parent_from_kwargs(kwargs: dict) -> tk.Widget | None:
    return kwargs.get("parent") or _DIALOG_ROOT
