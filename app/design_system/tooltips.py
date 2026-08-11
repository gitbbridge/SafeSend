import tkinter as tk


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.window: tk.Toplevel | None = None
        self._after_id: str | None = None
        widget.bind("<Enter>", self.schedule, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<Destroy>", self.hide, add="+")

    def schedule(self, _event=None) -> None:
        if not self.text or self.window:
            return
        self.cancel()
        self._after_id = self.widget.after(650, self.show)

    def cancel(self) -> None:
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def show(self, _event=None) -> None:
        self._after_id = None
        if not self.text or self.window:
            return
        from app.design_system.theme import active_theme
        from app.design_system.typography import font
        import customtkinter as ctk

        theme = active_theme()
        palette = theme.palette
        space = theme.spacing
        x = self.widget.winfo_rootx() + space.xl
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + space.sm
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_attributes("-topmost", True)
        self.window.configure(background=palette.border)

        lines = [line.strip() for line in self.text.splitlines() if line.strip()]
        title = lines[0] if lines else ""
        details = lines[1:]
        is_explainer = any(":" in line for line in details)
        wrap = 520 if is_explainer else 280

        shell = ctk.CTkFrame(
            self.window,
            fg_color=palette.surface,
            corner_radius=6,
            border_width=1,
            border_color=palette.border,
        )
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(1, weight=1)

        ctk.CTkFrame(shell, fg_color=palette.primary, width=4, corner_radius=2).grid(
            row=0,
            column=0,
            rowspan=3,
            sticky="nsw",
            padx=(space.md, 0),
            pady=space.md,
        )
        ctk.CTkLabel(
            shell,
            text=title,
            fg_color=palette.surface,
            text_color=palette.text,
            font=font(theme, "panel_title", weight="semibold"),
            anchor="w",
            justify="left",
        ).grid(row=0, column=1, sticky="ew", padx=space.md, pady=(space.md, space.xs))

        if is_explainer:
            body = ctk.CTkFrame(shell, fg_color=palette.surface_alt, corner_radius=4, border_width=0)
            body.grid(row=1, column=1, sticky="ew", padx=(space.md, space.lg), pady=(0, space.md))
            body.columnconfigure(1, weight=1)
            for index, line in enumerate(details):
                key, value = _split_detail(line)
                ctk.CTkLabel(
                    body,
                    text=key,
                    fg_color=palette.surface_alt,
                    text_color=palette.text,
                    font=font(theme, "caption", weight="semibold"),
                    anchor="nw",
                    justify="left",
                    width=118,
                ).grid(row=index, column=0, sticky="nw", padx=(space.md, space.sm), pady=(space.xs if index else space.sm, space.xs))
                ctk.CTkLabel(
                    body,
                    text=value,
                    fg_color=palette.surface_alt,
                    text_color=palette.text_muted,
                    font=font(theme, "caption"),
                    anchor="nw",
                    justify="left",
                    wraplength=wrap - 150,
                ).grid(row=index, column=1, sticky="ew", padx=(0, space.md), pady=(space.xs if index else space.sm, space.xs))
        elif details:
            ctk.CTkLabel(
                shell,
                text="\n".join(details),
                fg_color=palette.surface,
                text_color=palette.text_muted,
                font=font(theme, "caption"),
                anchor="w",
                justify="left",
                wraplength=wrap,
            ).grid(row=1, column=1, sticky="ew", padx=(space.md, space.lg), pady=(0, space.md))

        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        x = min(x, max(0, screen_width - width - space.md))
        y = min(y, max(0, screen_height - height - space.md))
        self.window.wm_geometry(f"+{x}+{y}")

    def hide(self, _event=None) -> None:
        self.cancel()
        if self.window:
            self.window.destroy()
            self.window = None


def _split_detail(line: str) -> tuple[str, str]:
    if ":" not in line:
        return "", line
    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def tooltip(widget: tk.Widget, text: str) -> tk.Widget:
    instance = Tooltip(widget, text)
    attached = getattr(widget, "_safesend_tooltips", [])
    attached.append(instance)
    widget._safesend_tooltips = attached
    return widget


def help_text(label: str, recommended: str = "", explanation: str = "") -> str:
    lines = [label]
    if recommended:
        lines.append(f"Recommended: {recommended}")
    if explanation:
        lines.append(f"Explanation: {explanation}")
    return "\n".join(lines)
