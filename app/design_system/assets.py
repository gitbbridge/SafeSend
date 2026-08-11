from pathlib import Path

from app.utils.paths import BASE_DIR


ASSETS_DIR = BASE_DIR / "app" / "assets"
LOGO_ICO = ASSETS_DIR / "safesend_logo.ico"
LOGO_PNG = ASSETS_DIR / "safesend_logo.png"


def asset_path(path: Path) -> str:
    return str(path)

