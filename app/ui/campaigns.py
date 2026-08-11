import random
import re
import tkinter as tk
from tkinter import messagebox, ttk

from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import combobox as ctk_combobox
from app.design_system.customtkinter_adapter import entry as ctk_entry
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.customtkinter_adapter import style_text_widget
from app.design_system.customtkinter_adapter import toplevel as ctk_toplevel
from app.design_system import components as ds
from app.ui.shared import build_tree, clear_tree, icon_text, insert_empty_row, insert_table_row, section

DASHBOARD_COLUMNS = (
    "id",
    "name",
    "status",
    "created_at",
    "updated_at",
    "smtp_profile_name",
    "template_name",
    "list_name",
    "recipient_count",
)


def build(parent: tk.Widget, app) -> None:
    frame = section(parent, "Campaigns", "Campaign Builder & Preflight System")
    frame.pack(fill="both", expand=True)
    frame.rowconfigure(4, weight=1)
    frame.columnconfigure(0, weight=1)

    search = tk.StringVar()
    theme = app.theme
    toolbar = ctk_frame(frame, theme, "background")
    toolbar.grid(row=2, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 10))
    toolbar.columnconfigure(1, weight=1)
    ctk_button(toolbar, theme, icon_text("new", "New Campaign"), command=lambda: open_wizard(), variant="primary", width=154).grid(row=0, column=0, padx=(0, 8), pady=4)
    ctk_entry(toolbar, theme, search, placeholder_text="Search campaigns").grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=12)
    ctk_button(toolbar, theme, "Filter", command=lambda: refresh(), width=78).grid(row=0, column=2, padx=3, pady=4)
    ctk_button(toolbar, theme, "Edit", command=lambda: edit_selected(), icon="edit", width=76).grid(row=0, column=3, padx=3, pady=4)
    ctk_button(toolbar, theme, "Copy", command=lambda: duplicate_selected(), icon="duplicate", width=78).grid(row=0, column=4, padx=3, pady=4)
    ctk_button(toolbar, theme, "Arc", command=lambda: archive_selected(), icon="archive", width=72).grid(row=0, column=5, padx=3, pady=4)
    ctk_button(toolbar, theme, "Del", command=lambda: delete_selected(), variant="danger", icon="delete", width=72).grid(row=0, column=6, padx=3, pady=4)
    ctk_button(toolbar, theme, "Export", command=lambda: app.status.set("Campaign export placeholder"), icon="export", width=88).grid(row=0, column=7, padx=(3, 0), pady=4)

    stats = ctk_frame(frame, theme, "background")
    stats.grid(row=3, column=0, sticky="ew", padx=theme.spacing.page_padding, pady=(0, 10))
    stat_labels = _stats(stats, theme)

    table = ctk_frame(frame, theme, "card")
    table.grid(row=4, column=0, sticky="nsew", padx=theme.spacing.page_padding, pady=(0, 0))
    tree = build_tree(
        table,
        DASHBOARD_COLUMNS,
        headings=("ID", "Campaign", "Status", "Created", "Modified", "SMTP Profile", "Template", "Contact List", "Recipients"),
        height=18,
    )
    tree.column("id", width=48, minwidth=48, stretch=False)
    tree.column("name", width=220, minwidth=180, stretch=True)
    tree.column("status", width=98, minwidth=90, stretch=False)
    tree.column("created_at", width=112, minwidth=104, stretch=False)
    tree.column("updated_at", width=112, minwidth=104, stretch=False)
    tree.column("smtp_profile_name", width=150, minwidth=120, stretch=True)
    tree.column("template_name", width=150, minwidth=120, stretch=True)
    tree.column("list_name", width=150, minwidth=120, stretch=True)
    tree.column("recipient_count", width=92, minwidth=82, stretch=False)

    def refresh() -> None:
        rows = app.campaign_service.list_campaigns(search.get())
        clear_tree(tree)
        counts = {"Draft": 0, "Ready": 0, "Scheduled": 0, "Archived": 0}
        for row in rows:
            counts[row.get("status") or "Draft"] = counts.get(row.get("status") or "Draft", 0) + 1
            insert_table_row(tree, [row.get(column, "") or "" for column in DASHBOARD_COLUMNS])
        if not rows:
            insert_empty_row(tree, "No campaigns yet. Create your first campaign to get started.", DASHBOARD_COLUMNS)
        stat_labels["total"].configure(text=str(len(rows)))
        stat_labels["sent"].configure(text=str(sum(int(row.get("recipient_count") or 0) for row in rows)))
        stat_labels["delivery"].configure(text="99.8%")
        stat_labels["bounces"].configure(text="0.02%")

    def selected_id() -> int:
        selection = tree.selection()
        if not selection:
            return 0
        values = tree.item(selection[0], "values")
        try:
            return int(values[0]) if values else 0
        except (TypeError, ValueError):
            return 0

    def open_wizard(campaign_id: int = 0) -> None:
        CampaignWizard(frame, app, campaign_id or None, on_close=refresh)

    def edit_selected() -> None:
        campaign_id = selected_id()
        if not campaign_id:
            messagebox.showinfo("Edit Campaign", "Select a campaign first.")
            return
        open_wizard(campaign_id)

    def duplicate_selected() -> None:
        campaign_id = selected_id()
        if not campaign_id:
            messagebox.showinfo("Duplicate Campaign", "Select a campaign first.")
            return
        try:
            app.campaign_service.duplicate_campaign(campaign_id)
            refresh()
        except Exception as exc:
            messagebox.showerror("Duplicate Campaign", str(exc))

    def archive_selected() -> None:
        campaign_id = selected_id()
        if not campaign_id:
            messagebox.showinfo("Archive Campaign", "Select a campaign first.")
            return
        app.campaign_service.archive_campaign(campaign_id, True)
        refresh()

    def delete_selected() -> None:
        campaign_id = selected_id()
        if not campaign_id:
            messagebox.showinfo("Delete Campaign", "Select a campaign first.")
            return
        if messagebox.askyesno("Delete Campaign", "Delete this campaign?"):
            app.campaign_service.delete_campaign(campaign_id)
            refresh()

    search.trace_add("write", lambda *_: refresh())
    tree.bind("<Double-1>", lambda _event: edit_selected())
    refresh()


