from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    background: str
    surface: str
    surface_alt: str
    surface_soft: str
    text: str
    text_muted: str
    border: str
    border_soft: str
    hover: str
    pressed: str
    primary: str
    primary_dark: str
    secondary: str
    divider: str
    placeholder: str
    selection: str
    table_hover: str
    table_selected: str
    button_background: str
    button_hover: str
    button_pressed: str
    button_border: str
    sidebar: str
    sidebar_hover: str
    sidebar_selected: str
    sidebar_text: str
    sidebar_muted: str
    success: str
    warning: str
    orange: str
    danger: str
    info: str
    chart_primary: str
    chart_secondary: str
    chart_warning: str
    chart_danger: str


NEW_SKIN_COLORS = Palette(
    background="#F5F8FA",
    surface="#FFFFFF",
    surface_alt="#F5F8FA",
    surface_soft="#F8FBFD",
    text="#33475B",
    text_muted="#516F90",
    border="#CBD6E2",
    border_soft="#DDE8F0",
    hover="#EAF0F6",
    pressed="#DCE6EF",
    primary="#FF5C35",
    primary_dark="#E04826",
    secondary="#425B76",
    divider="#DDE8F0",
    placeholder="#7C98B6",
    selection="#E5F5F8",
    table_hover="#F5F8FA",
    table_selected="#E5F5F8",
    button_background="#EAF0F6",
    button_hover="#DDE8F0",
    button_pressed="#CBD6E2",
    button_border="#CBD6E2",
    sidebar="#213343",
    sidebar_hover="#2E475D",
    sidebar_selected="#425B76",
    sidebar_text="#FFFFFF",
    sidebar_muted="#B6C7D6",
    success="#00A38D",
    warning="#FFB020",
    orange="#FF5C35",
    danger="#D94C53",
    info="#0091AE",
    chart_primary="#FF5C35",
    chart_secondary="#00A4BD",
    chart_warning="#FFB020",
    chart_danger="#D94C53",
)


ORIGINAL_SKIN_COLORS = Palette(
    background="#F5F8FB",
    surface="#FFFFFF",
    surface_alt="#F5F8FB",
    surface_soft="#FAFCFE",
    text="#172033",
    text_muted="#65758B",
    border="#D9E2EC",
    border_soft="#EEF3F8",
    hover="#E6EEF5",
    pressed="#DCE8F3",
    primary="#0F75BC",
    primary_dark="#0A4F85",
    secondary="#65758B",
    divider="#E7EEF5",
    placeholder="#9FB3C8",
    selection="#DCE8F3",
    table_hover="#F0F6FB",
    table_selected="#DCE8F3",
    button_background="#F5F8FB",
    button_hover="#E6EEF5",
    button_pressed="#DCE8F3",
    button_border="#D9E2EC",
    sidebar="#102A43",
    sidebar_hover="#173D5F",
    sidebar_selected="#173D5F",
    sidebar_text="#EEF6FF",
    sidebar_muted="#B9C9D8",
    success="#2F9E44",
    warning="#F2C94C",
    orange="#F2994A",
    danger="#D64545",
    info="#2F80ED",
    chart_primary="#0F75BC",
    chart_secondary="#2F80ED",
    chart_warning="#F2C94C",
    chart_danger="#D64545",
)
