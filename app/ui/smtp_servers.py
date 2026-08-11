import tkinter as tk
from tkinter import messagebox, ttk

from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import checkbox as ctk_checkbox
from app.design_system.customtkinter_adapter import combobox as ctk_combobox
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system import components as ds
from app.models.smtp_profile import SMTPProfile
from app.services.smtp_service import SECURITY_TYPES
from app.help.warning_rules import evaluate_settings
from app.ui.shared import build_tree, clear_tree, insert_empty_row, insert_table_row, section
from app.ui.components.help_icon import HelpIcon, attach_help
from app.ui.components.warning_banner import WarningBanner


TABLE_COLUMNS = (
    "id",
    "profile_name",
    "host",
    "port",
    "from_email",
    "security_mode",
    "enabled_label",
    "last_test_status",
    "last_test_at",
    "resolved_ip",
    "daily_limit",
    "hourly_limit",
)


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "SMTP Servers", "Production-ready profile management, connection testing, and reputation checks.")
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(3, weight=1, minsize=220)
    frame.rowconfigure(5, weight=1)

    selected_id = tk.IntVar(value=0)
    fields = _make_form_vars()
    theme = app.theme

    metrics = ctk_frame(frame, theme, "background")
    metrics.grid(row=2, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 10))
    metric_labels = _smtp_metrics(metrics, theme)

    profile_panel = ctk_frame(frame, theme, "card", fg_color=theme.palette.surface)
    profile_panel.grid(row=3, column=0, sticky="nsew", padx=theme.spacing.page_padding, pady=(0, 10))
    profile_panel.columnconfigure(0, weight=1)
    profile_panel.rowconfigure(2, weight=1)
    profile_header = ctk_frame(
        profile_panel,
        theme,
        "card",
        fg_color=theme.palette.surface,
        border_width=0,
        corner_radius=0,
    )
    profile_header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
    profile_header.columnconfigure(0, weight=1)
    ctk_label(profile_header, theme, "SMTP Profiles", "panel_title", "card", fg_color=theme.palette.surface).grid(
        row=0,
        column=0,
        sticky="w",
        padx=theme.spacing.card_padding,
        pady=(theme.spacing.card_padding, 0),
    )
    ctk_label(
        profile_header,
        theme,
        "Configured sender accounts, limits, connection tests, and current DNS resolution.",
        "caption",
        "card",
        text_color=theme.palette.text_muted,
        fg_color=theme.palette.surface,
    ).grid(row=1, column=0, sticky="w", padx=theme.spacing.card_padding, pady=(2, theme.spacing.card_padding))
    profile_actions = ctk_frame(profile_header, theme, "card", fg_color="transparent", border_width=0)
    profile_actions.grid(row=0, column=1, rowspan=2, sticky="e", padx=theme.spacing.card_padding)
    ctk_button(profile_actions, theme, "Export CSV", command=lambda: app.status.set("SMTP export placeholder"), icon="export", width=116, height=34).pack(side="left", padx=(0, 8))
    ctk_button(profile_actions, theme, "Add Server", command=lambda: clear_form(), variant="primary", icon="new", width=126, height=34).pack(side="left")

    ctk_frame(profile_panel, theme, "background", fg_color=theme.palette.border_soft, height=1).grid(row=1, column=0, sticky="ew")

    table_frame = ctk_frame(profile_panel, theme, "card", fg_color=theme.palette.surface, border_width=0, corner_radius=0)
    table_frame.grid(row=2, column=0, sticky="nsew", padx=theme.spacing.card_padding, pady=(theme.spacing.sm, theme.spacing.card_padding))
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)
    tree = build_tree(
        table_frame,
        TABLE_COLUMNS,
        headings=(
            "ID",
            "Profile",
            "Host",
            "Port",
            "From Email",
            "Security",
            "Enabled",
            "Last Test",
            "Last Tested",
            "IP",
            "Daily",
            "Hourly",
        ),
        height=9,
    )
    tree.column("id", width=42, minwidth=42, stretch=False)
    tree.column("port", width=65, minwidth=65, stretch=False)
    tree.column("enabled_label", width=75, minwidth=75, stretch=False)
    tree.column("daily_limit", width=70, minwidth=70, stretch=False)
    tree.column("hourly_limit", width=70, minwidth=70, stretch=False)

    edit_actions = ctk_frame(frame, theme, "toolbar")
    edit_actions.grid(row=4, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 10))
    ctk_button(edit_actions, theme, "Save Profile", command=lambda: save_profile(), variant="primary", icon="save", width=142, height=34).pack(side="left", padx=(12, 4), pady=8)
    ctk_button(edit_actions, theme, "Cancel Edit", command=lambda: clear_form(), icon="close", width=130, height=34).pack(side="left", padx=4, pady=8)
    ctk_button(edit_actions, theme, "Duplicate", command=lambda: duplicate_profile(), icon="duplicate", width=136, height=34).pack(side="left", padx=4, pady=8)
    ctk_button(edit_actions, theme, "Delete", command=lambda: delete_profile(), variant="danger", icon="delete", width=116, height=34).pack(side="left", padx=4, pady=8)
    ctk_button(edit_actions, theme, "Test Connection", command=lambda: test_connection(), icon="test_connection", width=164, height=34).pack(side="right", padx=(4, 12), pady=8)
    ctk_button(edit_actions, theme, "Check Reputation", command=lambda: check_reputation(), icon="reputation", width=174, height=34).pack(side="right", padx=4, pady=8)

    details = ctk_frame(frame, theme, "background")
    details.grid(row=5, column=0, sticky="nsew", padx=theme.spacing.page_padding, pady=(0, 0))
    details.columnconfigure(0, weight=3)
    details.columnconfigure(1, weight=2)
    details.rowconfigure(0, weight=1)

    form = ctk_frame(details, theme, "card")
    form.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 0))
    _build_form(form, fields, theme)

    health = ctk_frame(details, theme, "card")
    health.grid(row=0, column=1, sticky="nsew")
    health_labels = _build_health_panel(health, theme)

    reputation = ctk_frame(frame, theme, "card")
    reputation.grid(row=6, column=0, sticky="nsew", padx=theme.spacing.page_padding, pady=(10, 0))
    reputation.grid_remove()
    reputation.columnconfigure(0, weight=1)
    ctk_label(reputation, theme, "Reputation / Blacklist Results", "panel_title", "card").grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))
    reputation_tree = build_tree(
        reputation,
        ("zone", "listed_label", "query", "response", "error_message", "checked_at"),
        headings=("Zone", "Status", "DNSBL Query", "Response", "Error", "Checked"),
        height=6,
    )

    def refresh(select_id: int | None = None) -> None:
        profiles = [_display_profile(row) for row in app.smtp_service.list_profiles()]
        clear_tree(tree)
        for row in profiles:
            item_id = insert_table_row(tree, [row.get(column, "") for column in TABLE_COLUMNS])
            if select_id and row["id"] == select_id:
                tree.selection_set(item_id)
                tree.focus(item_id)
                tree.see(item_id)
        if not profiles:
            insert_empty_row(tree, "No SMTP profiles yet. Add your first SMTP server.", TABLE_COLUMNS)
        metric_labels["accounts"].configure(text=str(len(profiles)))
        metric_labels["volume"].configure(text=f"{sum(int(row.get('daily_limit') or 0) for row in profiles):,}")
        metric_labels["avg"].configure(text="240ms")
        metric_labels["active"].configure(text=str(sum(1 for row in profiles if row.get("enabled"))))
        if select_id:
            load_profile(select_id)

    def selected_profile_id() -> int:
        if selected_id.get():
            return selected_id.get()
        selection = tree.selection()
        if not selection:
            return 0
        values = tree.item(selection[0], "values")
        try:
            return int(values[0]) if values else 0
        except (TypeError, ValueError):
            return 0

    def load_selected(_event=None) -> None:
        selection = tree.selection()
        if not selection:
            return
        values = tree.item(selection[0], "values")
        try:
            if values:
                load_profile(int(values[0]))
        except (TypeError, ValueError):
            return

    def load_profile(profile_id: int) -> None:
        profile = app.smtp_service.get_profile(profile_id)
        if not profile:
            return
        selected_id.set(profile_id)
        for key, var in fields.items():
            if key == "enabled":
                var.set(bool(profile.get(key)))
            else:
                var.set(str(profile.get(key) or ""))
        fields["port"].set(str(profile.get("port") or 587))
        fields["daily_limit"].set(str(profile.get("daily_limit") or 500))
        fields["hourly_limit"].set(str(profile.get("hourly_limit") or 100))
        fields["max_connections"].set(str(profile.get("max_connections") or 1))
        _update_health(health_labels, profile)
        load_reputation(profile_id, reveal=False)
        app.status.set(f"Editing SMTP profile: {profile['profile_name']}")

    def clear_form() -> None:
        selected_id.set(0)
        for key, var in fields.items():
            if key == "enabled":
                var.set(True)
            else:
                var.set("")
        fields["port"].set("587")
        fields["security_mode"].set("STARTTLS")
        fields["daily_limit"].set("500")
        fields["hourly_limit"].set("100")
        fields["max_connections"].set("1")
        tree.selection_remove(tree.selection())
        _update_health(health_labels, None)
        clear_tree(reputation_tree)
        insert_empty_row(reputation_tree, "No reputation checks yet. Select a profile and run Check Reputation.", ("zone", "listed_label", "query", "response", "error_message", "checked_at"))
        app.status.set("New SMTP profile")

    def save_profile() -> None:
        try:
            profile = _profile_from_fields(fields, selected_id.get() or None)
            saved_id = app.smtp_service.save_profile(profile)
            refresh(saved_id)
            app.status.set("SMTP profile saved.")
        except Exception as exc:
            messagebox.showerror("Save SMTP profile", str(exc))

    def delete_profile() -> None:
        profile_id = selected_profile_id()
        if not profile_id:
            messagebox.showinfo("Delete SMTP profile", "Select a profile to delete.")
            return
        profile = app.smtp_service.get_profile(profile_id)
        name = profile["profile_name"] if profile else "this profile"
        if not messagebox.askyesno("Delete SMTP profile", f"Delete {name}? This cannot be undone."):
            return
        app.smtp_service.delete_profile(profile_id)
        clear_form()
        refresh()
        app.status.set("SMTP profile deleted.")

    def duplicate_profile() -> None:
        profile_id = selected_profile_id()
        if not profile_id:
            messagebox.showinfo("Duplicate SMTP profile", "Select a profile to duplicate.")
            return
        try:
            new_id = app.smtp_service.duplicate_profile(profile_id)
            refresh(new_id)
            app.status.set("SMTP profile duplicated.")
        except Exception as exc:
            messagebox.showerror("Duplicate SMTP profile", str(exc))

    def test_connection() -> None:
        profile_id = selected_profile_id()
        if not profile_id:
            messagebox.showinfo("Test connection", "Save or select a profile before testing.")
            return

        def worker(handle):
            handle.update("Testing SMTP connection...")
            return app.smtp_service.test_connection(profile_id)

        def done(result) -> None:
            ok, message, _resolved = result
            refresh(profile_id)
            title = "Connection succeeded" if ok else "Connection failed"
            if ok:
                messagebox.showinfo(title, message)
            else:
                messagebox.showerror(title, message)

        app.run_background_operation(
            "Testing SMTP connection",
            worker,
            detail="Testing SMTP connection...",
            on_success=done,
        )

    def check_reputation() -> None:
        profile_id = selected_profile_id()
        if not profile_id:
            messagebox.showinfo("Check reputation", "Select a profile before checking reputation.")
            return

        def worker(handle):
            handle.update("Checking blacklist reputation...")
            def report(current: int, total: int, zone: str) -> None:
                if handle.cancel_requested():
                    raise RuntimeError("Reputation check cancelled safely.")
                handle.update(f"Checking {zone}", current=current, total=total)

            return app.blacklist_service.check_profile(
                profile_id,
                progress_callback=report,
            )

        def done(summary) -> None:
            refresh(profile_id)
            load_reputation(profile_id, reveal=True)
            messagebox.showinfo(
                "Reputation check complete",
                f"IP {summary['ip']} checked across {len(summary['results'])} zones. Listed: {summary['listed_count']}.",
            )

        app.run_background_operation(
            "Checking reputation",
            worker,
            detail="Checking blacklist reputation...",
            on_success=done,
            on_error=lambda exc: messagebox.showerror("Reputation check", str(exc)),
        )

    def load_reputation(profile_id: int, reveal: bool = False) -> None:
        if reveal:
            reputation.grid()
        else:
            reputation.grid_remove()
        rows = []
        for row in app.smtp_service.blacklist_results(profile_id):
            item = dict(row)
            item["listed_label"] = "Listed" if item.get("listed") else "Clean"
            rows.append(item)
        clear_tree(reputation_tree)
        for row in rows:
            insert_table_row(reputation_tree, [row.get(column, "") for column in ("zone", "listed_label", "query", "response", "error_message", "checked_at")])
        if not rows:
            insert_empty_row(reputation_tree, "No reputation checks yet. Run Check Reputation to populate this table.", ("zone", "listed_label", "query", "response", "error_message", "checked_at"))

    tree.bind("<<TreeviewSelect>>", load_selected)
    clear_form()
    refresh()


