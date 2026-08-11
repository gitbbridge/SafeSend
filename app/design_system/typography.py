from dataclasses import dataclass


FONT_CHOICES = ("Segoe UI", "Arial", "Calibri", "Georgia", "Times New Roman", "Courier New")
EDITOR_SIZE_CHOICES = ("10", "11", "12", "14", "16", "18", "22", "28", "36")


@dataclass(frozen=True)
class Typography:
    family: str = "Segoe UI"
    family_semibold: str = "Segoe UI Semibold"
    mono: str = "Consolas"
    body: int = 11
    small: int = 10
    caption: int = 10
    button: int = 11
    toolbar: int = 11
    table: int = 11
    status_badge: int = 10
    tooltip: int = 10
    title: int = 28
    window_title: int = 22
    page_title: int = 30
    section_header: int = 17
    panel_title: int = 16
    card_header: int = 15
    card_subtitle: int = 10
    sidebar: int = 11
    brand: int = 20
    metric: int = 32
    metric_large: int = 40
    editor: int = 13
    source: int = 11


def font(theme, role: str = "body", scale: float = 1.0, weight: str = "") -> tuple:
    typo = theme.typography
    size = int(getattr(typo, role, typo.body) * scale)
    family = typo.family_semibold if weight == "semibold" else typo.family
    if role == "source":
        family = typo.mono
    return (family, size, weight) if weight and weight != "semibold" else (family, size)
