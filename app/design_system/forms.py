from tkinter import ttk


FORM_STYLES = {
    "label": "TLabel",
    "help": "Muted.TLabel",
    "validation": "Danger.TLabel",
    "warning": "Warning.TLabel",
    "section": "SectionTitle.TLabel",
}


def configure_form_styles(style: ttk.Style, theme) -> None:
    palette = theme.palette
    typo = theme.typography
    style.configure("TEntry", fieldbackground=palette.surface_alt, foreground=palette.text, bordercolor=palette.border, padding=(10, 8), font=(typo.family, typo.body))
    style.configure("TCombobox", fieldbackground=palette.surface_alt, foreground=palette.text, bordercolor=palette.border, padding=(10, 8), font=(typo.family, typo.body))
    style.configure("TCheckbutton", background=palette.background, foreground=palette.text, font=(typo.family, typo.body))
    style.configure("TLabelframe", background=palette.background, foreground=palette.text, bordercolor=palette.border_soft)
    style.configure("TLabelframe.Label", background=palette.background, foreground=palette.text, font=(typo.family_semibold, typo.section_header))