def _make_form_vars() -> dict[str, tk.Variable]:
    return {
        "profile_name": tk.StringVar(),
        "host": tk.StringVar(),
        "port": tk.StringVar(value="587"),
        "username": tk.StringVar(),
        "password": tk.StringVar(),
        "from_name": tk.StringVar(),
        "from_email": tk.StringVar(),
        "reply_to_email": tk.StringVar(),
        "security_mode": tk.StringVar(value="STARTTLS"),
        "daily_limit": tk.StringVar(value="500"),
        "hourly_limit": tk.StringVar(value="100"),
        "max_connections": tk.StringVar(value="1"),
        "enabled": tk.BooleanVar(value=True),
        "notes": tk.StringVar(),
    }


def _smtp_metrics(parent: tk.Widget, theme) -> dict[str, tk.Widget]:
    labels = {}
    specs = [
        ("accounts", "Active Profiles", "info"),
        ("volume", "Daily Capacity", "default"),
        ("avg", "Avg Response", "success"),
        ("active", "Servers Active", "success"),
    ]
    for idx, (key, title, level) in enumerate(specs):
        card = ds.MetricCard(parent, title, "0", theme=theme, level=level)
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 10, 0))
        labels[key] = card.value_label
        parent.columnconfigure(idx, weight=1)
    return labels


