import tkinter as tk
from dataclasses import dataclass
from typing import Callable, Iterable

import customtkinter as ctk

from app.design_system.icons import ICONS, get_route_icon, icon_image
from app.design_system.charts import ReputationDonut
from app.design_system.theme import SafeSendTheme, active_theme
from app.design_system.tooltips import tooltip as attach_tooltip
from app.design_system.typography import font


ButtonVariant = str
InputState = str


@dataclass(frozen=True)
class ComponentSizes:
    button_height: int = 38
    input_height: int = 40
    compact_height: int = 32
    icon_button_width: int = 42
    modal_min_width: int = 520
    modal_min_height: int = 320


SIZES = ComponentSizes()


def _theme(theme: SafeSendTheme | None = None) -> SafeSendTheme:
    return theme or active_theme()


def button(
    parent: tk.Widget,
    text: str,
    command: Callable | None = None,
    *,
    variant: ButtonVariant = "secondary",
    theme: SafeSendTheme | None = None,
    icon: str = "",
    width: int | None = None,
    disabled: bool = False,
    **kwargs,
) -> ctk.CTkButton:
    theme = _theme(theme)
    palette = theme.palette
    styles = {
        "primary": {
            "fg_color": palette.primary,
            "hover_color": palette.primary_dark,
            "text_color": palette.surface,
            "border_width": 0,
        },
        "secondary": {
            "fg_color": palette.button_background,
            "hover_color": palette.button_hover,
            "text_color": palette.text,
            "border_width": 1,
        },
        "danger": {
            "fg_color": palette.button_background,
            "hover_color": palette.button_hover,
            "text_color": palette.danger,
            "border_width": 1,
        },
        "warning": {
            "fg_color": palette.warning,
            "hover_color": palette.orange,
            "text_color": palette.surface,
            "border_width": 0,
        },
        "outline": {
            "fg_color": palette.surface,
            "hover_color": palette.hover,
            "text_color": palette.text,
            "border_width": 1,
        },
        "link": {
            "fg_color": "transparent",
            "hover_color": palette.hover,
            "text_color": palette.primary,
            "border_width": 0,
        },
        "ghost": {
            "fg_color": "transparent",
            "hover_color": palette.hover,
            "text_color": palette.text_muted,
            "border_width": 0,
        },
        "success": {
            "fg_color": palette.button_background,
            "hover_color": palette.button_hover,
            "text_color": palette.success,
            "border_width": 1,
        },
    }
    icon_name = icon if icon in ICONS else ""
    icon_color_value = {
        "primary": palette.surface,
        "warning": palette.surface,
        "outline": palette.text,
        "secondary": palette.text,
        "danger": palette.danger,
        "success": palette.success,
        "link": palette.primary,
        "ghost": palette.text_muted,
    }.get(variant, palette.text)
    options = {
        "text": text,
        "command": command,
        "height": SIZES.button_height,
        "corner_radius": 4,
        "border_color": palette.button_border,
        "font": font(theme, "button"),
        "state": "disabled" if disabled else "normal",
    } | styles.get(variant, styles["secondary"])
    if width is not None:
        options["width"] = width
    if icon_name:
        options["image"] = icon_image(icon_name, color=icon_color_value, size=16)
        options["compound"] = "left"
    options.update(kwargs)
    widget = ctk.CTkButton(parent, **options)
    if icon_name:
        widget._safesend_icon_image = options["image"]
    return widget


def text_input(
    parent: tk.Widget,
    variable: tk.Variable | None = None,
    *,
    state: InputState = "default",
    theme: SafeSendTheme | None = None,
    placeholder: str = "",
    width: int = 220,
    show: str = "",
    **kwargs,
) -> ctk.CTkEntry:
    theme = _theme(theme)
    palette = theme.palette
    border_color = {
        "default": palette.border,
        "focus": palette.primary,
        "error": palette.danger,
        "disabled": palette.border_soft,
    }.get(state, palette.border)
    options = {
        "textvariable": variable,
        "width": width,
        "height": SIZES.input_height,
        "show": show,
        "corner_radius": 2,
        "border_width": 1,
        "border_color": border_color,
        "fg_color": palette.surface_alt,
        "text_color": palette.text,
        "placeholder_text": placeholder,
        "placeholder_text_color": palette.placeholder,
        "font": font(theme, "body"),
        "state": "disabled" if state == "disabled" else "normal",
    }
    options.update(kwargs)
    return ctk.CTkEntry(parent, **options)


def dropdown(
    parent: tk.Widget,
    variable: tk.Variable,
    values: Iterable[str],
    *,
    theme: SafeSendTheme | None = None,
    state: str = "readonly",
    width: int = 220,
    **kwargs,
) -> ctk.CTkComboBox:
    theme = _theme(theme)
    palette = theme.palette
    options = {
        "variable": variable,
        "values": list(values),
        "width": width,
        "height": SIZES.input_height,
        "corner_radius": 2,
        "border_width": 1,
        "border_color": palette.border,
        "fg_color": palette.surface_alt,
        "button_color": palette.button_background,
        "button_hover_color": palette.button_hover,
        "dropdown_fg_color": palette.surface,
        "dropdown_hover_color": palette.hover,
        "text_color": palette.text,
        "font": font(theme, "body"),
        "state": state,
    }
    options.update(kwargs)
    return ctk.CTkComboBox(parent, **options)


class SelectDropdownButton(ctk.CTkButton):
    def __init__(
        self,
        parent: tk.Widget,
        variable: tk.Variable,
        values: Iterable[str],
        *,
        theme: SafeSendTheme | None = None,
        width: int = 160,
        command: Callable | None = None,
        **kwargs,
    ) -> None:
        self.theme = _theme(theme)
        self.variable = variable
        self.values = list(values)
        self.on_select = command
        self._menu: ctk.CTkToplevel | None = None
        palette = self.theme.palette
        options = {
            "text": self._button_text(),
            "command": self._toggle_menu,
            "width": width,
            "height": SIZES.input_height,
            "corner_radius": 3,
            "border_width": 1,
            "border_color": palette.border,
            "fg_color": palette.button_background,
            "hover_color": palette.button_hover,
            "text_color": palette.text,
            "font": font(self.theme, "body", weight="semibold"),
            "anchor": "center",
        }
        options.update(kwargs)
        super().__init__(parent, **options)
        self.variable.trace_add("write", lambda *_: self.configure(text=self._button_text()))

    def _button_text(self) -> str:
        value = str(self.variable.get() or (self.values[0] if self.values else "Select"))
        return f"{value}  v"

    def _toggle_menu(self) -> None:
        if self._menu and self._menu.winfo_exists():
            self._close_menu()
            return
        self._open_menu()

    def _open_menu(self) -> None:
        palette = self.theme.palette
        self._menu = ctk.CTkToplevel(self)
        self._menu.overrideredirect(True)
        self._menu.attributes("-topmost", True)
        self._menu.configure(fg_color=palette.surface)
        self._menu.bind("<FocusOut>", lambda _event: self._close_menu(), add="+")
        menu_width = max(int(self.cget("width") or 160), 150)
        item_height = 34
        visible_count = min(max(len(self.values), 1), 8)
        self._menu.geometry(f"{menu_width}x{visible_count * item_height + 2}+{self.winfo_rootx()}+{self.winfo_rooty() + self.winfo_height() + 4}")
        shell = ctk.CTkFrame(self._menu, fg_color=palette.surface, border_width=1, border_color=palette.border, corner_radius=3)
        shell.pack(fill="both", expand=True)
        body = ctk.CTkScrollableFrame(shell, fg_color=palette.surface, corner_radius=0)
        body.pack(fill="both", expand=True, padx=1, pady=1)
        for value in self.values:
            selected = value == self.variable.get()
            row = ctk.CTkButton(
                body,
                text=value,
                command=lambda selected_value=value: self._select(selected_value),
                height=item_height,
                corner_radius=3,
                fg_color=palette.selection if selected else "transparent",
                hover_color=palette.hover,
                text_color=palette.primary if selected else palette.text,
                font=font(self.theme, "body"),
                anchor="w",
            )
            row.pack(fill="x", padx=2, pady=1)
        self._menu.after(10, self._menu.focus_force)

    def _select(self, value: str) -> None:
        self.variable.set(value)
        if callable(self.on_select):
            self.on_select(value)
        self._close_menu()

    def _close_menu(self) -> None:
        if self._menu and self._menu.winfo_exists():
            self._menu.destroy()
        self._menu = None


