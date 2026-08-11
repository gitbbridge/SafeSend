from tkinter import ttk


def configure_toolbar_styles(style: ttk.Style, theme) -> None:
    palette = theme.palette
    style.configure("Toolbar.TFrame", background=palette.surface, relief="solid", borderwidth=1, bordercolor=palette.border_soft)

