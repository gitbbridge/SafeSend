import tkinter as tk

from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.customtkinter_adapter import textbox as ctk_textbox
from app.design_system.customtkinter_adapter import toplevel
from app.help.search_index import search_help
from app.design_system.theme import active_theme


class HelpCenter:
    def __init__(self, parent: tk.Widget) -> None:
        self.theme = active_theme()
        self.window = toplevel(parent, "SafeSend Help Center", "820x600")
        self.query = tk.StringVar()
        body = ctk_frame(self.window, self.theme, "background")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(2, weight=1)
        ctk_label(body, self.theme, "Help Center", role="page_title").grid(row=0, column=0, sticky="w", padx=self.theme.spacing.page_padding, pady=(self.theme.spacing.page_padding, 0))
        search = ctk_entry(body, self.theme, self.query, placeholder_text="Search SMTP, warm-up, queue, reports, suppression...")
        search.grid(row=1, column=0, sticky="ew", padx=self.theme.spacing.page_padding, pady=(self.theme.spacing.md, self.theme.spacing.md))
        search.bind("<KeyRelease>", lambda _event: self.refresh())
        self.results = ctk_textbox(
            body,
            self.theme,
            wrap="word",
            placeholder_text="Search results appear here.",
        )
        self.results.grid(row=2, column=0, sticky="nsew", padx=self.theme.spacing.page_padding, pady=(0, self.theme.spacing.page_padding))
        self.refresh()

    def refresh(self) -> None:
        rows = search_help(self.query.get())
        self.results.configure(state="normal")
        self.results.delete("1.0", "end")
        if not rows:
            self.results.insert("1.0", "No help topics matched your search.")
        else:
            self.results.insert("1.0", "\n\n".join(f"{title}\n{body}" for title, body in rows))
        self.results.configure(state="disabled")
