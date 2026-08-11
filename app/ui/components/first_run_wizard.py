import tkinter as tk

from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.customtkinter_adapter import toplevel

from app.design_system.theme import active_theme


STEPS = [
    ("Add SMTP", "Create an SMTP profile, test the connection, and check reputation before using it."),
    ("Import Contacts", "Create a contact list and import a CSV with clean field mapping."),
    ("Verify Contacts", "Verify recipients and treat Risky or Unknown contacts conservatively."),
    ("Review Recipient Infrastructure", "Use clustering and MX/provider awareness to avoid concentrated sending bursts."),
    ("Build Campaign", "Choose a contact list, template, SMTP profile, and internal notes."),
    ("Configure Sending Rules", "Use conservative pacing, quiet hours, and daily/hourly caps."),
    ("Send", "Build and review the queue before enabling any future sending workflow."),
    ("Review Reports", "Use failures, suppressions, and status trends to improve the next send."),
]


class FirstRunWizard:
    def __init__(self, parent: tk.Widget) -> None:
        self.theme = active_theme()
        self.window = toplevel(parent, "SafeSend First Run Guide", "800x620")
        body = ctk_frame(self.window, self.theme, "background")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        ctk_label(body, self.theme, "First Run Guide", role="page_title").grid(row=0, column=0, sticky="w", padx=self.theme.spacing.page_padding, pady=(self.theme.spacing.page_padding, 0))
        ctk_label(
            body,
            self.theme,
            text="Follow these steps to configure SafeSend safely and understand why each step matters.",
            role="caption",
            wraplength=680,
        ).grid(row=1, column=0, sticky="w", pady=(self.theme.spacing.xs, self.theme.spacing.lg))
        for idx, (title, body_text) in enumerate(STEPS, start=1):
            row = ctk_frame(body, self.theme, "card")
            row.grid(row=idx + 1, column=0, sticky="ew", padx=self.theme.spacing.page_padding, pady=(0, self.theme.spacing.sm))
            ctk_label(row, self.theme, f"{idx}. {title}", role="panel_title", variant="card").pack(anchor="w", padx=self.theme.spacing.md, pady=(self.theme.spacing.md, 0))
            ctk_label(row, self.theme, body_text, role="caption", variant="card", wraplength=650, justify="left").pack(anchor="w", padx=self.theme.spacing.md, pady=(self.theme.spacing.xs, self.theme.spacing.md))
