import logging

from app.utils.paths import LOG_DIR


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if any(getattr(handler, "_safesend_handler", False) for handler in root.handlers):
        return
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = logging.FileHandler(LOG_DIR / "safesend.log", encoding="utf-8")
    stream_handler = logging.StreamHandler()
    for handler in (file_handler, stream_handler):
        handler.setFormatter(formatter)
        handler._safesend_handler = True
        root.addHandler(handler)
    root.setLevel(logging.INFO)
