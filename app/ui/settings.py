import tkinter as tk
from tkinter import ttk

from app.database import db
from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import checkbox as ctk_checkbox
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.customtkinter_adapter import style_text_widget
from app.help.preferences import guided_configuration_enabled, learning_mode_enabled, set_guided_configuration, set_learning_mode
from app.ui.shared import section
from app.ui.components.first_run_wizard import FirstRunWizard
from app.ui.components.help_center import HelpCenter
from app.utils.paths import CONFIG_DIR, DATA_DIR, LOG_DIR


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Settings", "Local database, folders, and application configuration.")
    frame.pack(fill="both", expand=True)
    theme = app.theme
    frame.rowconfigure(2, weight=1)
    shell = ctk_frame(frame, theme, "background")
    shell.grid(row=2, column=0, sticky="nsew", padx=theme.spacing.page_padding)
    shell.columnconfigure(0, weight=0, minsize=220)
    shell.columnconfigure(1, weight=1)
    shell.rowconfigure(0, weight=1)

    categories = ctk_frame(shell, theme, "card")
    categories.grid(row=0, column=0, sticky="nsew", padx=(0, theme.spacing.md))
    ctk_label(categories, theme, "Categories", "caption", "card").pack(anchor="w", padx=16, pady=(16, 8))
    for label in ["General Configuration", "Security & Access", "Notification Rules", "Data Management", "Advanced / CLI"]:
        ctk_button(categories, theme, label, command=lambda value=label: app.status.set(value), variant="ghost", width=186, anchor="w").pack(fill="x", padx=12, pady=2)

    content = ctk_frame(shell, theme, "background")
    content.grid(row=0, column=1, sticky="nsew")
    content.columnconfigure(0, weight=1)
    content.rowconfigure(2, weight=1)

    panel = ctk_frame(content, theme, "card")
    panel.grid(row=0, column=0, sticky="ew")
    panel.columnconfigure(1, weight=1)
    ctk_label(panel, theme, "General Configuration", "panel_title", "card").grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 8))
    for idx, (label, path) in enumerate([("Data", DATA_DIR), ("Logs", LOG_DIR), ("Config", CONFIG_DIR)], start=1):
        ctk_label(panel, theme, label, "caption", "card").grid(row=idx, column=0, sticky="w", padx=18, pady=4)
        ctk_label(panel, theme, str(path), "caption", "card").grid(row=idx, column=1, sticky="w", padx=10, pady=4)

    guidance_panel = ctk_frame(content, theme, "card")
    guidance_panel.grid(row=1, column=0, sticky="ew", pady=(14, 0))
    guidance_panel.columnconfigure(1, weight=1)
    header = tk.Canvas(guidance_panel, height=46, highlightthickness=0, bd=0)
    header.grid(row=0, column=0, columnspan=3, sticky="ew")

    def draw_header(_event=None) -> None:
        width = max(header.winfo_width(), 1)
        height = max(header.winfo_height(), 46)
        header.delete("all")
        for x in range(width):
            ratio = x / max(width - 1, 1)
            header.create_line(x, 0, x, height, fill=_blend(theme.palette.info, theme.palette.success, ratio))
        header.create_text(26, height / 2, text="Guidance Preferences", anchor="w", fill=theme.palette.sidebar_text, font=(theme.typography.family_semibold, 14))

    header.bind("<Configure>", draw_header)
    learning_mode = tk.BooleanVar(value=learning_mode_enabled())
    guided_configuration = tk.BooleanVar(value=guided_configuration_enabled())
    ctk_checkbox(guidance_panel, theme, "Learning Mode", learning_mode).grid(row=1, column=0, sticky="w", padx=24, pady=(18, 10))
    ctk_label(
        guidance_panel,
        theme,
        text="When enabled, SafeSend keeps concise page intros, recommendations, warnings, tips, and field guidance available.",
        role="caption",
        variant="card",
        wraplength=640,
    ).grid(row=1, column=1, sticky="w", padx=10, pady=(18, 10))
    ctk_checkbox(guidance_panel, theme, "Show Guided Configuration", guided_configuration).grid(row=2, column=0, sticky="w", padx=24, pady=(0, 18))
    ctk_label(
        guidance_panel,
        theme,
        text="When enabled, SafeSend can show guided recommendations in supporting help surfaces without changing the main page layout.",
        role="caption",
        variant="card",
        wraplength=640,
    ).grid(row=2, column=1, sticky="w", padx=10, pady=(0, 18))

    def save_guidance_preferences() -> None:
        set_learning_mode(learning_mode.get())
        set_guided_configuration(guided_configuration.get())
        app.status.set("Guidance preferences saved.")
        app.navigate("Settings")

    ctk_button(guidance_panel, theme, "Save Guidance", command=save_guidance_preferences, variant="primary", icon="save", width=184).grid(row=1, column=2, rowspan=2, sticky="e", padx=(10, 24), pady=(18, 18))
    footer = ctk_frame(guidance_panel, theme, "surface", corner_radius=0, border_width=0)
    footer.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
    ctk_button(footer, theme, "Open Help Center", command=lambda: HelpCenter(frame), icon="help", width=172).pack(side="left", padx=(24, 8), pady=14)
    ctk_button(footer, theme, "Open First Run Guide", command=lambda: FirstRunWizard(frame), icon="info", width=192).pack(side="left", padx=8, pady=14)

    settings_panel = ctk_frame(content, theme, "card")
    settings_panel.grid(row=2, column=0, sticky="nsew", pady=(14, 0))
    ctk_label(settings_panel, theme, "Stored Settings", "panel_title", "card").pack(anchor="w", padx=18, pady=(18, 8))
    text = tk.Text(settings_panel, height=14, wrap="word")
    style_text_widget(text, theme)
    text.pack(fill="both", expand=True, padx=18, pady=(0, 18))
    rows = db.fetch_all("SELECT key, value, updated_at FROM app_settings ORDER BY key")
    text.insert("1.0", "\n".join(f"{row['key']} = {row['value']} ({row['updated_at']})" for row in rows))
    text.configure(state="disabled")
    content.rowconfigure(2, weight=1)


def _blend(start: str, end: str, ratio: float) -> str:
    sr, sg, sb = _hex_to_rgb(start)
    er, eg, eb = _hex_to_rgb(end)
    return f"#{int(sr + (er - sr) * ratio):02x}{int(sg + (eg - sg) * ratio):02x}{int(sb + (eb - sb) * ratio):02x}"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)