def select_dropdown_button(
    parent: tk.Widget,
    variable: tk.Variable,
    values: Iterable[str],
    *,
    theme: SafeSendTheme | None = None,
    width: int = 160,
    command: Callable | None = None,
    **kwargs,
) -> SelectDropdownButton:
    return SelectDropdownButton(parent, variable, values, theme=theme, width=width, command=command, **kwargs)


def checkbox(parent: tk.Widget, text: str, variable: tk.Variable, *, theme: SafeSendTheme | None = None, **kwargs) -> ctk.CTkCheckBox:
    theme = _theme(theme)
    palette = theme.palette
    options = {
        "text": text,
        "variable": variable,
        "fg_color": palette.primary,
        "hover_color": palette.primary_dark,
        "border_color": palette.border,
        "text_color": palette.text,
        "font": font(theme, "body"),
    }
    options.update(kwargs)
    return ctk.CTkCheckBox(parent, **options)


def toggle(parent: tk.Widget, text: str, variable: tk.Variable, *, theme: SafeSendTheme | None = None, **kwargs) -> ctk.CTkSwitch:
    theme = _theme(theme)
    palette = theme.palette
    options = {
        "text": text,
        "variable": variable,
        "progress_color": palette.primary,
        "button_color": palette.surface,
        "button_hover_color": palette.surface_alt,
        "fg_color": palette.border,
        "text_color": palette.text,
        "font": font(theme, "body"),
    }
    options.update(kwargs)
    return ctk.CTkSwitch(parent, **options)


def label(
    parent: tk.Widget,
    text: str = "",
    *,
    role: str = "body",
    theme: SafeSendTheme | None = None,
    surface: str = "background",
    muted: bool = False,
    **kwargs,
) -> ctk.CTkLabel:
    theme = _theme(theme)
    palette = theme.palette
    fg_color = {
        "background": palette.background,
        "card": palette.surface,
        "surface": palette.surface_alt,
        "sidebar": palette.sidebar,
        "transparent": "transparent",
    }.get(surface, palette.background)
    options = {
        "text": text,
        "fg_color": fg_color,
        "text_color": palette.text_muted if muted or role in {"caption", "small"} else palette.text,
        "font": font(theme, role, weight="semibold" if role in {"title", "page_title", "panel_title", "metric", "metric_large"} else ""),
    }
    options.update(kwargs)
    return ctk.CTkLabel(parent, **options)


class Card(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, *, theme: SafeSendTheme | None = None, title: str = "", subtitle: str = "", **kwargs) -> None:
        self.theme = _theme(theme)
        palette = self.theme.palette
        options = {
            "fg_color": palette.surface,
            "corner_radius": 4,
            "border_width": 1,
            "border_color": palette.border_soft,
        }
        options.update(kwargs)
        super().__init__(parent, **options)
        self.content_row = 0
        if title or subtitle:
            header = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
            header.grid(row=0, column=0, sticky="ew", padx=self.theme.spacing.card_padding, pady=(self.theme.spacing.card_padding, self.theme.spacing.sm))
            header.columnconfigure(0, weight=1)
            if title:
                label(header, title, role="panel_title", theme=self.theme, surface="transparent").grid(row=0, column=0, sticky="w")
            if subtitle:
                label(header, subtitle, role="caption", theme=self.theme, surface="transparent", muted=True, wraplength=520, justify="left").grid(row=1, column=0, sticky="w", pady=(2, 0))
            self.content_row = 1
        self.columnconfigure(0, weight=1)


class MetricCard(Card):
    def __init__(self, parent: tk.Widget, title: str, value: str | int, *, detail: str = "", theme: SafeSendTheme | None = None, level: str = "default") -> None:
        super().__init__(parent, theme=theme)
        palette = self.theme.palette
        self.configure(height=96)
        self.grid_propagate(False)
        accent = {
            "default": palette.primary,
            "success": palette.success,
            "warning": palette.orange,
            "danger": palette.danger,
            "info": palette.info,
        }.get(level, palette.primary)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        ctk.CTkFrame(self, fg_color=accent, width=4, corner_radius=2).grid(row=0, column=0, sticky="nsw", padx=(self.theme.spacing.card_padding, 0), pady=self.theme.spacing.card_padding)
        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.grid(row=0, column=1, sticky="nsew", padx=(self.theme.spacing.md, self.theme.spacing.card_padding), pady=(8, 6))
        self.value_label = label(body, str(value), role="metric", theme=self.theme, surface="transparent")
        self.value_label.pack(anchor="w")
        label(body, title, role="caption", theme=self.theme, surface="transparent", muted=True).pack(anchor="w", pady=(1, 0))
        if detail:
            label(body, detail, role="caption", theme=self.theme, surface="transparent", muted=True, wraplength=220, justify="left").pack(anchor="w", pady=(2, 0))


class SidebarItem(ctk.CTkButton):
    def __init__(self, parent: tk.Widget, text: str, command: Callable | None = None, *, selected: bool = False, theme: SafeSendTheme | None = None, icon: str = "", **kwargs) -> None:
        theme = _theme(theme)
        palette = theme.palette
        icon_name = icon if icon in ICONS else ""
        image = icon_image(icon_name, color=palette.sidebar_text, size=18) if icon_name else None
        options = {
            "text": text,
            "command": command,
            "height": 40,
            "corner_radius": 4,
            "fg_color": palette.sidebar_selected if selected else "transparent",
            "hover_color": palette.sidebar_hover,
            "text_color": palette.sidebar_text,
            "font": font(theme, "sidebar"),
            "anchor": "w",
            "border_width": 0,
        }
        if image:
            options["image"] = image
            options["compound"] = "left"
        options.update(kwargs)
        super().__init__(parent, **options)
        if image:
            self._safesend_icon_image = image


class SenderReputationCard(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, score: int = 92, *, theme: SafeSendTheme | None = None) -> None:
        self.theme = _theme(theme)
        palette = self.theme.palette
        super().__init__(
            parent,
            fg_color="#2E475D",
            corner_radius=4,
            border_width=1,
            border_color="#425B76",
        )
        self.configure(height=82)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self.columnconfigure(1, weight=1)
        ReputationDonut(self, score, theme=self.theme, size=54, background="#2E475D", text_color=palette.sidebar_text, nested=False).grid(
            row=0,
            column=0,
            rowspan=2,
            sticky="w",
            padx=(self.theme.spacing.sm, self.theme.spacing.xs),
            pady=self.theme.spacing.sm,
        )
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=1, sticky="ew", padx=(0, self.theme.spacing.sm), pady=(self.theme.spacing.sm, 0))
        header.columnconfigure(1, weight=1)
        icon_label(header, "shield_ai", theme=self.theme, text="", text_color=palette.success, surface="transparent", size=13).grid(row=0, column=0, sticky="w", padx=(0, self.theme.spacing.xs))
        label(header, "Sender Reputation", role="caption", theme=self.theme, surface="transparent", text_color=palette.sidebar_text).grid(row=0, column=1, sticky="w")
        label(self, "92 Excellent", role="caption", theme=self.theme, surface="transparent", text_color=palette.success).grid(row=1, column=1, sticky="nw", padx=(0, self.theme.spacing.sm), pady=(1, self.theme.spacing.sm))


class PageHeader(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, title: str, subtitle: str = "", *, theme: SafeSendTheme | None = None, intro: str = "") -> None:
        self.theme = _theme(theme)
        super().__init__(parent, fg_color=self.theme.palette.background, corner_radius=0)
        self.columnconfigure(0, weight=1)
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="w")
        icon_name = get_route_icon(title)
        if icon_name in ICONS:
            icon_label(title_row, icon_name, theme=self.theme, text_color=self.theme.palette.primary, size=32, surface="transparent").pack(side="left", padx=(0, self.theme.spacing.md))
        label(title_row, title, role="page_title", theme=self.theme, surface="transparent").pack(side="left")
        copy = "\n".join(part for part in (subtitle, intro) if part)
        if copy:
            copy_label = label(
                self,
                copy,
                role="body",
                theme=self.theme,
                muted=True,
                justify="left",
                anchor="w",
                wraplength=920,
            )
            copy_label.grid(row=1, column=0, sticky="ew", pady=(self.theme.spacing.sm, 0))

            def refresh_wrap(event: tk.Event | None = None) -> None:
                width = min(920, max(260, int((getattr(event, "width", 0) or self.winfo_width()) - 8)))
                copy_label.configure(wraplength=width)

            self.bind("<Configure>", refresh_wrap, add="+")
            self.after_idle(refresh_wrap)


