"""Compatibility facade for the SafeSend design system.

New code should import from app.design_system. Existing UI modules can continue
using app.ui.theme while the application migrates screen-by-screen.
"""

from app.design_system import (
    ASSETS_DIR,
    BUTTON_ICONS,
    LOGO_ICO,
    LOGO_PNG,
    NEW_SKIN,
    ORIGINAL_SKIN,
    ROUTE_ICONS,
    STATUS_LEVELS,
    Palette,
    SafeSendTheme,
    Spacing,
    Tooltip,
    Typography,
    active_theme,
    apply_theme,
    asset_path,
    font,
    get_button_icon,
    get_route_icon,
    help_text,
    icon_text,
    status_style,
    tooltip,
)