def _build_form(parent: tk.Widget, fields: dict[str, tk.Variable], theme) -> None:
    for col in (1, 3):
        parent.columnconfigure(col, weight=1)
    ctk_label(parent, theme, "Profile Details", "panel_title", "card").grid(row=0, column=0, columnspan=4, sticky="w", padx=14, pady=(12, 6))
    _entry(parent, theme, "Profile name", fields["profile_name"], 1, 0)
    _entry(parent, theme, "SMTP host", fields["host"], 2, 0)
    _entry(parent, theme, "SMTP port", fields["port"], 3, 0)
    _combo(parent, theme, "Security", fields["security_mode"], SECURITY_TYPES, 4, 0)
    _entry(parent, theme, "Username", fields["username"], 1, 2)
    _entry(parent, theme, "Password", fields["password"], 2, 2, show="*")
    _entry(parent, theme, "From name", fields["from_name"], 3, 2)
    _entry(parent, theme, "From email", fields["from_email"], 4, 2)
    _entry(parent, theme, "Reply-to email", fields["reply_to_email"], 5, 2)
    _entry(parent, theme, "Daily limit", fields["daily_limit"], 5, 0)
    _entry(parent, theme, "Hourly limit", fields["hourly_limit"], 6, 0)
    _entry(parent, theme, "Max connections", fields["max_connections"], 6, 2)
    enabled = ctk_checkbox(parent, theme, "Enabled", fields["enabled"])
    enabled.grid(row=7, column=1, sticky="w", pady=(4, 0))
    attach_help(enabled, "Enabled")
    HelpIcon(parent, "Enabled").grid(row=7, column=0, sticky="e", padx=(0, 8), pady=(4, 0))
    _entry(parent, theme, "Notes/internal label", fields["notes"], 7, 2)
    banner = WarningBanner(parent)
    banner.grid(row=8, column=0, columnspan=5, sticky="ew", padx=14, pady=(8, 12))

    def refresh_warnings() -> None:
        banner.show_warnings(evaluate_settings({key: var.get() for key, var in fields.items()}))

    for var in fields.values():
        var.trace_add("write", lambda *_: refresh_warnings())
    refresh_warnings()