class Toolbar(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, *, theme: SafeSendTheme | None = None, **kwargs) -> None:
        self.theme = _theme(theme)
        palette = self.theme.palette
        options = {
            "fg_color": palette.surface,
            "corner_radius": 4,
            "border_width": 1,
            "border_color": palette.border_soft,
        }
        options.update(kwargs)
        super().__init__(parent, **options)

    def add_button(self, text: str, command: Callable | None = None, *, variant: ButtonVariant = "secondary", **kwargs) -> ctk.CTkButton:
        child = button(self, text, command, variant=variant, theme=self.theme, **kwargs)
        child.pack(side="left", padx=(self.theme.spacing.sm, 0), pady=self.theme.spacing.sm)
        return child


class Modal(ctk.CTkToplevel):
    def __init__(self, parent: tk.Widget, title: str, *, theme: SafeSendTheme | None = None, geometry: str = "640x420") -> None:
        self.theme = _theme(theme)
        super().__init__(parent)
        self.title(title)
        self.geometry(geometry)
        self.minsize(SIZES.modal_min_width, SIZES.modal_min_height)
        self.configure(fg_color=self.theme.palette.background)
        self.body = Card(self, theme=self.theme)
        self.body.pack(fill="both", expand=True, padx=self.theme.spacing.page_padding, pady=self.theme.spacing.page_padding)
        self.transient(parent)


class EmptyState(Card):
    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        message: str,
        *,
        action_text: str = "",
        action_command: Callable | None = None,
        theme: SafeSendTheme | None = None,
    ) -> None:
        super().__init__(parent, theme=theme)
        label(self, title, role="panel_title", theme=self.theme, surface="card").pack(anchor="center", padx=24, pady=(24, 4))
        label(self, message, role="caption", theme=self.theme, surface="card", muted=True, wraplength=420, justify="center").pack(anchor="center", padx=24)
        if action_text:
            button(self, action_text, action_command, variant="primary", theme=self.theme).pack(anchor="center", pady=(16, 24))


class AIAssistantPanel(Card):
    def __init__(self, parent: tk.Widget, *, theme: SafeSendTheme | None = None, title: str = "AI Assistant") -> None:
        super().__init__(parent, theme=theme, title=title, subtitle="Contextual recommendations and next best actions.")
        self.messages = ctk.CTkTextbox(
            self,
            height=160,
            corner_radius=2,
            border_width=1,
            border_color=self.theme.palette.border,
            fg_color=self.theme.palette.surface_alt,
            text_color=self.theme.palette.text,
            font=font(self.theme, "body"),
            wrap="word",
            border_spacing=12,
            scrollbar_button_color="#CBD6E2",
            scrollbar_button_hover_color="#B6C7D6",
        )
        self.messages.grid(row=self.content_row, column=0, sticky="nsew", padx=self.theme.spacing.card_padding, pady=(0, self.theme.spacing.card_padding))
        self.messages.insert("1.0", "No recommendations yet.")
        self.messages.configure(state="disabled")


def attach_tooltip_to(widget: tk.Widget, text: str) -> None:
    attach_tooltip(widget, text)


def table(parent: tk.Widget, columns: tuple[str, ...], headings: tuple[str, ...] | None = None, height: int = 12):
    from app.ui.components.modern_table import ModernTable

    return ModernTable(parent, columns, headings=headings, height=height)


# Foundations


@dataclass(frozen=True)
class FoundationTokens:
    radius_sm: int = 6
    radius_md: int = 10
    radius_lg: int = 14
    radius_xl: int = 18
    elevation_0: int = 0
    elevation_1: int = 1
    elevation_2: int = 2
    opacity_disabled: float = 0.45
    opacity_muted: float = 0.72
    animation_fast_ms: int = 120
    animation_normal_ms: int = 180
    animation_slow_ms: int = 260


FOUNDATIONS = FoundationTokens()


def divider(parent: tk.Widget, *, theme: SafeSendTheme | None = None, vertical: bool = False) -> ctk.CTkFrame:
    theme = _theme(theme)
    return ctk.CTkFrame(
        parent,
        fg_color=theme.palette.divider,
        width=1 if vertical else 10,
        height=10 if vertical else 1,
        corner_radius=0,
    )


def icon_label(
    parent: tk.Widget,
    icon: str,
    text: str = "",
    *,
    theme: SafeSendTheme | None = None,
    muted: bool = False,
    size: int = 18,
    text_color: str | None = None,
    surface: str = "background",
    **kwargs,
) -> ctk.CTkLabel:
    theme = _theme(theme)
    palette = theme.palette
    color = text_color or (palette.text_muted if muted else palette.text)
    fg_color = {
        "background": palette.background,
        "card": palette.surface,
        "surface": palette.surface_alt,
        "sidebar": palette.sidebar,
        "transparent": "transparent",
    }.get(surface, palette.background)
    if icon in ICONS:
        image = icon_image(icon, color=color, size=size)
        options = {
            "text": text,
            "image": image,
            "compound": "left" if text else "center",
            "fg_color": fg_color,
            "text_color": color,
            "font": font(theme, "body"),
        }
        options.update(kwargs)
        widget = ctk.CTkLabel(parent, **options)
        widget._safesend_icon_image = image
        return widget
    return label(parent, f"{icon}  {text}" if text else icon, role="body", theme=theme, muted=muted, text_color=color, surface=surface, **kwargs)


def illustration_placeholder(parent: tk.Widget, name: str, *, theme: SafeSendTheme | None = None) -> Card:
    card = Card(parent, theme=theme)
    label(card, name, role="caption", theme=card.theme, surface="card", muted=True).pack(padx=24, pady=24)
    return card


# Layout components


