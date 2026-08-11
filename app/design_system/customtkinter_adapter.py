import tkinter as tk

import customtkinter as ctk

from app.design_system import components
from app.design_system.icons import parse_icon_text
from app.design_system.theme import SafeSendTheme
from app.design_system.typography import font


def apply_customtkinter_runtime(theme: SafeSendTheme) -> None:
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)


def ctk_font(theme: SafeSendTheme, role: str = "body", weight: str = "") -> tuple:
    return font(theme, role, weight=weight)


def app_window() -> ctk.CTk:
    return ctk.CTk()


def toplevel(parent: tk.Widget, title: str = "", geometry: str = "") -> ctk.CTkToplevel:
    master = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
    window = ctk.CTkToplevel(master)
    if title:
        window.title(title)
    if geometry:
        window.geometry(geometry)
    try:
        window.transient(master)
    except tk.TclError:
        pass
    window.after_idle(lambda: _present_toplevel(window, master, geometry))
    return window


def _present_toplevel(window: ctk.CTkToplevel, parent: tk.Widget, geometry: str = "") -> None:
    try:
        window.update_idletasks()
        if geometry and "+" not in geometry:
            _center_toplevel(window, parent, geometry)
        window.deiconify()
        window.lift(parent)
        window.focus_force()
        window.attributes("-topmost", True)
        window.after(180, lambda: _clear_topmost(window))
    except tk.TclError:
        pass


def _clear_topmost(window: ctk.CTkToplevel) -> None:
    try:
        window.attributes("-topmost", False)
    except tk.TclError:
        pass


def _center_toplevel(window: ctk.CTkToplevel, parent: tk.Widget, geometry: str) -> None:
    size = geometry.split("+", 1)[0]
    if "x" not in size:
        return
    width_text, height_text = size.lower().split("x", 1)
    try:
        width = int(width_text)
        height = int(height_text)
    except ValueError:
        return
    try:
        parent.update_idletasks()
        parent_width = max(parent.winfo_width(), 1)
        parent_height = max(parent.winfo_height(), 1)
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
    except tk.TclError:
        parent_width = window.winfo_screenwidth()
        parent_height = window.winfo_screenheight()
        parent_x = 0
        parent_y = 0
    x = max(0, parent_x + (parent_width - width) // 2)
    y = max(0, parent_y + (parent_height - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def frame(parent: tk.Widget, theme: SafeSendTheme, variant: str = "background", **kwargs) -> ctk.CTkFrame:
    palette = theme.palette
    variants = {
        "background": {"fg_color": palette.background, "corner_radius": 0},
        "content": {"fg_color": palette.background, "corner_radius": 0},
        "surface": {"fg_color": palette.surface_alt, "corner_radius": 4, "border_width": 1, "border_color": palette.border_soft},
        "card": {"fg_color": palette.surface, "corner_radius": 4, "border_width": 1, "border_color": palette.border_soft},
        "toolbar": {"fg_color": palette.surface, "corner_radius": 4, "border_width": 1, "border_color": palette.border_soft},
        "sidebar": {"fg_color": palette.sidebar, "corner_radius": 0},
        "panel": {"fg_color": palette.surface_alt, "corner_radius": 4},
    }
    options = variants.get(variant, variants["background"]) | kwargs
    return ctk.CTkFrame(parent, **options)


def label(parent: tk.Widget, theme: SafeSendTheme, text: str = "", role: str = "body", variant: str = "background", **kwargs) -> ctk.CTkLabel:
    palette = theme.palette
    fg_color = {
        "background": palette.background,
        "content": palette.background,
        "surface": palette.surface_alt,
        "panel": palette.surface_alt,
        "card": palette.surface,
    }.get(variant, palette.background)
    text_color = palette.text_muted if role in {"caption", "small"} else palette.text
    if variant == "sidebar":
        fg_color = palette.sidebar
        text_color = palette.sidebar_text
    options = {
        "text": text,
        "font": ctk_font(theme, role, "semibold" if role in {"title", "page_title", "panel_title", "brand", "metric", "metric_large"} else ""),
        "text_color": text_color,
        "fg_color": fg_color,
    } | kwargs
    return ctk.CTkLabel(parent, **options)


def button(parent: tk.Widget, theme: SafeSendTheme, text: str, command=None, variant: str = "secondary", **kwargs) -> ctk.CTkButton:
    mapped = "primary" if variant == "sidebar_selected" else ("ghost" if variant == "sidebar" else variant)
    if variant.startswith("sidebar"):
        kwargs.setdefault("anchor", "w")
    icon_name, clean_text = parse_icon_text(text)
    if icon_name and "icon" not in kwargs:
        kwargs["icon"] = icon_name
    return components.button(parent, clean_text, command, variant=mapped, theme=theme, **kwargs)


def entry(parent: tk.Widget, theme: SafeSendTheme, variable: tk.StringVar, width: int = 220, show: str = "", **kwargs) -> ctk.CTkEntry:
    placeholder = str(kwargs.pop("placeholder_text", ""))
    state = str(kwargs.pop("visual_state", "default"))
    return components.text_input(parent, variable, theme=theme, width=width, show=show, placeholder=placeholder, state=state, **kwargs)


def combobox(parent: tk.Widget, theme: SafeSendTheme, variable: tk.StringVar, values: list[str] | tuple[str, ...], **kwargs) -> ctk.CTkComboBox:
    return components.dropdown(parent, variable, values, theme=theme, **kwargs)


def checkbox(parent: tk.Widget, theme: SafeSendTheme, text: str, variable: tk.Variable, **kwargs) -> ctk.CTkCheckBox:
    return components.checkbox(parent, text, variable, theme=theme, **kwargs)


def textbox(parent: tk.Widget, theme: SafeSendTheme, **kwargs) -> ctk.CTkTextbox:
    state = str(kwargs.pop("visual_state", kwargs.pop("state_style", "default")))
    placeholder = str(kwargs.pop("placeholder_text", ""))
    return components.text_area(parent, theme=theme, state=state, placeholder=placeholder, **kwargs)


def style_text_widget(widget: tk.Text, theme: SafeSendTheme) -> None:
    palette = theme.palette
    widget.configure(
        bg=palette.surface_alt,
        fg=palette.text,
        insertbackground=palette.text,
        selectbackground=palette.selection,
        selectforeground=palette.text,
        relief="flat",
        bd=0,
        padx=12,
        pady=10,
        spacing1=2,
        spacing2=2,
        spacing3=6,
        font=ctk_font(theme, "body"),
        highlightthickness=1,
        highlightbackground=palette.border,
        highlightcolor=palette.info,
        inactiveselectbackground=palette.selection,
    )
    widget.bind("<FocusIn>", lambda _event: widget.configure(highlightbackground=palette.info), add="+")
    widget.bind("<FocusOut>", lambda _event: widget.configure(highlightbackground=palette.border), add="+")
