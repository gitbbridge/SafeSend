from tkinter import ttk


TABLE_TAGS = {
    "even": "evenrow",
    "odd": "oddrow",
    "empty": "empty",
    "hover": "hoverrow",
}


def configure_table_styles(style: ttk.Style, theme) -> None:
    palette = theme.palette
    typo = theme.typography
    space = theme.spacing
    style.configure(
        "Treeview",
        rowheight=space.table_row_height,
        fieldbackground=palette.surface,
        background=palette.surface,
        foreground=palette.text,
        bordercolor=palette.border_soft,
        borderwidth=0,
        relief="flat",
        font=(typo.family, typo.table),
        padding=(space.sm, 0),
    )
    style.configure(
        "Treeview.Heading",
        font=(typo.family_semibold, typo.small),
        background=palette.surface_alt,
        foreground=palette.text,
        bordercolor=palette.border_soft,
        relief="flat",
        padding=(space.md, space.md),
    )
    style.map("Treeview", background=[("selected", palette.table_selected)], foreground=[("selected", palette.text)])


def configure_table_tags(tree: ttk.Treeview, theme) -> None:
    palette = theme.palette
    tree.tag_configure(TABLE_TAGS["even"], background=palette.surface)
    tree.tag_configure(TABLE_TAGS["odd"], background=palette.surface_soft)
    tree.tag_configure(TABLE_TAGS["empty"], background=palette.surface, foreground=palette.text_muted)
    tree.tag_configure(TABLE_TAGS["hover"], background=palette.table_hover)
