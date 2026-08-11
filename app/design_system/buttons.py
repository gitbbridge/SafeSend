from tkinter import ttk


BUTTON_STYLES = {
    "primary": "Primary.TButton",
    "secondary": "TButton",
    "outline": "Outline.TButton",
    "toolbar": "Toolbar.TButton",
    "icon": "Icon.TButton",
    "danger": "Danger.TButton",
    "success": "Success.TButton",
}


def configure_button_styles(style: ttk.Style, theme) -> None:
    palette = theme.palette
    typo = theme.typography
    space = theme.spacing
    base_padding = (space.button_pad_x, space.button_pad_y)

    style.configure(
        "TButton",
        padding=base_padding,
        background=palette.button_background,
        foreground=palette.text,
        borderwidth=1,
        bordercolor=palette.button_border,
        font=(typo.family, typo.button),
    )
    style.map("TButton", background=[("active", palette.button_hover), ("pressed", palette.button_pressed)], foreground=[("active", palette.text)])

    style.configure("Primary.TButton", padding=base_padding, background=palette.primary, foreground=palette.surface, borderwidth=0, font=(typo.family_semibold, typo.button))
    style.map("Primary.TButton", background=[("active", palette.primary_dark), ("pressed", palette.primary_dark)], foreground=[("active", palette.surface)])

    style.configure("Outline.TButton", padding=base_padding, background=palette.surface, foreground=palette.text, borderwidth=1, bordercolor=palette.border)
    style.configure("Toolbar.TButton", padding=(space.md, space.sm), background=palette.surface, foreground=palette.text, borderwidth=1, bordercolor=palette.border_soft)
    style.configure("Icon.TButton", padding=(space.sm, space.sm), background=palette.button_background, foreground=palette.text, borderwidth=1, bordercolor=palette.button_border)
    style.configure("Danger.TButton", padding=base_padding, background=palette.button_background, foreground=palette.danger, borderwidth=1, bordercolor=palette.button_border)
    style.configure("Success.TButton", padding=base_padding, background=palette.button_background, foreground=palette.success, borderwidth=1, bordercolor=palette.button_border)