def app_shell(parent: tk.Widget, *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    shell = ctk.CTkFrame(parent, fg_color=theme.palette.background, corner_radius=0)
    shell.columnconfigure(1, weight=1)
    shell.rowconfigure(0, weight=1)
    return shell


def sidebar(parent: tk.Widget, *, theme: SafeSendTheme | None = None, width: int | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    nav = ctk.CTkFrame(parent, fg_color=theme.palette.sidebar, corner_radius=0, width=width or theme.spacing.sidebar_width)
    nav.pack_propagate(False)
    return nav


def sidebar_section(parent: tk.Widget, title: str, *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    section_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    label(section_frame, title.upper(), role="small", theme=theme, surface="sidebar", muted=True, text_color=theme.palette.sidebar_muted).pack(
        anchor="w",
        padx=theme.spacing.md,
        pady=(theme.spacing.md, theme.spacing.xs),
    )
    return section_frame


def top_navigation(parent: tk.Widget, *, theme: SafeSendTheme | None = None, title: str = "") -> Toolbar:
    bar = Toolbar(parent, theme=theme)
    if title:
        label(bar, title, role="panel_title", theme=bar.theme, surface="card").pack(side="left", padx=bar.theme.spacing.md)
    return bar


def page_container(parent: tk.Widget, *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    container = ctk.CTkFrame(parent, fg_color=theme.palette.background, corner_radius=0)
    container.columnconfigure(0, weight=1)
    return container


def content_area(parent: tk.Widget, *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    return page_container(parent, theme=theme)


def section(parent: tk.Widget, title: str = "", subtitle: str = "", *, theme: SafeSendTheme | None = None) -> Card:
    return Card(parent, theme=theme, title=title, subtitle=subtitle)


def panel(parent: tk.Widget, title: str = "", *, theme: SafeSendTheme | None = None) -> Card:
    return Card(parent, theme=theme, title=title)


def split_panel(parent: tk.Widget, *, orientation: str = "horizontal") -> tk.PanedWindow:
    orient = tk.HORIZONTAL if orientation == "horizontal" else tk.VERTICAL
    return tk.PanedWindow(parent, orient=orient, sashwidth=4, bd=0, relief="flat")


resizable_panel = split_panel


def drawer(parent: tk.Widget, title: str = "", *, theme: SafeSendTheme | None = None, width: int = 360) -> Card:
    return Card(parent, theme=theme, title=title, width=width)


def inspector_panel(parent: tk.Widget, title: str = "Inspector", *, theme: SafeSendTheme | None = None) -> Card:
    return Card(parent, theme=theme, title=title, subtitle="Details and editable properties.")


class Accordion(Card):
    def __init__(self, parent: tk.Widget, title: str, *, theme: SafeSendTheme | None = None, open: bool = True) -> None:
        super().__init__(parent, theme=theme)
        self.open_var = tk.BooleanVar(value=open)
        self.header_button = button(self, title, self.toggle, variant="ghost", theme=self.theme)
        self.header_button.grid(row=0, column=0, sticky="ew", padx=self.theme.spacing.sm, pady=self.theme.spacing.sm)
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        if open:
            self.content.grid(row=1, column=0, sticky="nsew", padx=self.theme.spacing.card_padding, pady=(0, self.theme.spacing.card_padding))

    def toggle(self) -> None:
        if self.content.winfo_ismapped():
            self.content.grid_remove()
        else:
            self.content.grid(row=1, column=0, sticky="nsew", padx=self.theme.spacing.card_padding, pady=(0, self.theme.spacing.card_padding))


class Stack(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, *, theme: SafeSendTheme | None = None, gap: int | None = None, horizontal: bool = False) -> None:
        self.theme = _theme(theme)
        self.gap = self.theme.spacing.grid_gap if gap is None else gap
        self.horizontal = horizontal
        self.count = 0
        super().__init__(parent, fg_color="transparent", corner_radius=0)

    def add(self, widget: tk.Widget, **grid_kwargs) -> tk.Widget:
        row = 0 if self.horizontal else self.count
        column = self.count if self.horizontal else 0
        widget.grid(row=row, column=column, sticky="ew", padx=(0, self.gap if self.horizontal else 0), pady=(0, self.gap if not self.horizontal else 0), **grid_kwargs)
        self.count += 1
        return widget


class Grid(ctk.CTkFrame):
    def __init__(self, parent: tk.Widget, columns: int = 2, *, theme: SafeSendTheme | None = None) -> None:
        self.theme = _theme(theme)
        self.columns = columns
        self.count = 0
        super().__init__(parent, fg_color="transparent", corner_radius=0)
        for idx in range(columns):
            self.columnconfigure(idx, weight=1)

    def add(self, widget: tk.Widget) -> tk.Widget:
        row = self.count // self.columns
        col = self.count % self.columns
        widget.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else self.theme.spacing.grid_gap, 0), pady=(0, self.theme.spacing.grid_gap))
        self.count += 1
        return widget


def scrollable_container(parent: tk.Widget, *, theme: SafeSendTheme | None = None, height: int = 360) -> ctk.CTkScrollableFrame:
    theme = _theme(theme)
    return ctk.CTkScrollableFrame(parent, fg_color=theme.palette.background, corner_radius=0, height=height)


# Navigation


def navigation_menu(parent: tk.Widget, items: Iterable[str], command: Callable[[str], None], *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    menu = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    for item in items:
        SidebarItem(menu, item, command=lambda value=item: command(value), theme=theme).pack(fill="x", pady=theme.spacing.xs)
    return menu


def breadcrumbs(parent: tk.Widget, items: Iterable[str], *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    crumb_frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    label(crumb_frame, " / ".join(items), role="caption", theme=theme, muted=True).pack(anchor="w")
    return crumb_frame


def tabs(parent: tk.Widget, names: Iterable[str], *, theme: SafeSendTheme | None = None) -> ctk.CTkTabview:
    theme = _theme(theme)
    tabview = ctk.CTkTabview(parent, fg_color=theme.palette.surface, segmented_button_fg_color=theme.palette.surface_alt, corner_radius=4)
    for name in names:
        tabview.add(name)
    return tabview


def segmented_control(parent: tk.Widget, variable: tk.Variable, values: Iterable[str], *, theme: SafeSendTheme | None = None, command=None) -> ctk.CTkSegmentedButton:
    theme = _theme(theme)
    return ctk.CTkSegmentedButton(
        parent,
        variable=variable,
        values=list(values),
        command=command,
        fg_color=theme.palette.surface_alt,
        selected_color=theme.palette.primary,
        selected_hover_color=theme.palette.primary_dark,
        unselected_color=theme.palette.button_background,
        unselected_hover_color=theme.palette.button_hover,
        text_color=theme.palette.text,
    )


def pagination(parent: tk.Widget, current: int, total: int, on_previous: Callable | None = None, on_next: Callable | None = None, *, theme: SafeSendTheme | None = None) -> Toolbar:
    bar = Toolbar(parent, theme=theme)
    bar.add_button("Previous", on_previous)
    label(bar, f"Page {current} of {total}", role="caption", theme=bar.theme, surface="card").pack(side="left", padx=bar.theme.spacing.md)
    bar.add_button("Next", on_next)
    return bar


def step_indicator(parent: tk.Widget, steps: Iterable[str], active_index: int = 0, *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    for idx, step in enumerate(steps):
        level = "primary" if idx == active_index else "ghost"
        button(frame, f"{idx + 1}. {step}", variant=level, theme=theme, width=140).pack(side="left", padx=(0, theme.spacing.sm))
    return frame


def wizard(parent: tk.Widget, title: str, steps: Iterable[str], *, theme: SafeSendTheme | None = None) -> Modal:
    modal = Modal(parent, title, theme=theme, geometry="900x620")
    step_indicator(modal.body, steps, theme=modal.theme).grid(row=0, column=0, sticky="ew", padx=modal.theme.spacing.card_padding, pady=modal.theme.spacing.card_padding)
    return modal


def previous_next(parent: tk.Widget, previous: Callable | None, next: Callable | None, *, theme: SafeSendTheme | None = None) -> Toolbar:
    bar = Toolbar(parent, theme=theme)
    bar.add_button("Previous", previous)
    bar.add_button("Next", next, variant="primary")
    return bar


def context_menu(parent: tk.Widget, items: dict[str, Callable]) -> tk.Menu:
    menu = tk.Menu(parent, tearoff=False)
    for label_text, command in items.items():
        menu.add_command(label=label_text, command=command)
    return menu


overflow_menu = context_menu
dropdown_menu = context_menu


# Buttons


def primary_button(parent: tk.Widget, text: str, command: Callable | None = None, **kwargs) -> ctk.CTkButton:
    return button(parent, text, command, variant="primary", **kwargs)


def secondary_button(parent: tk.Widget, text: str, command: Callable | None = None, **kwargs) -> ctk.CTkButton:
    return button(parent, text, command, variant="secondary", **kwargs)


def ghost_button(parent: tk.Widget, text: str, command: Callable | None = None, **kwargs) -> ctk.CTkButton:
    return button(parent, text, command, variant="ghost", **kwargs)


def danger_button(parent: tk.Widget, text: str, command: Callable | None = None, **kwargs) -> ctk.CTkButton:
    return button(parent, text, command, variant="danger", **kwargs)


def success_button(parent: tk.Widget, text: str, command: Callable | None = None, **kwargs) -> ctk.CTkButton:
    return button(parent, text, command, variant="success", **kwargs)


def icon_button(parent: tk.Widget, icon: str, command: Callable | None = None, *, theme: SafeSendTheme | None = None, **kwargs) -> ctk.CTkButton:
    return button(parent, icon, command, variant="ghost", theme=theme, width=SIZES.icon_button_width, **kwargs)


def split_button(parent: tk.Widget, text: str, command: Callable | None, menu_items: dict[str, Callable], *, theme: SafeSendTheme | None = None) -> Toolbar:
    bar = Toolbar(parent, theme=theme)
    bar.add_button(text, command, variant="primary")
    bar.add_button("v", lambda: None, width=SIZES.icon_button_width)
    bar.menu = context_menu(bar, menu_items)
    return bar


def loading_button(parent: tk.Widget, text: str = "Loading", *, theme: SafeSendTheme | None = None) -> ctk.CTkButton:
    return button(parent, f"{text}...", disabled=True, theme=theme)


def dropdown_button(parent: tk.Widget, text: str, items: dict[str, Callable], *, theme: SafeSendTheme | None = None) -> ctk.CTkButton:
    btn = button(parent, f"{text} v", theme=theme)
    btn.menu = context_menu(btn, items)
    return btn


def button_group(parent: tk.Widget, actions: Iterable[tuple[str, Callable | None]], *, theme: SafeSendTheme | None = None) -> Toolbar:
    bar = Toolbar(parent, theme=theme)
    for text, command in actions:
        bar.add_button(text, command)
    return bar


def floating_action_button(parent: tk.Widget, text: str = "+", command: Callable | None = None, *, theme: SafeSendTheme | None = None) -> ctk.CTkButton:
    return button(parent, text, command, variant="primary", theme=theme, width=54, height=54, corner_radius=27)


# Inputs


def password_input(parent: tk.Widget, variable: tk.Variable | None = None, **kwargs) -> ctk.CTkEntry:
    return text_input(parent, variable, show="*", **kwargs)


def email_input(parent: tk.Widget, variable: tk.Variable | None = None, **kwargs) -> ctk.CTkEntry:
    kwargs.setdefault("placeholder", "name@example.com")
    return text_input(parent, variable, **kwargs)


def number_input(parent: tk.Widget, variable: tk.Variable | None = None, **kwargs) -> ctk.CTkEntry:
    return text_input(parent, variable, **kwargs)


def phone_input(parent: tk.Widget, variable: tk.Variable | None = None, **kwargs) -> ctk.CTkEntry:
    kwargs.setdefault("placeholder", "(555) 555-5555")
    return text_input(parent, variable, **kwargs)


def search_box(parent: tk.Widget, variable: tk.Variable | None = None, **kwargs) -> ctk.CTkEntry:
    kwargs.setdefault("placeholder", "Search")
    return text_input(parent, variable, **kwargs)


def command_search(
    parent: tk.Widget,
    variable: tk.Variable,
    *,
    theme: SafeSendTheme | None = None,
    command: Callable | None = None,
    placeholder: str = "Search campaigns, contacts, SMTP profiles...",
    width: int = 540,
) -> ctk.CTkFrame:
    theme = _theme(theme)
    palette = theme.palette
    frame = ctk.CTkFrame(
        parent,
        fg_color=palette.surface_alt,
        corner_radius=4,
        height=30,
        width=width,
        border_width=1,
        border_color=palette.border_soft,
    )
    frame.pack_propagate(False)

    icon_label(frame, "search", theme=theme, text_color=palette.text_muted, size=15, surface="surface").pack(
        side="left",
        padx=(theme.spacing.md, theme.spacing.xs),
        pady=0,
    )
    entry = text_input(
        frame,
        variable,
        theme=theme,
        placeholder=placeholder,
        width=max(180, width - 166),
        height=24,
        border_width=0,
        fg_color=palette.surface_alt,
        corner_radius=0,
    )
    entry.pack(side="left", fill="x", expand=True, padx=(0, theme.spacing.sm), pady=2)

    shortcut = ctk.CTkLabel(
        frame,
        text="Ctrl+K",
        fg_color=palette.surface_alt,
        text_color=palette.text_muted,
        font=font(theme, "caption"),
        height=20,
    )
    shortcut.pack(side="left", padx=(0, theme.spacing.xs), pady=4)

    action = ctk.CTkButton(
        frame,
        text="Search",
        command=command,
        width=54,
        height=24,
        corner_radius=3,
        border_width=0,
        fg_color=palette.surface_alt,
        hover_color=palette.hover,
        text_color=palette.secondary,
        font=font(theme, "caption", weight="semibold"),
    )
    action.pack(side="left", padx=(0, theme.spacing.xs), pady=2)

    def run(_event=None):
        if callable(command):
            command()
        return "break"

    def focus_in(_event=None) -> None:
        frame.configure(border_color=palette.info)

    def focus_out(_event=None) -> None:
        frame.configure(border_color=palette.border_soft)

    entry.bind("<Return>", run, add="+")
    entry.bind("<FocusIn>", focus_in, add="+")
    entry.bind("<FocusOut>", focus_out, add="+")
    frame.entry = entry
    return frame


def search_with_filters(parent: tk.Widget, search_var: tk.Variable, filters: dict[str, Iterable[str]], *, theme: SafeSendTheme | None = None) -> Toolbar:
    theme = _theme(theme)
    bar = Toolbar(parent, theme=theme)
    search_box(bar, search_var, theme=theme).pack(side="left", fill="x", expand=True, padx=theme.spacing.sm, pady=theme.spacing.sm)
    for name, values in filters.items():
        var = tk.StringVar(value=list(values)[0] if values else "")
        dropdown(bar, var, values, theme=theme, width=150).pack(side="left", padx=theme.spacing.sm)
        bar.filter_vars = getattr(bar, "filter_vars", {})
        bar.filter_vars[name] = var
    return bar


class TextArea(ctk.CTkTextbox):
    def __init__(
        self,
        parent: tk.Widget,
        *,
        theme: SafeSendTheme | None = None,
        height: int = 120,
        visual_state: str = "default",
        placeholder_text: str = "",
        **kwargs,
    ) -> None:
        self.theme = _theme(theme)
        self.visual_state = visual_state
        self.placeholder_text = placeholder_text
        self._placeholder_visible = False
        self._has_focus = False
        palette = self.theme.palette
        border_color = {
            "default": palette.border,
            "focus": palette.info,
            "error": palette.danger,
            "disabled": palette.border_soft,
            "readonly": palette.border_soft,
        }.get(visual_state, palette.border)
        fg_color = palette.surface_alt if visual_state not in {"disabled", "readonly"} else "#EAF0F6"
        options = {
            "height": height,
            "corner_radius": 2,
            "border_width": 1,
            "border_color": border_color,
            "fg_color": fg_color,
            "text_color": palette.text,
            "font": font(self.theme, "body"),
            "wrap": "word",
            "border_spacing": 12,
            "scrollbar_button_color": "#CBD6E2",
            "scrollbar_button_hover_color": "#B6C7D6",
        }
        if visual_state in {"disabled", "readonly"}:
            options["state"] = "disabled"
        options.update(kwargs)
        super().__init__(parent, **options)
        self.bind("<FocusIn>", self._handle_focus_in, add="+")
        self.bind("<FocusOut>", self._handle_focus_out, add="+")
        self.bind("<KeyRelease>", self._handle_key_release, add="+")
        self.after_idle(self._show_placeholder_if_needed)

    def _set_border(self, color: str) -> None:
        try:
            self.configure(border_color=color)
        except tk.TclError:
            pass

    def _handle_focus_in(self, _event: tk.Event) -> None:
        self._has_focus = True
        if self._placeholder_visible:
            self._hide_placeholder()
        if self.visual_state != "error":
            self._set_border(self.theme.palette.info)

    def _handle_focus_out(self, _event: tk.Event) -> None:
        self._has_focus = False
        if self.visual_state != "error":
            self._set_border(self.theme.palette.border)
        self._show_placeholder_if_needed()

    def _handle_key_release(self, _event: tk.Event) -> None:
        if not self._has_focus:
            self._show_placeholder_if_needed()

    def _show_placeholder_if_needed(self) -> None:
        if not self.placeholder_text or self._has_focus or self._placeholder_visible:
            return
        if super().get("1.0", "end-1c"):
            return
        previous_state = str(self.cget("state"))
        if previous_state == "disabled":
            self.configure(state="normal")
        super().insert("1.0", self.placeholder_text)
        self.configure(text_color=self.theme.palette.placeholder)
        self._placeholder_visible = True
        if previous_state == "disabled":
            self.configure(state="disabled")

    def _hide_placeholder(self) -> None:
        if not self._placeholder_visible:
            return
        previous_state = str(self.cget("state"))
        if previous_state == "disabled":
            self.configure(state="normal")
        super().delete("1.0", "end")
        self.configure(text_color=self.theme.palette.text)
        self._placeholder_visible = False
        if previous_state == "disabled":
            self.configure(state="disabled")

    def insert(self, index: str, text: str, *args) -> None:
        if self._placeholder_visible:
            self._hide_placeholder()
        return super().insert(index, text, *args)

    def delete(self, index1: str, index2: str | None = None) -> None:
        if self._placeholder_visible:
            self._hide_placeholder()
        result = super().delete(index1, index2)
        self.after_idle(self._show_placeholder_if_needed)
        return result

    def get(self, index1: str, index2: str | None = None) -> str:
        if self._placeholder_visible:
            return ""
        if index2 is None:
            return super().get(index1)
        return super().get(index1, index2)


def text_area(
    parent: tk.Widget,
    *,
    theme: SafeSendTheme | None = None,
    height: int = 120,
    state: InputState = "default",
    placeholder: str = "",
    **kwargs,
) -> TextArea:
    theme = _theme(theme)
    placeholder_text = str(kwargs.pop("placeholder_text", placeholder))
    return TextArea(parent, theme=theme, height=height, visual_state=state, placeholder_text=placeholder_text, **kwargs)


rich_text_editor = text_area


def code_editor(parent: tk.Widget, *, theme: SafeSendTheme | None = None, height: int = 180) -> ctk.CTkTextbox:
    return text_area(parent, theme=theme, height=height, font=font(_theme(theme), "source"))


# Selection controls


def checkbox_group(parent: tk.Widget, options: Iterable[str], values: dict[str, tk.BooleanVar] | None = None, *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    frame.values = values or {option: tk.BooleanVar(value=False) for option in options}
    for idx, option in enumerate(options):
        checkbox(frame, option, frame.values[option], theme=theme).grid(row=idx, column=0, sticky="w", pady=theme.spacing.xs)
    return frame


def radio_button(parent: tk.Widget, text: str, variable: tk.Variable, value: str, *, theme: SafeSendTheme | None = None) -> ctk.CTkRadioButton:
    theme = _theme(theme)
    return ctk.CTkRadioButton(parent, text=text, variable=variable, value=value, fg_color=theme.palette.primary, text_color=theme.palette.text)


def radio_group(parent: tk.Widget, options: Iterable[str], variable: tk.Variable | None = None, *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    frame.variable = variable or tk.StringVar(value=next(iter(options), ""))
    for idx, option in enumerate(options):
        radio_button(frame, option, frame.variable, option, theme=theme).grid(row=idx, column=0, sticky="w", pady=theme.spacing.xs)
    return frame


def toggle_group(parent: tk.Widget, options: Iterable[str], *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    frame.values = {}
    for idx, option in enumerate(options):
        frame.values[option] = tk.BooleanVar(value=False)
        toggle(frame, option, frame.values[option], theme=theme).grid(row=idx, column=0, sticky="w", pady=theme.spacing.xs)
    return frame


select_dropdown = dropdown


def multi_select(parent: tk.Widget, options: Iterable[str], *, theme: SafeSendTheme | None = None) -> ctk.CTkScrollableFrame:
    theme = _theme(theme)
    frame = ctk.CTkScrollableFrame(parent, fg_color=theme.palette.surface, corner_radius=4, height=180)
    frame.values = {}
    for idx, option in enumerate(options):
        frame.values[option] = tk.BooleanVar(value=False)
        checkbox(frame, option, frame.values[option], theme=theme).grid(row=idx, column=0, sticky="w", padx=theme.spacing.md, pady=theme.spacing.xs)
    return frame


def tag_selector(parent: tk.Widget, tags: Iterable[str], *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
    for tag_name in tags:
        pill(frame, tag_name, theme=theme).pack(side="left", padx=(0, theme.spacing.xs), pady=theme.spacing.xs)
    return frame


def color_picker(parent: tk.Widget, variable: tk.Variable, *, theme: SafeSendTheme | None = None) -> ctk.CTkButton:
    return button(parent, "Color", lambda: variable.set("#0F75BC"), theme=theme)


def date_picker(parent: tk.Widget, variable: tk.Variable | None = None, **kwargs) -> ctk.CTkEntry:
    kwargs.setdefault("placeholder", "YYYY-MM-DD")
    return text_input(parent, variable, **kwargs)


def time_picker(parent: tk.Widget, variable: tk.Variable | None = None, **kwargs) -> ctk.CTkEntry:
    kwargs.setdefault("placeholder", "HH:MM")
    return text_input(parent, variable, **kwargs)


def date_range_picker(parent: tk.Widget, start_var: tk.Variable, end_var: tk.Variable, *, theme: SafeSendTheme | None = None) -> Toolbar:
    bar = Toolbar(parent, theme=theme)
    date_picker(bar, start_var, theme=bar.theme, width=140).pack(side="left", padx=bar.theme.spacing.sm, pady=bar.theme.spacing.sm)
    date_picker(bar, end_var, theme=bar.theme, width=140).pack(side="left", padx=bar.theme.spacing.sm, pady=bar.theme.spacing.sm)
    return bar


def slider(parent: tk.Widget, variable: tk.Variable | None = None, *, theme: SafeSendTheme | None = None, from_: int = 0, to: int = 100) -> ctk.CTkSlider:
    theme = _theme(theme)
    return ctk.CTkSlider(parent, variable=variable, from_=from_, to=to, progress_color=theme.palette.primary, button_color=theme.palette.primary)


def stepper(parent: tk.Widget, variable: tk.Variable, *, theme: SafeSendTheme | None = None) -> Toolbar:
    theme = _theme(theme)
    bar = Toolbar(parent, theme=theme)

    def adjust(delta: int) -> None:
        try:
            variable.set(str(int(variable.get() or 0) + delta))
        except ValueError:
            variable.set(str(delta))

    bar.add_button("-", lambda: adjust(-1), width=SIZES.icon_button_width)
    text_input(bar, variable, theme=theme, width=80).pack(side="left", padx=theme.spacing.sm, pady=theme.spacing.sm)
    bar.add_button("+", lambda: adjust(1), width=SIZES.icon_button_width)
    return bar


# Data display and status


modern_table = table
data_grid = table
tree_view = table


def property_grid(parent: tk.Widget, properties: dict[str, str], *, theme: SafeSendTheme | None = None) -> Card:
    card = Card(parent, theme=theme)
    for idx, (key, value) in enumerate(properties.items()):
        label(card, key, role="caption", theme=card.theme, surface="card", muted=True).grid(row=idx, column=0, sticky="w", padx=card.theme.spacing.card_padding, pady=card.theme.spacing.xs)
        label(card, str(value), role="body", theme=card.theme, surface="card").grid(row=idx, column=1, sticky="w", padx=card.theme.spacing.md, pady=card.theme.spacing.xs)
    return card


def statistics_card(parent: tk.Widget, title: str, value: str | int, **kwargs) -> MetricCard:
    return MetricCard(parent, title, value, **kwargs)


metric_card = statistics_card


def info_card(parent: tk.Widget, title: str, message: str, *, theme: SafeSendTheme | None = None) -> Card:
    return Card(parent, theme=theme, title=title, subtitle=message)


def list_view(parent: tk.Widget, items: Iterable[str], *, theme: SafeSendTheme | None = None) -> Card:
    card = Card(parent, theme=theme)
    for item in items:
        label(card, item, role="body", theme=card.theme, surface="card").pack(anchor="w", padx=card.theme.spacing.card_padding, pady=card.theme.spacing.xs)
    return card


def timeline(parent: tk.Widget, events: Iterable[str], *, theme: SafeSendTheme | None = None) -> Card:
    return list_view(parent, events, theme=theme)


activity_feed = timeline


def log_viewer(parent: tk.Widget, text: str = "", *, theme: SafeSendTheme | None = None) -> ctk.CTkTextbox:
    viewer = code_editor(parent, theme=theme, height=240)
    viewer.insert("1.0", text)
    viewer.configure(state="disabled")
    return viewer


json_viewer = log_viewer


def _level_colors(theme: SafeSendTheme, level: str) -> tuple[str, str, str]:
    palette = theme.palette
    colors = {
        "primary": ("#FFEDE8", palette.primary, "#FFD3C7"),
        "info": ("#E5F5F8", palette.info, "#B7ECEF"),
        "success": ("#E6F7F4", palette.success, "#B7ECE4"),
        "warning": ("#FFF4DE", "#B06A00", "#FFE2A8"),
        "danger": ("#FDECEE", palette.danger, "#F6C9CD"),
        "paused": ("#FFF4DE", "#B06A00", "#FFE2A8"),
        "draft": ("#EAF0F6", theme.palette.secondary, "#CBD6E2"),
        "archived": ("#EAF0F6", theme.palette.secondary, "#CBD6E2"),
        "default": ("#EAF0F6", theme.palette.secondary, "#CBD6E2"),
    }
    return colors.get(level, colors["default"])


def status_badge(parent: tk.Widget, text: str, *, level: str = "default", theme: SafeSendTheme | None = None, **kwargs) -> ctk.CTkLabel:
    theme = _theme(theme)
    fg, text_color, _border = _level_colors(theme, level)
    options = {
        "text": text,
        "fg_color": fg,
        "text_color": text_color,
        "corner_radius": 4,
        "padx": 10,
        "height": 24,
        "font": font(theme, "status_badge"),
    }
    options.update(kwargs)
    return ctk.CTkLabel(parent, **options)


def tag(parent: tk.Widget, text: str, *, theme: SafeSendTheme | None = None) -> ctk.CTkLabel:
    theme = _theme(theme)
    return ctk.CTkLabel(parent, text=text, fg_color=theme.palette.surface_alt, text_color=theme.palette.text, corner_radius=3, padx=10, height=24, font=font(theme, "caption"))


pill = tag


def alert(parent: tk.Widget, title: str, message: str, *, level: str = "info", theme: SafeSendTheme | None = None) -> Card:
    theme = _theme(theme)
    fg, text_color, border = _level_colors(theme, level)
    card = Card(parent, theme=theme, fg_color=fg, border_color=border, corner_radius=4)
    row = ctk.CTkFrame(card, fg_color="transparent", corner_radius=0)
    row.pack(fill="x", padx=theme.spacing.md, pady=theme.spacing.sm)
    status_badge(row, "!", level=level, theme=theme, width=24).pack(side="left")
    label(row, f"{title} ", role="body", theme=theme, surface="transparent", text_color=text_color).pack(side="left", padx=(theme.spacing.sm, 0))
    label(row, message, role="caption", theme=theme, surface="transparent", text_color=theme.palette.text).pack(side="left")
    label(row, "x", role="caption", theme=theme, surface="transparent", muted=True).pack(side="right")
    return card


banner = alert


def progress_bar(parent: tk.Widget, value: float = 0.0, *, theme: SafeSendTheme | None = None) -> ctk.CTkProgressBar:
    theme = _theme(theme)
    bar = ctk.CTkProgressBar(parent, progress_color=theme.palette.primary, fg_color=theme.palette.surface_alt)
    bar.set(value)
    return bar


class CircularProgress(Card):
    def __init__(
        self,
        parent: tk.Widget,
        value: float = 0.0,
        *,
        theme: SafeSendTheme | None = None,
        title: str = "Progress",
        detail: str = "",
        size: int = 118,
        level: str = "primary",
    ) -> None:
        super().__init__(parent, theme=theme)
        self.value = max(0.0, min(1.0, value))
        fg, text_color, _border = _level_colors(self.theme, level)
        self.canvas = tk.Canvas(self, width=size, height=size, bg=self.theme.palette.surface, highlightthickness=0)
        self.canvas.pack(anchor="center", padx=self.theme.spacing.card_padding, pady=(self.theme.spacing.card_padding, 0))
        pad = 12
        self.canvas.create_oval(pad, pad, size - pad, size - pad, outline=self.theme.palette.surface_alt, width=10)
        self.canvas.create_arc(
            pad,
            pad,
            size - pad,
            size - pad,
            start=90,
            extent=-360 * self.value,
            style="arc",
            outline=text_color,
            width=10,
        )
        self.canvas.create_text(size / 2, size / 2 - 4, text=str(int(self.value * 100)), fill=self.theme.palette.text, font=font(self.theme, "metric_large", weight="semibold"))
        self.canvas.create_text(size / 2, size / 2 + 22, text=detail or title, fill=text_color, font=font(self.theme, "caption"))
        label(self, title, role="caption", theme=self.theme, surface="card", muted=True).pack(anchor="center", pady=(self.theme.spacing.sm, self.theme.spacing.card_padding))


def circular_progress(parent: tk.Widget, value: float = 0.0, *, theme: SafeSendTheme | None = None, **kwargs) -> CircularProgress:
    return CircularProgress(parent, value, theme=theme, **kwargs)


def loading_spinner(parent: tk.Widget, *, theme: SafeSendTheme | None = None) -> ctk.CTkProgressBar:
    bar = progress_bar(parent, 0, theme=theme)
    bar.configure(mode="indeterminate")
    bar.start()
    return bar


def skeleton_loader(parent: tk.Widget, rows: int = 3, *, theme: SafeSendTheme | None = None) -> Card:
    card = Card(parent, theme=theme)
    for idx in range(rows):
        ctk.CTkFrame(card, fg_color=card.theme.palette.surface_alt, height=16, corner_radius=8).pack(fill="x", padx=card.theme.spacing.card_padding, pady=card.theme.spacing.xs)
    return card


def status_dot(parent: tk.Widget, *, level: str = "default", theme: SafeSendTheme | None = None) -> ctk.CTkLabel:
    return status_badge(parent, " ", level=level, theme=theme, width=14, height=14, corner_radius=7)


def connection_indicator(parent: tk.Widget, connected: bool, *, theme: SafeSendTheme | None = None) -> ctk.CTkLabel:
    return status_badge(parent, "Connected" if connected else "Disconnected", level="success" if connected else "danger", theme=theme)


def health_indicator(parent: tk.Widget, status: str, *, theme: SafeSendTheme | None = None) -> ctk.CTkLabel:
    level = "success" if status.lower() in {"healthy", "ok", "connected"} else "warning" if status.lower() in {"warning", "degraded"} else "danger"
    return status_badge(parent, status, level=level, theme=theme)


# Dialogs and notifications


def confirmation_dialog(parent: tk.Widget, title: str, message: str, *, theme: SafeSendTheme | None = None) -> Modal:
    modal = Modal(parent, title, theme=theme)
    label(modal.body, message, theme=modal.theme, surface="card", wraplength=480).pack(padx=modal.theme.spacing.card_padding, pady=modal.theme.spacing.card_padding)
    return modal


warning_dialog = confirmation_dialog
success_dialog = confirmation_dialog
delete_confirmation = confirmation_dialog
input_dialog = confirmation_dialog
progress_dialog = confirmation_dialog
about_dialog = confirmation_dialog
wizard_dialog = wizard


def toast(parent: tk.Widget, message: str, *, level: str = "info", theme: SafeSendTheme | None = None) -> Modal:
    modal = Modal(parent, "", theme=theme, geometry="360x140")
    alert(modal.body, level.title(), message, level=level, theme=modal.theme).pack(fill="both", expand=True)
    return modal


success_toast = lambda parent, message, **kwargs: toast(parent, message, level="success", **kwargs)
error_toast = lambda parent, message, **kwargs: toast(parent, message, level="danger", **kwargs)
warning_toast = lambda parent, message, **kwargs: toast(parent, message, level="warning", **kwargs)
information_toast = lambda parent, message, **kwargs: toast(parent, message, level="info", **kwargs)
persistent_notification = alert
toast_notification = toast


# Help, dashboard, charts, and domain-specific composition


def popover(parent: tk.Widget, title: str, message: str, *, theme: SafeSendTheme | None = None) -> Card:
    return Card(parent, theme=theme, title=title, subtitle=message)


help_bubble = popover
inline_help = popover
guided_configuration_card = popover
ai_recommendation_card = popover
documentation_link = ghost_button
did_you_know_card = popover


def chart_card(parent: tk.Widget, title: str, *, theme: SafeSendTheme | None = None, height: int = 220) -> Card:
    card = Card(parent, theme=theme, title=title)
    canvas = tk.Canvas(card, height=height, bg="#07111F", highlightthickness=0, bd=0)
    canvas.grid(row=card.content_row, column=0, sticky="nsew", padx=card.theme.spacing.card_padding, pady=(0, card.theme.spacing.card_padding))

    def redraw(event: tk.Event | None = None) -> None:
        width = max(320, int(getattr(event, "width", canvas.winfo_width()) or 320))
        height_px = max(180, int(getattr(event, "height", canvas.winfo_height()) or height))
        canvas.delete("all")
        left, right = 54, width - 24
        top, bottom = 34, height_px - 42
        grid_color = "#8CA0B3"
        axis_color = "#6F8AA3"
        text_color = "#B8C8D8"
        title_color = "#D9E7F5"
        canvas.create_text(18, 18, text=title, anchor="w", fill=title_color, font=font(card.theme, "caption", weight="bold"))
        for index in range(5):
            y = bottom - ((bottom - top) / 4) * index
            canvas.create_line(left, y, right, y, fill=grid_color, width=1)
            canvas.create_text(left - 16, y, text="0" if index == 0 else f"{index * 25}%", anchor="e", fill=text_color, font=font(card.theme, "micro"))
        canvas.create_line(left, top, left, bottom, fill=axis_color, width=1)
        canvas.create_line(left, bottom, right, bottom, fill=axis_color, width=1)
        bars = [0.66, 0.54, 0.72, 0.48]
        bar_width = min(62, max(34, (right - left) / 10))
        gap = (right - left) / max(len(bars), 1)
        for index, value in enumerate(bars):
            x0 = left + gap * index + gap * 0.24
            x1 = x0 + bar_width
            total_height = (bottom - top) * value
            y0 = bottom - total_height
            segment1 = y0 + total_height * 0.56
            segment2 = y0 + total_height * 0.78
            canvas.create_rectangle(x0, segment1, x1, bottom, fill="#FF9B85", outline="")
            canvas.create_rectangle(x0, segment2, x1, segment1, fill="#4ECDD3", outline="")
            canvas.create_rectangle(x0, y0, x1, segment2, fill="#F5C989", outline="")
            canvas.create_text((x0 + x1) / 2, bottom + 18, text=f"Bar {index + 1}", fill=text_color, font=font(card.theme, "micro"))
        canvas.create_text((left + right) / 2, height_px - 14, text="Workspace metric", fill=text_color, font=font(card.theme, "micro"))

    canvas.bind("<Configure>", redraw)
    canvas.after_idle(redraw)
    card.canvas = canvas
    return card


line_chart = chart_card
area_chart = chart_card
bar_chart = chart_card
horizontal_bar_chart = chart_card
pie_chart = chart_card
donut_chart = chart_card
gauge = chart_card
progress_ring = circular_progress
funnel = chart_card
heat_map = chart_card
scatter_plot = chart_card
timeline_chart = chart_card
sparkline = chart_card
world_map = chart_card
us_map = chart_card
calendar_heatmap = chart_card


recent_activity = activity_feed
quick_actions = button_group
recent_campaigns = list_view
smtp_health = lambda parent, status="Unknown", **kwargs: MetricCard(parent, "SMTP Health", status, **kwargs)
deliverability_score = lambda parent, score="0", **kwargs: MetricCard(parent, "Deliverability Score", score, **kwargs)
domain_health = lambda parent, status="Unknown", **kwargs: MetricCard(parent, "Domain Health", status, **kwargs)
ai_insights = AIAssistantPanel
notifications = list_view


email_preview = text_area
desktop_preview = text_area
mobile_preview = text_area
inbox_preview = text_area
subject_tester = text_input
preheader_preview = text_input
html_viewer = code_editor
merge_tag_browser = tag_selector
signature_picker = dropdown
attachment_list = list_view


campaign_card = Card
campaign_timeline = timeline
campaign_status = status_badge
campaign_statistics = MetricCard
campaign_schedule = Card
campaign_queue = table
recipient_counter = MetricCard


smtp_card = Card
smtp_health_card = smtp_health
smtp_test_results = property_grid
smtp_statistics = MetricCard
connection_status = connection_indicator
authentication_status = health_indicator
rate_limit_display = MetricCard
thread_monitor = progress_bar


spam_score = lambda parent, score="0", **kwargs: MetricCard(parent, "Spam Score", score, **kwargs)
inbox_probability = lambda parent, value="0%", **kwargs: MetricCard(parent, "Inbox Probability", value, **kwargs)
spf_card = Card
dkim_card = Card
dmarc_card = Card
blacklist_status = status_badge
domain_reputation = MetricCard
bounce_summary = MetricCard


contact_card = Card
organization_card = Card
import_wizard = wizard
csv_preview = table
verification_badge = status_badge
contact_timeline = timeline
duplicate_finder = table
suppression_badge = status_badge


ai_assistant_panel = AIAssistantPanel
ai_chat = AIAssistantPanel
recommendation_card = popover
optimization_card = popover
risk_card = popover
ai_summary = popover
ai_action_button = primary_button
conversation_history = timeline


def empty_state(parent: tk.Widget, kind: str, *, theme: SafeSendTheme | None = None, action_text: str = "", action_command: Callable | None = None) -> EmptyState:
    title = {
        "campaigns": "No campaigns yet",
        "contacts": "No contacts imported yet",
        "smtp": "No SMTP accounts yet",
        "reports": "No reports yet",
        "templates": "No templates yet",
        "notifications": "No notifications",
        "search": "No results found",
        "offline": "Offline",
        "error": "Something went wrong",
        "coming_soon": "Coming soon",
    }.get(kind, kind.replace("_", " ").title())
    message = {
        "campaigns": "Create your first campaign to get started.",
        "contacts": "Import a CSV or add a contact manually.",
        "smtp": "Add your first SMTP server to begin testing.",
        "reports": "Reports appear after campaign activity.",
        "templates": "Create or import a template to start composing.",
        "notifications": "Important updates will appear here.",
        "search": "Try adjusting your search or filters.",
        "offline": "Check your connection and try again.",
        "error": "Please retry or review the details.",
        "coming_soon": "This area is reserved for a future milestone.",
    }.get(kind, "No records to show.")
    return EmptyState(parent, title, message, action_text=action_text, action_command=action_command, theme=theme)


no_campaigns = lambda parent, **kwargs: empty_state(parent, "campaigns", **kwargs)
no_contacts = lambda parent, **kwargs: empty_state(parent, "contacts", **kwargs)
no_smtp_accounts = lambda parent, **kwargs: empty_state(parent, "smtp", **kwargs)
no_reports = lambda parent, **kwargs: empty_state(parent, "reports", **kwargs)
no_templates = lambda parent, **kwargs: empty_state(parent, "templates", **kwargs)
no_notifications = lambda parent, **kwargs: empty_state(parent, "notifications", **kwargs)
no_search_results = lambda parent, **kwargs: empty_state(parent, "search", **kwargs)
offline_empty_state = lambda parent, **kwargs: empty_state(parent, "offline", **kwargs)
error_empty_state = lambda parent, **kwargs: empty_state(parent, "error", **kwargs)
coming_soon_empty_state = lambda parent, **kwargs: empty_state(parent, "coming_soon", **kwargs)


upload_zone = lambda parent, **kwargs: EmptyState(parent, "Drop files here", "Browse or drag files into this area.", **kwargs)
file_browser = list_view
attachment_card = Card
download_button = secondary_button
import_progress = progress_bar
export_progress = progress_bar


settings_group = Card
settings_card = Card
preference_toggle = toggle
api_key_display = password_input
license_card = Card
theme_selector = dropdown
backup_card = Card
update_card = Card


license_status = status_badge
activation_card = Card
encryption_status = health_indicator
password_strength = progress_bar
permission_badge = status_badge
audit_log = log_viewer


safe_send_score = lambda parent, value="0", **kwargs: MetricCard(parent, "SafeSend Score", value, **kwargs)
campaign_readiness = lambda parent, value="Draft", **kwargs: MetricCard(parent, "Campaign Readiness", value, **kwargs)
warm_up_progress = lambda parent, value=0.0, **kwargs: progress_bar(parent, value, **kwargs)
bounce_intelligence = lambda parent, value="0", **kwargs: MetricCard(parent, "Bounce Intelligence", value, **kwargs)
suppression_intelligence = lambda parent, value="0", **kwargs: MetricCard(parent, "Suppression Intelligence", value, **kwargs)
authentication_overview = property_grid
ai_reputation_advisor = AIAssistantPanel
campaign_risk_score = lambda parent, value="0", **kwargs: MetricCard(parent, "Campaign Risk Score", value, **kwargs)
sending_queue_monitor = progress_bar
thread_utilization = progress_bar
smtp_rotation_status = status_badge
mailbox_health = health_indicator
link_tracking_status = status_badge
open_tracking_status = status_badge
click_analytics = chart_card
bounce_analytics = chart_card
unsubscribe_analytics = chart_card
ai_campaign_review = AIAssistantPanel
guided_configuration_panel = guided_configuration_card


# Page templates


def page_template(parent: tk.Widget, title: str, subtitle: str = "", *, theme: SafeSendTheme | None = None) -> ctk.CTkFrame:
    theme = _theme(theme)
    page = page_container(parent, theme=theme)
    PageHeader(page, title, subtitle, theme=theme).grid(row=0, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=theme.spacing.page_padding)
    page.body = ctk.CTkFrame(page, fg_color=theme.palette.background, corner_radius=0)
    page.body.grid(row=1, column=0, sticky="nsew", padx=theme.spacing.page_padding)
    page.rowconfigure(1, weight=1)
    return page


dashboard_template = lambda parent, **kwargs: page_template(parent, "Dashboard", "Product overview and operational health.", **kwargs)
data_management_template = lambda parent, **kwargs: page_template(parent, "Data Management", "Import, clean, and organize records.", **kwargs)
settings_template = lambda parent, **kwargs: page_template(parent, "Settings", "Configure application preferences.", **kwargs)
wizard_template = lambda parent, **kwargs: page_template(parent, "Wizard", "Step-by-step setup flow.", **kwargs)
analytics_dashboard_template = lambda parent, **kwargs: page_template(parent, "Analytics Dashboard", "Performance and deliverability insights.", **kwargs)
campaign_builder_template = lambda parent, **kwargs: page_template(parent, "Campaign Builder", "Build, review, and prepare campaigns.", **kwargs)
compose_email_template = lambda parent, **kwargs: page_template(parent, "Compose Email", "Create and preview email templates.", **kwargs)
smtp_manager_template = lambda parent, **kwargs: page_template(parent, "SMTP Manager", "Manage sender accounts and health.", **kwargs)
contacts_template = lambda parent, **kwargs: page_template(parent, "Contacts", "Manage recipients and lists.", **kwargs)
reports_template = lambda parent, **kwargs: page_template(parent, "Reports", "Review campaign and queue activity.", **kwargs)
ai_assistant_template = lambda parent, **kwargs: page_template(parent, "AI Assistant", "Recommendations and assisted optimization.", **kwargs)
deliverability_center_template = lambda parent, **kwargs: page_template(parent, "Deliverability Center", "Domain, inbox, and reputation health.", **kwargs)
verification_center_template = lambda parent, **kwargs: page_template(parent, "Verification Center", "Validate contact quality and categories.", **kwargs)
license_management_template = lambda parent, **kwargs: page_template(parent, "License Management", "Activation, license, and security state.", **kwargs)
help_center_template = lambda parent, **kwargs: page_template(parent, "Help Center", "Guidance and documentation.", **kwargs)