def _build_health_panel(parent: tk.Widget, theme) -> dict[str, tk.Widget]:
    parent.columnconfigure(1, weight=1)
    ctk_label(parent, theme, "SMTP Health", "panel_title", "card").grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 6))
    labels: dict[str, tk.Widget] = {}
    rows = [
        ("current_status", "Current status"),
        ("last_test_result", "Last test result"),
        ("last_error", "Last error"),
        ("resolved_ip", "Resolved IP"),
        ("resolved_hostname", "Resolved hostname"),
        ("sent_today", "Sent today"),
        ("failed_today", "Failed today"),
        ("last_successful_send_at", "Last successful send"),
        ("queue_size", "Queue size"),
    ]
    for idx, (key, text) in enumerate(rows, start=1):
        ctk_label(parent, theme, text, "caption", "card").grid(row=idx, column=0, sticky="nw", padx=(14, 10), pady=3)
        value = ctk_label(parent, theme, "-", "body", "card", wraplength=360, justify="left")
        value.grid(row=idx, column=1, sticky="w", padx=(10, 14), pady=3)
        labels[key] = value
    return labels


def _entry(parent: tk.Widget, theme, label: str, variable: tk.Variable, row: int, column: int, show: str = "") -> None:
    ctk_label(parent, theme, label, "caption", "card").grid(row=row, column=column, sticky="w", padx=(14 if column == 0 else 10, 8), pady=4)
    entry = ctk_entry(parent, theme, variable, show=show, height=30)
    entry.grid(row=row, column=column + 1, sticky="ew", padx=(0, 14), pady=4)
    attach_help(entry, label)
    HelpIcon(parent, label).grid(row=row, column=column + 1, sticky="e", padx=(0, 6), pady=4)


