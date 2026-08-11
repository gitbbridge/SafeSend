import itertools
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk

from app.design_system.theme import active_theme


STATUS_LEVELS = {
    "draft": "draft",
    "ready": "success",
    "active": "success",
    "scheduled": "info",
    "completed": "success",
    "sent": "success",
    "success": "success",
    "healthy": "success",
    "enabled": "success",
    "clean": "success",
    "deliverable": "success",
    "queued": "info",
    "pending": "info",
    "running": "info",
    "not tested": "draft",
    "unknown": "draft",
    "archived": "draft",
    "disabled": "draft",
    "paused": "warning",
    "risky": "warning",
    "warning": "warning",
    "skipped": "warning",
    "failed": "danger",
    "error": "danger",
    "critical": "danger",
    "suppressed": "danger",
    "undeliverable": "danger",
    "listed": "danger",
}


class ModernTable(ctk.CTkFrame):
    """Lightweight Treeview-compatible table rendered on a canvas.

    The earlier CustomTkinter table created one frame and one label per visible
    cell. That looked nice, but large contact/template grids became sluggish.
    This keeps the same small API surface used by the app while drawing only
    the rows currently visible in the viewport.
    """

    def __init__(self, parent: tk.Widget, columns: tuple[str, ...], headings: tuple[str, ...] | None = None, height: int = 12) -> None:
        self.theme = active_theme()
        self.palette = self.theme.palette
        super().__init__(
            parent,
            fg_color=self.palette.surface,
            corner_radius=4,
            border_width=1,
            border_color=self.palette.border_soft,
        )
        self.columns = columns
        self.headings = dict(zip(columns, headings or columns))
        self.height = height
        self._id_counter = itertools.count(1)
        self._items: dict[str, dict] = {}
        self._order: list[str] = []
        self._selection: list[str] = []
        self._focus = ""
        self._column_options: dict[str, dict] = {column: {"width": 130, "minwidth": 80, "stretch": True} for column in columns}
        self._heading_commands: dict[str, callable] = {}
        self._bindings: dict[str, list[callable]] = {}
        self._selectmode = "browse"
        self._draw_after_id: str | None = None
        self._row_height = 40
        self._header_height = 36
        self._table_font_size = max(9, self.theme.typography.table - 1)
        self._header_font_size = max(8, self.theme.typography.small - 1)
        self._badge_font_size = max(8, self.theme.typography.status_badge - 1)
        self._font = (self.theme.typography.family, self._table_font_size)
        self._header_font = (self.theme.typography.family_semibold, self._header_font_size)
        self._badge_font = (self.theme.typography.family_semibold, self._badge_font_size)
        self._footer_font = (self.theme.typography.family, max(8, self.theme.typography.caption - 1))
        self._footer_bold_font = (self.theme.typography.family_semibold, max(8, self.theme.typography.caption - 1))
        self._measure_font: tkfont.Font | None = None
        self._badge_measure_font: tkfont.Font | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header = tk.Canvas(self, height=self._header_height, bg=self.palette.surface_alt, highlightthickness=0, bd=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.bind("<Button-1>", self._header_click, add="+")
        self.header.bind("<Configure>", lambda _event: self._draw_header(), add="+")

        body = ctk.CTkFrame(self, fg_color=self.palette.surface, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            body,
            bg=self.palette.surface,
            highlightthickness=0,
            bd=0,
            height=max(240, height * self.theme.spacing.table_row_height),
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ctk.CTkScrollbar(
            body,
            orientation="vertical",
            command=self.canvas.yview,
            button_color=self.palette.border,
            button_hover_color=self.palette.hover,
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.x_scrollbar = ctk.CTkScrollbar(
            self,
            orientation="horizontal",
            command=self._xview,
            button_color=self.palette.border,
            button_hover_color=self.palette.hover,
            height=12,
        )
        self.x_scrollbar.grid(row=2, column=0, sticky="ew", padx=10, pady=(8, 4))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.configure(xscrollcommand=self.x_scrollbar.set)
        self.canvas.bind("<Configure>", lambda _event: self._schedule_draw_rows(), add="+")
        self.canvas.bind("<Button-1>", self._canvas_click, add="+")
        self.canvas.bind("<Double-1>", self._canvas_double_click, add="+")
        self.canvas.bind("<MouseWheel>", self._mousewheel, add="+")

        self.footer = ctk.CTkFrame(self, fg_color=self.palette.surface, corner_radius=0)
        self.footer.grid(row=3, column=0, sticky="ew", padx=10, pady=(2, 10))
        self.footer.columnconfigure(1, weight=1)
        self.powered_label = ctk.CTkLabel(
            self.footer,
            text="Powered by SafeSend",
            fg_color=self.palette.surface,
            text_color=self.palette.text_muted,
            font=self._footer_font,
        )
        self.powered_label.grid(row=0, column=0, sticky="w")
        self.pagination = ctk.CTkLabel(
            self.footer,
            text="<< First    < Prev    1    2    3    4    5    Next >    Last >>",
            fg_color=self.palette.surface,
            text_color=self.palette.info,
            font=self._footer_bold_font,
        )
        self.pagination.grid(row=0, column=1, sticky="e")
        self._draw_header()
        self._schedule_draw_rows()

    def _draw_header(self) -> None:
        self.header.delete("all")
        widths = self._column_widths(max(1, self.header.winfo_width()))
        total_width = max(sum(widths), self.header.winfo_width())
        self.header.configure(scrollregion=(0, 0, total_width, self._header_height))
        self.header.create_rectangle(0, 0, total_width, self._header_height, fill=self.palette.surface_alt, outline="")
        x = 0
        for column, width in zip(self.columns, widths):
            self.header.create_line(x, 0, x, self._header_height, fill=self.palette.border_soft)
            self.header.create_text(
                x + self.theme.spacing.md,
                self._header_height / 2,
                text=str(self.headings.get(column, column)).upper(),
                anchor="w",
                fill=self.palette.secondary,
                font=self._header_font,
            )
            x += width
        self.header.create_line(0, self._header_height - 1, total_width, self._header_height - 1, fill=self.palette.border_soft)

    def _schedule_draw_rows(self) -> None:
        if self._draw_after_id:
            return
        try:
            self._draw_after_id = self.after_idle(self._draw_rows)
        except tk.TclError:
            self._draw_rows()

    def destroy(self) -> None:
        if self._draw_after_id:
            try:
                self.after_cancel(self._draw_after_id)
            except tk.TclError:
                pass
            self._draw_after_id = None
        self._bindings.clear()
        self._heading_commands.clear()
        self._items.clear()
        self._order.clear()
        self._selection.clear()
        self._focus = ""
        super().destroy()

    def _draw_rows(self) -> None:
        self._draw_after_id = None
        self.canvas.delete("rows")
        row_count = len(self._order)
        canvas_width = max(1, self.canvas.winfo_width())
        canvas_height = max(1, self.canvas.winfo_height())
        widths = self._column_widths(canvas_width)
        total_width = max(canvas_width, sum(widths))
        total_height = max(canvas_height, row_count * self._row_height)
        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))
        self._update_footer(row_count)
        if not row_count:
            return
        if row_count == 1:
            only_item = self._items[self._order[0]]
            if "empty" in only_item.get("tags", ()):
                self._draw_empty_state(canvas_width, canvas_height, only_item)
                return

        top = self.canvas.canvasy(0)
        bottom = top + canvas_height
        first = max(0, int(top // self._row_height) - 2)
        last = min(row_count, int(bottom // self._row_height) + 3)
        for row_index in range(first, last):
            item_id = self._order[row_index]
            item = self._items[item_id]
            selected = item_id in self._selection
            tags = item.get("tags", ())
            row_color = self.palette.table_selected if selected else (self.palette.surface_soft if row_index % 2 == 0 else self.palette.surface)
            text_color = self.palette.text_muted if "empty" in tags else self.palette.text
            if "empty" in tags:
                row_color = self.palette.surface
            y1 = row_index * self._row_height
            y2 = y1 + self._row_height
            self.canvas.create_rectangle(0, y1, total_width, y2, fill=row_color, outline="", tags=("rows",))
            self.canvas.create_line(0, y2 - 1, total_width, y2 - 1, fill=self.palette.border_soft, tags=("rows",))
            x = 0
            for column, value, width in zip(self.columns, item["values"], widths):
                value_text = str(value)
                badge = self._status_badge_colors(value_text)
                if "actions" in column.lower() and value_text and "empty" not in tags:
                    self._draw_action_button(x + self.theme.spacing.md, y1 + (self._row_height - 26) / 2, value_text, max(44, width - self.theme.spacing.md * 2))
                elif badge and "empty" not in tags:
                    fg, bg, border = badge
                    self._draw_status_tag(
                        x + self.theme.spacing.md,
                        y1 + (self._row_height - 22) / 2,
                        value_text,
                        fg,
                        bg,
                        border,
                        max(32, width - self.theme.spacing.md * 2),
                    )
                else:
                    self.canvas.create_text(
                        x + self.theme.spacing.md,
                        y1 + self._row_height / 2,
                        text=self._ellipsize(value_text, max(24, width - self.theme.spacing.md * 2)),
                        anchor="w",
                        fill=text_color,
                        font=self._font,
                        tags=("rows",),
                    )
                x += width

    def _draw_empty_state(self, canvas_width: int, canvas_height: int, item: dict) -> None:
        values = [str(value) for value in item.get("values", ()) if str(value).strip()]
        message = values[0] if values else "No records to show yet."
        center_x = canvas_width / 2
        center_y = max(118, canvas_height / 2)
        icon_w = 58
        icon_h = 42
        x1 = center_x - icon_w / 2
        y1 = center_y - 52
        self._rounded_rect(self.canvas, x1, y1, x1 + icon_w, y1 + icon_h, 7, self.palette.surface_soft, self.palette.border_soft, ("rows",))
        self.canvas.create_line(x1 + 8, y1 + 10, center_x, y1 + 25, x1 + icon_w - 8, y1 + 10, fill=self.palette.border, width=2, tags=("rows",))
        self.canvas.create_line(x1 + 8, y1 + icon_h - 8, x1 + 24, y1 + 23, fill=self.palette.border_soft, width=2, tags=("rows",))
        self.canvas.create_line(x1 + icon_w - 8, y1 + icon_h - 8, x1 + icon_w - 24, y1 + 23, fill=self.palette.border_soft, width=2, tags=("rows",))
        self.canvas.create_text(
            center_x,
            center_y + 12,
            text=message,
            anchor="center",
            fill=self.palette.text_muted,
            font=(self.theme.typography.family, self.theme.typography.body),
            tags=("rows",),
        )

    def _column_widths(self, available_width: int) -> list[int]:
        bases = [
            max(
                int(self._column_options.get(column, {}).get("minwidth", 80)),
                int(self._column_options.get(column, {}).get("width", 130)),
            )
            for column in self.columns
        ]
        stretch_indices = [idx for idx, column in enumerate(self.columns) if self._column_options.get(column, {}).get("stretch", True)]
        total = max(1, sum(bases))
        if available_width >= total and stretch_indices:
            extra = available_width - total
            each = extra // len(stretch_indices)
            for idx in stretch_indices:
                bases[idx] += each
            bases[stretch_indices[-1]] += extra - each * len(stretch_indices)
        elif available_width < total:
            return bases
        return bases

    def _ellipsize(self, text: str, max_width: int) -> str:
        if not text:
            return ""
        font = self._measurement_font()
        if font.measure(text) <= max_width:
            return text
        ellipsis = "..."
        low, high = 0, len(text)
        while low < high:
            mid = (low + high) // 2
            if font.measure(text[:mid] + ellipsis) <= max_width:
                low = mid + 1
            else:
                high = mid
        return text[: max(0, low - 1)] + ellipsis

    def _measurement_font(self) -> tkfont.Font:
        if self._measure_font is None:
            self._measure_font = tkfont.Font(family=self.theme.typography.family, size=self._table_font_size)
        return self._measure_font

    def _badge_measurement_font(self) -> tkfont.Font:
        if self._badge_measure_font is None:
            self._badge_measure_font = tkfont.Font(family=self.theme.typography.family_semibold, size=self._badge_font_size)
        return self._badge_measure_font

    def _status_badge_colors(self, value: str) -> tuple[str, str, str] | None:
        key = value.strip().lower()
        if not key:
            return None
        level = STATUS_LEVELS.get(key)
        if not level:
            return None
        colors = {
            "success": (self.palette.success, "#E6F7F4", "#B7ECE4"),
            "info": (self.palette.info, "#E5F5F8", "#B7ECEF"),
            "warning": ("#B06A00", "#FFF4DE", "#FFE2A8"),
            "danger": (self.palette.danger, "#FDECEE", "#F6C9CD"),
            "draft": (self.palette.text_muted, "#F6F8FA", "#D7DEE7"),
        }
        return colors[level]

    def _draw_status_tag(self, x: float, y: float, text: str, fg: str, bg: str, border: str, max_width: float) -> None:
        label = self._ellipsize(text.upper(), max(24, int(max_width) - 22))
        tag_width = min(max_width, self._badge_measurement_font().measure(label) + 26)
        self._rounded_rect(self.canvas, x, y, x + tag_width, y + 22, 3, bg, border, ("rows",))
        self.canvas.create_rectangle(x, y + 4, x + 3, y + 18, fill=fg, outline="", tags=("rows",))
        self.canvas.create_text(
            x + tag_width / 2 + 2,
            y + 11,
            text=label,
            anchor="center",
            fill=fg,
            font=self._badge_font,
            tags=("rows",),
        )

    def _draw_action_button(self, x: float, y: float, text: str, max_width: float) -> None:
        label = self._ellipsize(text, max(28, int(max_width) - 18))
        button_width = min(max_width, max(58, self._measurement_font().measure(label) + 24))
        self._rounded_rect(self.canvas, x, y, x + button_width, y + 26, 3, self.palette.button_background, self.palette.button_border, ("rows",))
        self.canvas.create_text(
            x + button_width / 2,
            y + 13,
            text=label,
            anchor="center",
            fill=self.palette.secondary,
            font=(self.theme.typography.family_semibold, self.theme.typography.caption),
            tags=("rows",),
        )

    def _update_footer(self, row_count: int) -> None:
        self.powered_label.configure(text="Powered by SafeSend")
        if row_count <= 1 and self._order:
            only_item = self._items.get(self._order[0], {})
            if "empty" in only_item.get("tags", ()):
                self.pagination.configure(text="")
                return
        pages = max(1, (row_count + max(self.height, 1) - 1) // max(self.height, 1))
        page_numbers = "    ".join(str(page) for page in range(1, min(pages, 5) + 1))
        self.pagination.configure(text=f"<< First    < Prev    {page_numbers}    Next >    Last >>" if row_count else "")

    def _rounded_rect(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, radius: float, fill: str, outline: str, tags: tuple[str, ...]) -> None:
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=outline, tags=tags)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline=outline, tags=tags)
        canvas.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, fill=fill, outline=outline, tags=tags)
        canvas.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, fill=fill, outline=outline, tags=tags)
        canvas.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, fill=fill, outline=outline, tags=tags)
        canvas.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, fill=fill, outline=outline, tags=tags)

    def _header_click(self, event) -> None:
        x = self.header.canvasx(event.x)
        cursor = 0
        for column, width in zip(self.columns, self._column_widths(max(1, self.header.winfo_width()))):
            if cursor <= x <= cursor + width:
                self._invoke_heading(column)
                return
            cursor += width

    def _xview(self, *args) -> None:
        self.canvas.xview(*args)
        self.header.xview(*args)

    def _canvas_click(self, event) -> None:
        item_id = self._item_at_y(event.y)
        if item_id:
            self._select_item(item_id, event)

    def _canvas_double_click(self, event) -> None:
        item_id = self._item_at_y(event.y)
        if item_id:
            self._double_click(item_id, event)

    def _item_at_y(self, y: int) -> str:
        row_index = int(self.canvas.canvasy(y) // self._row_height)
        if 0 <= row_index < len(self._order):
            return self._order[row_index]
        return ""

    def _mousewheel(self, event) -> str:
        delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta * 3, "units")
        self._draw_rows()
        return "break"

    def _invoke_heading(self, column: str) -> None:
        command = self._heading_commands.get(column)
        if command:
            command()

    def _select_item(self, item_id: str, event=None) -> None:
        if item_id not in self._items:
            return
        values = self._items[item_id].get("values") or []
        if values and values[0] == "":
            return
        if self._selectmode == "extended" and event is not None and getattr(event, "state", 0) & 0x0004:
            if item_id in self._selection:
                self._selection.remove(item_id)
            else:
                self._selection.append(item_id)
        else:
            self._selection = [item_id]
        self._focus = item_id
        self._draw_rows()
        self._emit("<<TreeviewSelect>>")

    def _double_click(self, item_id: str, event=None) -> None:
        self._select_item(item_id, event)
        self._emit("<Double-1>")

    def _emit(self, sequence: str) -> None:
        for callback in self._bindings.get(sequence, []):
            callback(None)

    def heading(self, column: str, text: str | None = None, command=None, **_kwargs) -> None:
        if text is not None:
            self.headings[column] = text
        if command is not None:
            self._heading_commands[column] = command
        self._draw_header()

    def column(self, column: str, **kwargs) -> None:
        self._column_options.setdefault(column, {}).update(kwargs)
        self._draw_header()
        self._schedule_draw_rows()

    def configure(self, **kwargs) -> None:
        if "columns" in kwargs:
            new_columns = tuple(kwargs.pop("columns"))
            self.columns = new_columns
            self.headings = {column: self.headings.get(column, column) for column in new_columns}
            self._column_options = {column: self._column_options.get(column, {"width": 130, "minwidth": 80, "stretch": True}) for column in new_columns}
            self.clear()
            self._draw_header()
        if "selectmode" in kwargs:
            self._selectmode = kwargs.pop("selectmode")
        if kwargs:
            super().configure(**kwargs)

    config = configure

    def insert(self, _parent: str, _index: str, values: list | tuple, tags: tuple | list = ()) -> str:
        item_id = f"I{next(self._id_counter):04d}"
        padded = list(values) + [""] * max(0, len(self.columns) - len(values))
        self._items[item_id] = {"values": tuple(padded[: len(self.columns)]), "tags": tuple(tags)}
        self._order.append(item_id)
        self._schedule_draw_rows()
        return item_id

    def delete(self, item_id: str) -> None:
        if item_id in self._items:
            del self._items[item_id]
        if item_id in self._order:
            self._order.remove(item_id)
        if item_id in self._selection:
            self._selection.remove(item_id)
        self._schedule_draw_rows()

    def clear(self) -> None:
        self._items.clear()
        self._order.clear()
        self._selection.clear()
        self._focus = ""
        self._schedule_draw_rows()

    def get_children(self) -> tuple[str, ...]:
        return tuple(self._order)

    def item(self, item_id: str, option: str | None = None):
        item = self._items.get(item_id, {"values": ()})
        if option == "values":
            return item.get("values", ())
        return item

    def selection(self) -> tuple[str, ...]:
        return tuple(self._selection)

    def selection_set(self, item_id: str) -> None:
        if item_id in self._items:
            self._selection = [item_id]
            self._focus = item_id
            self._draw_rows()
            self._emit("<<TreeviewSelect>>")

    def selection_remove(self, item_ids) -> None:
        if isinstance(item_ids, str):
            item_ids = (item_ids,)
        for item_id in item_ids:
            if item_id in self._selection:
                self._selection.remove(item_id)
        self._draw_rows()

    def focus(self, item_id: str | None = None) -> str:
        if item_id is not None:
            self._focus = item_id
        return self._focus

    def see(self, item_id: str) -> None:
        if item_id in self._order and self._order:
            row_index = self._order.index(item_id)
            total_height = max(1, len(self._order) * self._row_height)
            self.canvas.yview_moveto((row_index * self._row_height) / total_height)
            self._draw_rows()

    def bind(self, sequence: str | None = None, func=None, add=None):
        if sequence in {"<<TreeviewSelect>>", "<Double-1>"} and func is not None:
            self._bindings.setdefault(sequence, []).append(func)
            return None
        return super().bind(sequence, func, add)

    def yview(self, *args):
        return self.canvas.yview(*args)

    def tag_configure(self, *_args, **_kwargs) -> None:
        return
