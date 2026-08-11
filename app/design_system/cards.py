from tkinter import ttk


CARD_STYLES = {
    "base": "Card.TFrame",
    "elevated": "ElevatedCard.TFrame",
    "panel": "Panel.TFrame",
    "statistics": "StatisticsCard.TFrame",
    "dashboard": "DashboardCard.TFrame",
    "configuration": "ConfigurationCard.TFrame",
    "chart": "ChartCard.TFrame",
    "information": "InformationCard.TFrame",
    "warning": "WarningCard.TFrame",
    "help": "HelpCard.TFrame",
    "summary": "SummaryCard.TFrame",
}


def configure_card_styles(style: ttk.Style, theme) -> None:
    palette = theme.palette
    style.configure("Card.TFrame", background=palette.surface, relief="solid", borderwidth=1, bordercolor=palette.border_soft)
    style.configure("ElevatedCard.TFrame", background=palette.surface, relief="solid", borderwidth=1, bordercolor=palette.border)
    style.configure("Panel.TFrame", background=palette.surface)
    for style_name in [
        "StatisticsCard.TFrame",
        "DashboardCard.TFrame",
        "ConfigurationCard.TFrame",
        "ChartCard.TFrame",
        "InformationCard.TFrame",
        "HelpCard.TFrame",
        "SummaryCard.TFrame",
    ]:
        style.configure(style_name, background=palette.surface, relief="solid", borderwidth=1, bordercolor=palette.border_soft)
    style.configure("WarningCard.TFrame", background=palette.surface, relief="solid", borderwidth=1, bordercolor=palette.warning)