class CampaignWizard:
    def __init__(self, parent: tk.Widget, app, campaign_id: int | None = None, on_close=None) -> None:
        self.app = app
        self.on_close = on_close
        self.theme = app.theme
        self.window = ctk_toplevel(parent, "Campaign Builder", "1180x760")
        self.window.minsize(980, 660)
        self.campaign_id = campaign_id or app.campaign_service.create_campaign()
        self.step = 0
        self.vars = {
            "name": tk.StringVar(),
            "description": tk.StringVar(),
            "tags": tk.StringVar(),
            "internal_notes": tk.StringVar(),
            "contact_list": tk.StringVar(),
            "template": tk.StringVar(),
            "smtp_profile": tk.StringVar(),
            "send_rate": tk.StringVar(),
            "delay_between_emails": tk.StringVar(),
            "max_per_hour": tk.StringVar(),
            "max_per_day": tk.StringVar(),
            "business_hours": tk.StringVar(),
            "quiet_hours": tk.StringVar(),
        }
        self.progress = tk.StringVar()
        self.preview_index = 0
        self.preview_contacts: list[dict] = []
        self.body = ctk_frame(self.window, self.theme, "background")
        self.body.pack(fill="both", expand=True)
        self.body.rowconfigure(2, weight=1)
        self.body.columnconfigure(0, weight=1)
        self.steps = [
            ("Campaign Info", self._step_info),
            ("Contact List", self._step_contacts),
            ("Template", self._step_template),
            ("SMTP Profile", self._step_smtp),
            ("Rules", self._step_rules),
            ("Merge Preview", self._step_preview),
            ("Preflight", self._step_preflight),
            ("Summary", self._step_summary),
        ]
        self._load()
        self._render()
        self.window.protocol("WM_DELETE_WINDOW", self._close)

    def _load(self) -> None:
        campaign = self.app.campaign_service.get_campaign(self.campaign_id)
        rules = self.app.campaign_rules_service.get_rules(self.campaign_id)
        if campaign:
            self.vars["name"].set(campaign.get("name") or "")
            self.vars["description"].set(campaign.get("description") or "")
            self.vars["tags"].set(campaign.get("tags") or "")
            self.vars["internal_notes"].set(campaign.get("internal_notes") or "")
            self.vars["contact_list"].set(self._label("list", campaign.get("contact_list_id")))
            self.vars["template"].set(self._label("template", campaign.get("template_id")))
            self.vars["smtp_profile"].set(self._label("smtp", campaign.get("smtp_profile_id")))
        for key in ["send_rate", "delay_between_emails", "max_per_hour", "max_per_day", "business_hours", "quiet_hours"]:
            self.vars[key].set(rules.get(key) or "")

    def _render(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()
        self.progress.set(f"Step {self.step + 1} of {len(self.steps)}")
        header = ctk_frame(self.body, self.theme, "background")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 10))
        header.columnconfigure(0, weight=1)
        ctk_label(header, self.theme, "Campaign Builder", "title", "background").grid(row=0, column=0, sticky="w")
        ctk_label(
            header,
            self.theme,
            "Build, review, and prepare a campaign before sending is enabled.",
            "caption",
            "background",
            text_color=self.theme.palette.text_muted,
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ctk_label(header, self.theme, "", "caption", "background", textvariable=self.progress, text_color=self.theme.palette.text_muted).grid(row=0, column=1, sticky="e")
        self._render_stepper(self.body).grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        content = ctk_frame(self.body, self.theme, "card")
        stretchy_steps = {"Template", "SMTP Profile", "Merge Preview", "Preflight", "Summary"}
        is_stretchy = self.steps[self.step][0] in stretchy_steps
        self.body.rowconfigure(2, weight=1 if is_stretchy else 0)
        sticky = "nsew" if is_stretchy else "new"
        content.grid(row=2, column=0, sticky=sticky, padx=24)
        content.columnconfigure(0, weight=1)
        self.steps[self.step][1](content)
        nav = ctk_frame(self.body, self.theme, "toolbar")
        nav.grid(row=3, column=0, sticky="ew", padx=24, pady=(12, 20))
        ctk_button(nav, self.theme, "Previous", command=self._previous, icon="undo", width=122).pack(side="left", padx=(12, 4), pady=10)
        ctk_button(nav, self.theme, "Next", command=self._next, variant="primary", icon="redo", width=112).pack(side="left", padx=4, pady=10)
        ctk_button(nav, self.theme, "Save Draft", command=self._save_draft, icon="save", width=132).pack(side="right", padx=(4, 12), pady=10)
        ctk_button(nav, self.theme, "Run Preflight", command=self._run_preflight, icon="test_connection", width=152).pack(side="right", padx=4, pady=10)
        ctk_button(nav, self.theme, "Mark Ready", command=self._mark_ready, variant="primary", icon="success", width=136).pack(side="right", padx=4, pady=10)

    def _render_stepper(self, parent: tk.Widget) -> tk.Widget:
        stepper = ctk_frame(parent, self.theme, "card")
        for idx, (title, _builder) in enumerate(self.steps):
            variant = "primary" if idx == self.step else "ghost"
            ctk_button(
                stepper,
                self.theme,
                f"{idx + 1}. {title}",
                command=lambda index=idx: self._go_to_step(index),
                variant=variant,
                width=128 if idx not in {5, 7} else 142,
                height=30,
            ).pack(side="left", padx=(10 if idx == 0 else 2, 2), pady=10)
        return stepper

    def _step_info(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        ctk_label(parent, self.theme, "Campaign Info", "panel_title", "card").grid(row=0, column=0, sticky="w", padx=22, pady=(18, 4))
        ctk_label(
            parent,
            self.theme,
            "Name the campaign and add internal notes before selecting recipients, templates, and delivery rules.",
            "caption",
            "card",
            text_color=self.theme.palette.text_muted,
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 14))

        form = ctk_frame(parent, self.theme, "surface")
        form.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 22))
        form.columnconfigure((0, 1), weight=1, uniform="campaign_info")
        self._field(form, 0, 0, "name", "Campaign Name", "Used internally to identify this campaign.")
        self._field(form, 0, 1, "tags", "Tags", "Optional labels, separated by commas.")
        self._field(form, 1, 0, "description", "Description", "Short working summary for your team.")
        self._field(form, 1, 1, "internal_notes", "Internal Notes", "Private notes, reminders, or approvals.")

    def _field(self, parent: tk.Widget, row: int, column: int, key: str, label_text: str, helper: str = "") -> None:
        field = ctk_frame(parent, self.theme, "surface", border_width=0, fg_color="transparent")
        field.grid(row=row, column=column, sticky="ew", padx=(16, 10), pady=(14, 12))
        field.columnconfigure(0, weight=1)
        ctk_label(field, self.theme, label_text, "caption", "surface", text_color=self.theme.palette.text).grid(row=0, column=0, sticky="w")
        ctk_entry(field, self.theme, self.vars[key], placeholder_text=label_text).grid(row=1, column=0, sticky="ew", pady=(5, 4))
        if helper:
            ctk_label(field, self.theme, helper, "small", "surface", text_color=self.theme.palette.text_muted, wraplength=360).grid(row=2, column=0, sticky="w")

    def _step_contacts(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        lists = self.app.contact_list_service.list_lists()
        labels = [self._list_label(row) for row in lists]
        ctk_combobox(parent, self.theme, self.vars["contact_list"], labels).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 12))
        stats = self.app.campaign_summary_service.contact_stats(self._id_from_label(self.vars["contact_list"].get())) if self.vars["contact_list"].get() else self.app.campaign_summary_service.empty_stats()
        self._cards(parent, stats, 1)

    def _step_template(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        templates = self.app.template_service.list_templates()
        labels = [f"{row['id']} - {row['name']}" for row in templates]
        ctk_combobox(parent, self.theme, self.vars["template"], labels).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 10))
        template = self.app.template_service.get_template(self._id_from_label(self.vars["template"].get())) if self.vars["template"].get() else None
        preview = tk.Text(parent, height=20, wrap="word", padx=10, pady=10)
        style_text_widget(preview, self.theme)
        preview.grid(row=1, column=0, sticky="nsew")
        parent.rowconfigure(1, weight=1)
        if template:
            preview.insert("1.0", f"Template: {template['name']}\nSubject: {template.get('subject') or ''}\nPreheader: {template.get('preheader') or ''}\nModified: {template.get('updated_at') or ''}\n\n{self.app.template_service.html_to_text(template.get('html_body') or '')}")
        preview.configure(state="disabled")

    def _step_smtp(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        profiles = self.app.smtp_service.list_profiles()
        labels = [f"{row['id']} - {row['profile_name']}" for row in profiles]
        ctk_combobox(parent, self.theme, self.vars["smtp_profile"], labels).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 12))
        profile = self.app.smtp_service.get_profile(self._id_from_label(self.vars["smtp_profile"].get())) if self.vars["smtp_profile"].get() else None
        details = tk.Text(parent, height=16, wrap="word")
        style_text_widget(details, self.theme)
        details.grid(row=1, column=0, sticky="nsew")
        parent.rowconfigure(1, weight=1)
        if profile:
            blacklist = self.app.smtp_service.blacklist_results(profile["id"])
            listed = sum(1 for row in blacklist if row.get("listed"))
            details.insert(
                "1.0",
                "\n".join(
                    [
                        f"Profile: {profile.get('profile_name')}",
                        f"Host: {profile.get('host')}:{profile.get('port')}",
                        f"From: {profile.get('from_email')}",
                        f"Reply-To: {profile.get('reply_to_email')}",
                        f"Last Test: {profile.get('last_test_status')} at {profile.get('last_test_at') or '-'}",
                        f"Reputation: {listed} listed zones from latest stored results",
                        f"Daily Limit: {profile.get('daily_limit')}",
                        f"Hourly Limit: {profile.get('hourly_limit')}",
                    ]
                ),
            )
        details.configure(state="disabled")

    def _step_rules(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        for row, (key, label) in enumerate([
            ("send_rate", "Send rate placeholder"),
            ("delay_between_emails", "Delay between emails placeholder"),
            ("max_per_hour", "Max per hour placeholder"),
            ("max_per_day", "Max per day placeholder"),
            ("business_hours", "Business hours placeholder"),
            ("quiet_hours", "Quiet hours placeholder"),
        ]):
            ctk_label(parent, self.theme, label, "caption", "card").grid(row=row, column=0, sticky="w", padx=(16, 10), pady=6)
            ctk_entry(parent, self.theme, self.vars[key]).grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=6)

    def _step_preview(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        controls = ctk_frame(parent, self.theme, "toolbar")
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ctk_button(controls, self.theme, "Previous Contact", command=lambda: self._move_preview(-1), icon="undo", width=160).pack(side="left", padx=(12, 4), pady=12)
        ctk_button(controls, self.theme, "Next Contact", command=lambda: self._move_preview(1), icon="redo", width=140).pack(side="left", padx=4, pady=12)
        ctk_button(controls, self.theme, "Random Contact", command=lambda: self._random_preview(), icon="sparkles", width=152).pack(side="left", padx=4, pady=12)
        preview = tk.Text(parent, height=24, wrap="word", padx=10, pady=10)
        style_text_widget(preview, self.theme)
        preview.grid(row=1, column=0, sticky="nsew")
        self._load_preview_contacts()
        preview.insert("1.0", self._merged_preview())
        preview.configure(state="disabled")

    def _step_preflight(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        self._save_silent()
        result = self.app.preflight_service.run(self.campaign_id)
        tree = build_tree(parent, ("level", "label", "message"), headings=("Status", "Check", "Message"), height=20)
        for item in result["checks"]:
            icon = {"pass": "PASS", "warning": "WARN", "error": "ERROR"}[item["level"]]
            tree.insert("", "end", values=[icon, item["label"], item["message"]])
        ctk_label(parent, self.theme, f"Errors: {result['errors']}   Warnings: {result['warnings']}   Ready: {'Yes' if result['can_mark_ready'] else 'No'}", "caption", "card").grid(row=1, column=0, sticky="w", padx=16, pady=(10, 0))

    def _step_summary(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        self._save_silent()
        summary = self.app.campaign_summary_service.summary(self.campaign_id)
        campaign = summary["campaign"]
        contacts = summary["contacts"]
        rules = summary["rules"]
        text = tk.Text(parent, wrap="word", padx=10, pady=10)
        style_text_widget(text, self.theme)
        text.grid(row=0, column=0, sticky="nsew")
        parent.rowconfigure(0, weight=1)
        text.insert(
            "1.0",
            "\n".join(
                [
                    f"Campaign Name: {campaign.get('name')}",
                    f"Template: {campaign.get('template_name') or campaign.get('template_id') or '-'}",
                    f"SMTP Profile: {campaign.get('smtp_profile_name') or campaign.get('smtp_profile_id') or '-'}",
                    f"Contact List: {campaign.get('contact_list_name') or campaign.get('contact_list_id') or '-'}",
                    f"Total Recipients: {contacts['total']}",
                    f"Estimated Send Count: {contacts['estimated_send_count']}",
                    f"Suppressed Count: {contacts['suppressed']}",
                    f"Duplicate Count: {contacts['duplicates']}",
                    f"Deliverable: {contacts['Deliverable']}  Risky: {contacts['Risky']}  Unknown: {contacts['Unknown']}  Undeliverable: {contacts['Undeliverable']}",
                    "",
                    "Campaign Rules:",
                    f"Send rate: {rules.get('send_rate') or '-'}",
                    f"Delay: {rules.get('delay_between_emails') or '-'}",
                    f"Max/hour: {rules.get('max_per_hour') or '-'}",
                    f"Max/day: {rules.get('max_per_day') or '-'}",
                    f"Business hours: {rules.get('business_hours') or '-'}",
                    f"Quiet hours: {rules.get('quiet_hours') or '-'}",
                    "",
                    f"Notes: {campaign.get('internal_notes') or '-'}",
                ]
            ),
        )
        text.configure(state="disabled")

    def _cards(self, parent: ttk.Frame, stats: dict, row: int) -> None:
        cards = ctk_frame(parent, self.theme, "background")
        cards.grid(row=row, column=0, sticky="ew")
        for idx, key in enumerate(["total", "estimated_send_count", "suppressed", "duplicates", "Deliverable", "Risky", "Unknown", "Undeliverable"]):
            level = {
                "Deliverable": "success",
                "Risky": "warning",
                "Undeliverable": "danger",
                "suppressed": "danger",
            }.get(key, "default")
            card = ds.MetricCard(cards, key.replace("_", " ").title(), stats.get(key, 0), theme=self.theme, level=level)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 6, 0))
            cards.columnconfigure(idx, weight=1)

    def _save_silent(self) -> None:
        template = self.app.template_service.get_template(self._id_from_label(self.vars["template"].get())) if self.vars["template"].get() else None
        self.app.campaign_service.save_builder(
            {
                "name": self.vars["name"].get() or "Untitled Campaign",
                "description": self.vars["description"].get(),
                "tags": self.vars["tags"].get(),
                "internal_notes": self.vars["internal_notes"].get(),
                "contact_list_id": self._id_from_label(self.vars["contact_list"].get()) or None,
                "template_id": self._id_from_label(self.vars["template"].get()) or None,
                "smtp_profile_id": self._id_from_label(self.vars["smtp_profile"].get()) or None,
                "subject": (template or {}).get("subject") or "",
                "html_body": (template or {}).get("html_body") or "",
                "plain_text_body": (template or {}).get("plain_text_body") or "",
                "footer_text": "{{Unsubscribe}}" if "{{Unsubscribe}}" in ((template or {}).get("html_body") or "") else "",
                "status": (self.app.campaign_service.get_campaign(self.campaign_id) or {}).get("status") or "Draft",
            },
            self.campaign_id,
        )
        self.app.campaign_rules_service.save_rules(
            self.campaign_id,
            {key: self.vars[key].get() for key in ["send_rate", "delay_between_emails", "max_per_hour", "max_per_day", "business_hours", "quiet_hours"]},
        )

    def _save_draft(self) -> None:
        try:
            self._save_silent()
            self.app.campaign_service.mark_draft(self.campaign_id)
            messagebox.showinfo("Campaign", "Campaign saved as Draft.", parent=self.window)
            if self.on_close:
                self.on_close()
        except Exception as exc:
            messagebox.showerror("Campaign", str(exc), parent=self.window)

    def _run_preflight(self) -> None:
        try:
            self._save_silent()
            self.step = 6
            self._render()
        except Exception as exc:
            messagebox.showerror("Preflight", str(exc), parent=self.window)

    def _mark_ready(self) -> None:
        try:
            self._save_silent()
            result = self.app.preflight_service.run(self.campaign_id)
            if not result["can_mark_ready"]:
                messagebox.showerror("Preflight", "Blocking errors must be fixed before marking Ready.", parent=self.window)
                self.step = 6
                self._render()
                return
            self.app.campaign_service.mark_ready(self.campaign_id)
            messagebox.showinfo("Campaign Ready", "Campaign marked Ready.", parent=self.window)
            if self.on_close:
                self.on_close()
        except Exception as exc:
            messagebox.showerror("Campaign Ready", str(exc), parent=self.window)

    def _previous(self) -> None:
        self._save_silent()
        self.step = max(0, self.step - 1)
        self._render()

    def _next(self) -> None:
        self._save_silent()
        self.step = min(len(self.steps) - 1, self.step + 1)
        self._render()

    def _go_to_step(self, index: int) -> None:
        self._save_silent()
        self.step = max(0, min(len(self.steps) - 1, index))
        self._render()

    def _close(self) -> None:
        try:
            self._save_silent()
        finally:
            if self.on_close:
                self.on_close()
            self.window.destroy()

    def _load_preview_contacts(self) -> None:
        list_id = self._id_from_label(self.vars["contact_list"].get())
        self.preview_contacts = self.app.contact_service.list_contacts(list_id, "", "All", "All") if list_id else []
        self.preview_index = min(self.preview_index, max(0, len(self.preview_contacts) - 1))

    def _move_preview(self, delta: int) -> None:
        self._load_preview_contacts()
        if self.preview_contacts:
            self.preview_index = (self.preview_index + delta) % len(self.preview_contacts)
        self._render()

    def _random_preview(self) -> None:
        self._load_preview_contacts()
        if self.preview_contacts:
            self.preview_index = random.randrange(len(self.preview_contacts))
        self._render()

    def _merged_preview(self) -> str:
        template = self.app.template_service.get_template(self._id_from_label(self.vars["template"].get())) if self.vars["template"].get() else None
        if not template:
            return "Choose a template to preview merged content."
        contact = self.preview_contacts[self.preview_index] if self.preview_contacts else {}
        subject = self._merge(template.get("subject") or "", contact)
        body = self._merge(self.app.template_service.html_to_text(template.get("html_body") or ""), contact)
        return f"Contact {self.preview_index + 1 if self.preview_contacts else 0} of {len(self.preview_contacts)}\n\nSubject: {subject}\n\n{body}"

    def _merge(self, text: str, contact: dict) -> str:
        values = {
            "FirstName": contact.get("first_name") or "",
            "LastName": contact.get("last_name") or "",
            "Company": contact.get("company") or "",
            "Email": contact.get("email") or "",
            "State": contact.get("state") or "",
            "City": contact.get("city") or "",
            "Custom1": contact.get("custom1") or "",
            "Custom2": contact.get("custom2") or "",
            "Custom3": contact.get("custom3") or "",
            "Unsubscribe": "unsubscribe link placeholder",
        }
        return re.sub(r"{{\s*([A-Za-z0-9_]+)\s*}}", lambda m: values.get(m.group(1), m.group(0)), text)

    def _label(self, kind: str, item_id: int | None) -> str:
        if not item_id:
            return ""
        if kind == "list":
            item = self.app.contact_list_service.get_list(int(item_id))
            return self._list_label(item) if item else ""
        if kind == "template":
            item = self.app.template_service.get_template(int(item_id))
            return f"{item['id']} - {item['name']}" if item else ""
        if kind == "smtp":
            item = self.app.smtp_service.get_profile(int(item_id))
            return f"{item['id']} - {item['profile_name']}" if item else ""
        return ""

    def _list_label(self, row: dict) -> str:
        return f"{row['id']} - {row['name']} ({row.get('total_contacts') or 0})"

    def _id_from_label(self, label: str) -> int:
        if not label:
            return 0
        try:
            return int(label.split(" - ", 1)[0])
        except ValueError:
            return 0


def _stats(parent: tk.Widget, theme) -> dict[str, tk.Widget]:
    labels = {}
    specs = [("total", "Active Now", "info"), ("sent", "Total Sent", "default"), ("delivery", "Delivery Rate", "success"), ("bounces", "Bounces", "warning")]
    for idx, (key, label, level) in enumerate(specs):
        card = ds.MetricCard(parent, label, "0", theme=theme, level=level)
        card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 10, 0))
        labels[key] = card.value_label
        parent.columnconfigure(idx, weight=1)
    return labels


def _clear_tree(tree: ttk.Treeview) -> None:
    for item in tree.get_children():
        tree.delete(item)
