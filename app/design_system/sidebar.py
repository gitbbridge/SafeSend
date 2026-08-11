from tkinter import ttk


def configure_sidebar_styles(style: ttk.Style, theme) -> None:
    palette = theme.palette
    typo = theme.typography
    space = theme.spacing
    style.configure("Sidebar.TFrame", background=palette.sidebar)
    style.configure("Brand.TLabel", background=palette.sidebar, foreground=palette.sidebar_text, font=(typo.family_semibold, typo.brand))
    style.configure("SidebarMuted.TLabel", background=palette.sidebar, foreground=palette.sidebar_muted, font=(typo.family, typo.small))
    style.configure("Sidebar.TButton", anchor="w", padding=(space.lg, space.md), background=palette.sidebar, foreground=palette.sidebar_text, borderwidth=0, font=(typo.family, typo.sidebar))
    style.configure("SidebarSelected.TButton", anchor="w", padding=(space.lg, space.md), background=palette.sidebar_selected, foreground=palette.sidebar_text, borderwidth=0, font=(typo.family_semibold, typo.sidebar))
    style.map("Sidebar.TButton", background=[("active", palette.sidebar_hover), ("pressed", palette.sidebar_selected)], foreground=[("active", palette.sidebar_text)])

