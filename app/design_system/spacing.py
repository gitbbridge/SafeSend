from dataclasses import dataclass


@dataclass(frozen=True)
class Spacing:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32
    page_padding: int = 28
    page_margin: int = 28
    section_gap: int = 16
    card_padding: int = 20
    card_gap: int = 12
    grid_gap: int = 12
    toolbar_padding: int = 12
    sidebar_padding: int = 18
    button_pad_x: int = 14
    button_pad_y: int = 9
    form_row_gap: int = 6
    table_row_height: int = 46
    sidebar_width: int = 230
    toolbar_height: int = 48
    status_bar_height: int = 28
    card_width: int = 260
    chart_width: int = 520
    page_width: int = 1180
    panel_width: int = 420
    icon_size: int = 18
