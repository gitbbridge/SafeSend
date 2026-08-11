from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutSpec:
    min_window_width: int = 1040
    min_window_height: int = 680
    default_window_width: int = 1260
    default_window_height: int = 780
    default_table_column_width: int = 130
    min_table_column_width: int = 80
    tooltip_wrap_length: int = 280
    dashboard_columns: int = 4
    form_label_width: int = 150


LAYOUT = LayoutSpec()
