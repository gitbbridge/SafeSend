import tkinter as tk
from tkinter import ttk


def clear_frame(frame: tk.Widget) -> None:
    for child in frame.winfo_children():
        child.destroy()


def section(parent: tk.Widget, title: str, subtitle: str = "") -> ttk.Frame:
    frame = ttk.Frame(parent, padding=18)
    frame.columnconfigure(0, weight=1)
    ttk.Label(frame, text=title, style="Title.TLabel").grid(row=0, column=0, sticky="w")
    if subtitle:
        ttk.Label(frame, text=subtitle, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 14))
    else:
        ttk.Separator(frame).grid(row=1, column=0, sticky="ew", pady=(8, 14))
    return frame


def labeled_entry(parent: tk.Widget, label: str, row: int, column: int = 0, width: int = 28, show: str = "") -> tk.StringVar:
    var = tk.StringVar()
    ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, 8), pady=5)
    ttk.Entry(parent, textvariable=var, width=width, show=show).grid(row=row, column=column + 1, sticky="ew", pady=5)
    return var


def labeled_combo(parent: tk.Widget, label: str, row: int, values: list[str], column: int = 0) -> tk.StringVar:
    var = tk.StringVar(value=values[0] if values else "")
    ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, 8), pady=5)
    ttk.Combobox(parent, textvariable=var, values=values, state="readonly").grid(row=row, column=column + 1, sticky="ew", pady=5)
    return var


def build_tree(parent: tk.Widget, columns: tuple[str, ...], headings: tuple[str, ...] | None = None, height: int = 12) -> ttk.Treeview:
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=height)
    labels = headings or columns
    for column, heading in zip(columns, labels):
        tree.heading(column, text=heading)
        tree.column(column, width=130, minwidth=80, stretch=True)
    tree.grid(row=0, column=0, sticky="nsew")
    scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    scroll.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scroll.set)
    parent.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)
    return tree


def fill_tree(tree: ttk.Treeview, rows: list[dict], columns: tuple[str, ...]) -> None:
    for item in tree.get_children():
        tree.delete(item)
    for row in rows:
        tree.insert("", "end", values=[row.get(column, "") for column in columns])


class StatusBar(ttk.Label):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, text="Ready", style="Muted.TLabel", anchor="w")

    def set(self, message: str) -> None:
        self.configure(text=message)
