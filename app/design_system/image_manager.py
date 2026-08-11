from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image


class ImageManager:
    """Small shared cache for app-level bitmap resources.

    Vector-like icons are cached in app.design_system.icons. This manager covers
    file-backed images such as the SafeSend logo so sidebar rebuilds and route
    navigation do not repeatedly reopen files or allocate duplicate CTkImages.
    """

    def __init__(self) -> None:
        self._pil_cache: dict[tuple[str, bool], Image.Image] = {}
        self._ctk_cache: dict[tuple[str, bool, tuple[int, int] | None], ctk.CTkImage] = {}

    def logo(self, path: Path, *, collapsed: bool = False, size: tuple[int, int] | None = None) -> ctk.CTkImage:
        key = (str(path.resolve()), collapsed, size)
        cached = self._ctk_cache.get(key)
        if cached is not None:
            return cached

        source = self._logo_source(path, collapsed=collapsed)
        if size is None:
            width, height = source.size
            target_width = 38 if collapsed else min(148, max(112, width))
            target_height = 38 if collapsed else max(22, int(height * (target_width / max(width, 1))))
            size = (target_width, target_height)
        image = ctk.CTkImage(light_image=source, dark_image=source, size=size)
        self._ctk_cache[key] = image
        return image

    def _logo_source(self, path: Path, *, collapsed: bool) -> Image.Image:
        key = (str(path.resolve()), collapsed)
        cached = self._pil_cache.get(key)
        if cached is not None:
            return cached
        source = Image.open(path)
        if collapsed:
            edge = min(source.size)
            source = source.crop((0, 0, edge, edge))
        self._pil_cache[key] = source
        return source

    def clear(self) -> None:
        self._ctk_cache.clear()
        self._pil_cache.clear()


image_manager = ImageManager()
