import tkinter as tk
from tkinter import messagebox, ttk

from app.models.smtp_profile import SMTPProfile
from app.services.smtp_service import SECURITY_TYPES
from app.ui.shared import build_tree, section


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
    frame.columnconfigure(0, weight=3)
    frame.columnconfigure(1, weight=2)
    frame.rowconfigure(4, weight=1)

    selected_id = tk.IntVar(value=0)
    fields = _make_form_vars()

    form = ttk.Frame(frame, padding=14, style="Card.TFrame")
    form.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(0, 12))
    _build_form(form, fields)

    health = ttk.Frame(frame, padding=14, style="Card.TFrame")
    health.grid(row=2, column=1, sticky="nsew", pady=(0, 12))
    health_labels = _build_health_panel(health)

    actions = ttk.Frame(frame)
    actions.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
    ttk.Button(actions, text="New", command=lambda: clear_form()).pack(side="left")
    ttk.Button(actions, text="Save Profile", command=lambda: save_profile()).pack(side="left", padx=6)
    ttk.Button(actions, text="Cancel Edit", command=lambda: clear_form()).pack(side="left", padx=6)
    ttk.Button(actions, text="Duplicate", command=lambda: duplicate_profile()).pack(side="left", padx=6)
    ttk.Button(actions, text="Delete", command=lambda: delete_profile()).pack(side="left", padx=6)
    ttk.Button(actions, text="Test Connection", command=lambda: test_connection()).pack(side="left", padx=(22, 6))
    ttk.Button(actions, text="Check Reputation", command=lambda: check_reputation()).pack(side="left", padx=6)

    table_frame = ttk.Frame(frame)
    table_frame.grid(row=4, column=0, columnspan=2, sticky="nsew")
    tree = build_tree(
        table_frame,
        TABLE_COLUMNS,
        headings=(
            "#",
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
        height=10,
    )
    tree.column("id", width=42, minwidth=42, stretch=False)
    tree.column("port", width=65, minwidth=65, stretch=False)
    tree.column("enabled_label", width=75, minwidth=75, stretch=False)
    tree.column("daily_limit", width=70, minwidth=70, stretch=False)
    tree.column("hourly_limit", width=70, minwidth=70, stretch=False)

    reputation = ttk.Frame(frame, padding=(0, 12, 0, 0))
    reputation.grid(row=5, column=0, columnspan=2, sticky="nsew")
    reputation.columnconfigure(0, weight=1)
    ttk.Label(reputation, text="Reputation / Blacklist Results", style="Muted.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 6))
    reputation_tree = build_tree(
        reputation,
        ("zone", "listed_label", "query", "response", "error_message", "checked_at"),
        headings=("Zone", "Status", "DNSBL Query", "Response", "Error", "Checked"),
        height=6,
    )

    def refresh(select_id: int | None = None) -> None:
        profiles = [_display_profile(row) for row in app.smtp_service.list_profiles()]
        for item in tree.get_children():
            tree.delete(item)
        for row in profiles:
            item_id = tree.insert("", "end", values=[row.get(column, "") for column in TABLE_COLUMNS])
            if select_id and row["id"] == select_id:
                tree.selection_set(item_id)
                tree.focus(item_id)
                tree.see(item_id)
        if select_id:
            load_profile(select_id)

    def selected_profile_id() -> int:
        if selected_id.get():
            return selected_id.get()
        selection = tree.selection()
        if not selection:
            return 0
        values = tree.item(selection[0], "values")
        return int(values[0]) if values else 0

    def load_selected(_event=None) -> None:
        selection = tree.selection()
        if not selection:
            return
        values = tree.item(selection[0], "values")
        if values:
            load_profile(int(values[0]))

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
        load_reputation(profile_id)
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
        _clear_tree(reputation_tree)
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
        app.status.set("Testing SMTP connection...")
        frame.update_idletasks()
        ok, message, _resolved = app.smtp_service.test_connection(profile_id)
        refresh(profile_id)
        title = "Connection succeeded" if ok else "Connection failed"
        if ok:
            messagebox.showinfo(title, message)
        else:
            messagebox.showerror(title, message)

    def check_reputation() -> None:
        profile_id = selected_profile_id()
        if not profile_id:
            messagebox.showinfo("Check reputation", "Select a profile before checking reputation.")
            return
        app.status.set("Checking blacklist reputation...")
        frame.update_idletasks()
        try:
            summary = app.blacklist_service.check_profile(profile_id)
            refresh(profile_id)
            load_reputation(profile_id)
            messagebox.showinfo(
                "Reputation check complete",
                f"IP {summary['ip']} checked across {len(summary['results'])} zones. Listed: {summary['listed_count']}.",
            )
        except Exception as exc:
            messagebox.showerror("Reputation check", str(exc))
        finally:
            app.status.set("SMTP reputation check finished.")

    def load_reputation(profile_id: int) -> None:
        rows = []
        for row in app.smtp_service.blacklist_results(profile_id):
            item = dict(row)
            item["listed_label"] = "Listed" if item.get("listed") else "Clean"
            rows.append(item)
        _clear_tree(reputation_tree)
        for row in rows:
            reputation_tree.insert(
                "",
                "end",
                values=[row.get(column, "") for column in ("zone", "listed_label", "query", "response", "error_message", "checked_at")],
            )

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


def _build_form(parent: ttk.Frame, fields: dict[str, tk.Variable]) -> None:
    for col in (1, 3):
        parent.columnconfigure(col, weight=1)
    ttk.Label(parent, text="Profile Details", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
    _entry(parent, "Profile name", fields["profile_name"], 1, 0)
    _entry(parent, "SMTP host", fields["host"], 2, 0)
    _entry(parent, "SMTP port", fields["port"], 3, 0)
    _combo(parent, "Security", fields["security_mode"], SECURITY_TYPES, 4, 0)
    _entry(parent, "Username", fields["username"], 1, 2)
    _entry(parent, "Password", fields["password"], 2, 2, show="*")
    _entry(parent, "From name", fields["from_name"], 3, 2)
    _entry(parent, "From email", fields["from_email"], 4, 2)
    _entry(parent, "Reply-to email", fields["reply_to_email"], 5, 2)
    _entry(parent, "Daily limit", fields["daily_limit"], 5, 0)
    _entry(parent, "Hourly limit", fields["hourly_limit"], 6, 0)
    _entry(parent, "Max connections", fields["max_connections"], 6, 2)
    ttk.Checkbutton(parent, text="Enabled", variable=fields["enabled"]).grid(row=7, column=1, sticky="w", pady=(8, 0))
    _entry(parent, "Notes/internal label", fields["notes"], 7, 2)


def _build_health_panel(parent: ttk.Frame) -> dict[str, ttk.Label]:
    parent.columnconfigure(1, weight=1)
    ttk.Label(parent, text="SMTP Health", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    labels: dict[str, ttk.Label] = {}
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
        ttk.Label(parent, text=text, style="CardMuted.TLabel").grid(row=idx, column=0, sticky="nw", pady=3)
        value = ttk.Label(parent, text="-", style="PanelTitle.TLabel", wraplength=360, justify="left")
        value.grid(row=idx, column=1, sticky="w", padx=(10, 0), pady=3)
        labels[key] = value
    return labels


def _entry(parent: ttk.Frame, label: str, variable: tk.Variable, row: int, column: int, show: str = "") -> None:
    ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, 8), pady=5)
    ttk.Entry(parent, textvariable=variable, show=show).grid(row=row, column=column + 1, sticky="ew", pady=5)


def _combo(parent: ttk.Frame, label: str, variable: tk.Variable, values: tuple[str, ...], row: int, column: int) -> None:
    ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=(0, 8), pady=5)
    ttk.Combobox(parent, textvariable=variable, values=values, state="readonly").grid(row=row, column=column + 1, sticky="ew", pady=5)


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


def _update_health(labels: dict[str, ttk.Label], profile: dict | None) -> None:
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