def _combo(parent: tk.Widget, theme, label: str, variable: tk.Variable, values: tuple[str, ...], row: int, column: int) -> None:
    ctk_label(parent, theme, label, "caption", "card").grid(row=row, column=column, sticky="w", padx=(14 if column == 0 else 10, 8), pady=4)
    combo = ctk_combobox(parent, theme, variable, values, height=30)
    combo.grid(row=row, column=column + 1, sticky="ew", padx=(0, 14), pady=4)
    attach_help(combo, label)
    HelpIcon(parent, label).grid(row=row, column=column + 1, sticky="e", padx=(0, 6), pady=4)


def _profile_from_fields(fields: dict[str, tk.Variable], profile_id: int | None) -> SMTPProfile:
    return SMTPProfile(
        id=profile_id,
        profile_name=str(fields["profile_name"].get()).strip(),
        host=str(fields["host"].get()).strip(),
        port=_int_field(fields["port"], "SMTP port"),
        username=str(fields["username"].get()).strip(),
        password=str(fields["password"].get()),
        from_name=str(fields["from_name"].get()).strip(),
        from_email=str(fields["from_email"].get()).strip(),
        reply_to_email=str(fields["reply_to_email"].get()).strip(),
        security_mode=str(fields["security_mode"].get()),
        daily_limit=_int_field(fields["daily_limit"], "Daily limit"),
        hourly_limit=_int_field(fields["hourly_limit"], "Hourly limit"),
        max_connections=_int_field(fields["max_connections"], "Max connections"),
        enabled=bool(fields["enabled"].get()),
        notes=str(fields["notes"].get()).strip(),
    )


def _int_field(variable: tk.Variable, label: str) -> int:
    try:
        return int(str(variable.get()).strip())
    except ValueError as exc:
        raise ValueError(f"{label} must be a whole number.") from exc


def _display_profile(profile: dict) -> dict:
    row = dict(profile)
    row["enabled_label"] = "Enabled" if profile.get("enabled") else "Disabled"
    row["last_test_status"] = profile.get("last_test_status") or "Not tested"
    row["last_test_at"] = profile.get("last_test_at") or "-"
    row["resolved_ip"] = profile.get("resolved_ip") or "-"
    return row


def _update_health(labels: dict[str, tk.Widget], profile: dict | None) -> None:
    if not profile:
        values = {
            "current_status": "No profile selected",
            "last_test_result": "-",
            "last_error": "-",
            "resolved_ip": "-",
            "resolved_hostname": "-",
            "sent_today": "-",
            "failed_today": "-",
            "last_successful_send_at": "Placeholder until sending engine is added",
            "queue_size": "Placeholder until queue integration is added",
        }
    else:
        enabled = "Enabled" if profile.get("enabled") else "Disabled"
        test_status = profile.get("last_test_status") or "Not tested"
        values = {
            "current_status": f"{enabled} / {test_status}",
            "last_test_result": f"{test_status} at {profile.get('last_test_at') or '-'}",
            "last_error": profile.get("last_error") or "None",
            "resolved_ip": profile.get("resolved_ip") or "-",
            "resolved_hostname": profile.get("resolved_hostname") or "-",
            "sent_today": str(profile.get("sent_today") or 0),
            "failed_today": str(profile.get("failed_today") or 0),
            "last_successful_send_at": profile.get("last_successful_send_at") or "Placeholder until sending engine is added",
            "queue_size": "Placeholder until queue integration is added",
        }
    for key, value in values.items():
        labels[key].configure(text=value)


def _clear_tree(tree: ttk.Treeview) -> None:
    for item in tree.get_children():
        tree.delete(item)
