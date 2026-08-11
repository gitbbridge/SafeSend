import tkinter as tk
import threading
import time
from tkinter import messagebox, ttk
from typing import Any, Callable

import customtkinter as ctk
from app.design_system.customtkinter_adapter import app_window, apply_customtkinter_runtime
from app.design_system.customtkinter_adapter import button as ctk_button
from app.design_system.customtkinter_adapter import frame as ctk_frame
from app.design_system.customtkinter_adapter import label as ctk_label
from app.design_system.components import command_search
from app.design_system.components import icon_label
from app.services.blacklist_service import BlacklistService
from app.services.campaign_rules_service import CampaignRulesService
from app.services.campaign_service import CampaignService
from app.services.campaign_summary_service import CampaignSummaryService
from app.services.clustering_service import ClusteringService
from app.services.contact_list_service import ContactListService
from app.services.contact_service import ContactService
from app.services.draft_service import DraftService
from app.services.export_service import ExportService
from app.services.import_service import ImportService
from app.services.preflight_service import PreflightService
from app.services.queue_service import QueueService
from app.services.send_engine import SendEngine
from app.services.operation_tracker import OperationHandle, OperationTracker
from app.services.signature_service import SignatureService
from app.services.spam_analysis_service import SpamAnalysisService
from app.services.smtp_service import SMTPService
from app.services.subject_service import SubjectService
from app.services.suppression_service import SuppressionService
from app.services.template_service import TemplateService
from app.services.verification_service import VerificationService
from app.ui import campaigns, clustering, compose, contacts, dashboard, design_system_gallery, queue, reports, sending_rules, settings, smtp_servers, suppression, templates, verification
from app.ui.shared import StatusBar
from app.design_system.assets import LOGO_ICO, LOGO_PNG
from app.design_system.dialogs import ask_stop_processing, install_dialogs
from app.design_system.icons import get_route_icon, icon_image
from app.design_system.image_manager import image_manager
from app.design_system.layout import LAYOUT
from app.design_system.theme import active_theme, apply_theme
from app.design_system.tooltips import tooltip
from app.ui.components.first_run_wizard import FirstRunWizard
from app.ui.components.help_center import HelpCenter


class SafeSendApp:
    def __init__(self) -> None:
        self.theme = active_theme()
        apply_customtkinter_runtime(self.theme)
        self.root = app_window()
        self.root.title("SafeSend")
        self.root.geometry(self._safe_window_geometry())
        self.root.minsize(LAYOUT.min_window_width, LAYOUT.min_window_height)
        install_dialogs(self.root)
        self.theme_name = self._load_theme()
        self.logo_image = None
        self.sidebar_buttons: dict[str, ctk.CTkButton] = {}
        self.sidebar_icon_images: list[ctk.CTkImage] = []
        self.page_cache: dict[str, tk.Widget] = {}
        self.sidebar_collapsed = False
        self.current_route = ""
        self.global_search = tk.StringVar()
        self.global_search_entry = None
        self._is_shutting_down = False
        self._force_exit = False
        self._operation_after_id = ""
        self.operation_tracker = OperationTracker()
        self._background_threads: list[threading.Thread] = []
        self._background_threads_lock = threading.Lock()

        self.smtp_service = SMTPService()
        self.blacklist_service = BlacklistService()
        self.import_service = ImportService()
        self.contact_list_service = ContactListService()
        self.contact_service = ContactService()
        self.export_service = ExportService()
        self.template_service = TemplateService()
        self.draft_service = DraftService()
        self.signature_service = SignatureService()
        self.subject_service = SubjectService()
        self.spam_analysis_service = SpamAnalysisService()
        self.campaign_service = CampaignService()
        self.campaign_rules_service = CampaignRulesService()
        self.campaign_summary_service = CampaignSummaryService()
        self.preflight_service = PreflightService()
        self.cluster_service = ClusteringService()
        self.queue_service = QueueService()
        self.send_engine = SendEngine(operation_tracker=self.operation_tracker)
        self.suppression_service = SuppressionService()
        self.verification_service = VerificationService()

        self.shell = ctk_frame(self.root, self.theme, "background")
        self.shell.pack(fill="both", expand=True)
        self.sidebar = ctk.CTkFrame(self.shell, fg_color=self.theme.palette.surface, width=188, corner_radius=0, border_width=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.main_area = ctk_frame(self.shell, self.theme, "content")
        self.main_area.pack(side="right", fill="both", expand=True)
        self._build_topbar()
        self.content = ctk_frame(self.main_area, self.theme, "content")
        self.content.pack(fill="both", expand=True)
        self.status = StatusBar(self.root)
        self.status.pack(fill="x", side="bottom")

        self.routes = {
            "Dashboard": dashboard.build,
            "Design System": design_system_gallery.build,
            "Campaigns": campaigns.build,
            "Compose": compose.build,
            "Templates": templates.build,
            "Contacts / Lists": contacts.build,
            "SMTP Servers": smtp_servers.build,
            "Sending Rules": sending_rules.build,
            "Clustering / Reputation Strategy": clustering.build,
            "Verification": verification.build,
            "Sending Queue": queue.build,
            "Reports / Logs": reports.build,
            "Suppression List": suppression.build,
            "Settings": settings.build,
        }
        self.search_index = self._build_search_index()
        self._build_sidebar()
        self.root.bind_all("<Control-k>", self._focus_global_search, add="+")
        self.root.bind_all("<Control-K>", self._focus_global_search, add="+")
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self._poll_operation_updates()
        self.navigate("Dashboard")

    def _safe_window_geometry(self) -> str:
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = min(LAYOUT.default_window_width, max(LAYOUT.min_window_width, screen_width - 80))
        height = min(LAYOUT.default_window_height, max(LAYOUT.min_window_height, screen_height - 180))
        x = max(0, (screen_width - width) // 2)
        y = 24
        return f"{width}x{height}+{x}+{y}"

    def run(self) -> None:
        self.root.mainloop()

    def navigate(self, name: str) -> None:
        if self._is_shutting_down:
            return
        previous_route = self.current_route
        if previous_route == name and name in self.page_cache:
            page = self.page_cache[name]
            if hasattr(page, "on_show"):
                page.on_show()
            return
        self.current_route = name
        self.status.set(name)
        for route, button in self.sidebar_buttons.items():
            if route == name:
                button.configure(fg_color=self.theme.palette.selection, text_color=self.theme.palette.primary)
            else:
                button.configure(fg_color="transparent", text_color=self.theme.palette.text)

        if previous_route and previous_route in self.page_cache:
            previous_page = self.page_cache[previous_route]
            if hasattr(previous_page, "on_hide"):
                previous_page.on_hide()
            previous_page.pack_forget()
        if name not in self.page_cache:
            host = self._create_page_host()
            self.page_cache[name] = host
            self.routes[name](host, self)
        page = self.page_cache[name]
        page.pack(fill="both", expand=True)
        if hasattr(page, "on_show"):
            page.on_show()

    def shutdown(self) -> None:
        if self._is_shutting_down:
            return
        stop_handle = None
        if not self._force_exit and self.operation_tracker.has_active_critical():
            active = self.operation_tracker.active_operations()
            current = active[0].label if active else ""
            if not ask_stop_processing(self.root, current):
                self.status.set("SafeSend is still running active work.")
                return
            self._force_exit = True
            stop_handle = self.operation_tracker.begin("Stopping safely", "Stopping safely...", cancellable=False)
            self.operation_tracker.cancel_all()
            self.send_engine.shutdown(timeout=8.0)
            if not self._wait_for_background_operations(timeout=30.0):
                self.status.set("SafeSend is still stopping active work. Please wait.")
                if stop_handle:
                    stop_handle.complete()
                self._force_exit = False
                return
        self._is_shutting_down = True
        try:
            self.root.unbind_all("<Control-k>")
            self.root.unbind_all("<Control-K>")
            if self._operation_after_id:
                self.root.after_cancel(self._operation_after_id)
        except tk.TclError:
            pass
        for page in list(self.page_cache.values()):
            try:
                if hasattr(page, "on_hide"):
                    page.on_hide()
                if hasattr(page, "cleanup"):
                    page.cleanup()
            except tk.TclError:
                pass
        try:
            self.send_engine.shutdown(timeout=3.0)
        except Exception:
            pass
        if stop_handle:
            stop_handle.complete()
        self.page_cache.clear()
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass

    def run_background_operation(
        self,
        title: str,
        worker: Callable[[OperationHandle], Any],
        *,
        detail: str = "",
        total: int | None = None,
        on_success: Callable[[Any], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> threading.Thread:
        handle = self.operation_tracker.begin(title, detail or title, total=total)

        def target() -> None:
            try:
                result = worker(handle)
            except Exception as exc:
                self._schedule_ui(lambda error=exc: self._operation_error(error, on_error))
            else:
                if on_success:
                    self._schedule_ui(lambda value=result: on_success(value))
            finally:
                handle.complete()

        thread = threading.Thread(target=target, name=f"SafeSendOperation-{title}", daemon=True)
        with self._background_threads_lock:
            self._background_threads.append(thread)
        thread.start()
        return thread

    def _operation_error(self, exc: Exception, handler: Callable[[Exception], None] | None) -> None:
        if handler:
            handler(exc)
            return
        messagebox.showerror("SafeSend operation failed", str(exc), parent=self.root)

    def _schedule_ui(self, callback: Callable[[], None]) -> None:
        if self._is_shutting_down:
            return
        try:
            self.root.after(0, callback)
        except tk.TclError:
            pass

    def _poll_operation_updates(self) -> None:
        try:
            self._prune_background_threads()
            for update in self.operation_tracker.drain_updates():
                if update.active:
                    self.status.show_operation(update)
                elif not self.operation_tracker.has_active_critical():
                    self.status.clear_operation()
            self._operation_after_id = self.root.after(150, self._poll_operation_updates)
        except tk.TclError:
            self._operation_after_id = ""

    def _prune_background_threads(self) -> None:
        with self._background_threads_lock:
            self._background_threads = [thread for thread in self._background_threads if thread.is_alive()]

    def _wait_for_background_operations(self, timeout: float) -> bool:
        end_at = time.time() + timeout
        while time.time() < end_at:
            self._prune_background_threads()
            with self._background_threads_lock:
                threads = list(self._background_threads)
            if not threads:
                return True
            for thread in threads:
                thread.join(timeout=0.1)
        self._prune_background_threads()
        with self._background_threads_lock:
            return not self._background_threads

    def _create_page_host(self) -> ctk.CTkScrollableFrame:
        palette = self.theme.palette
        host = ctk.CTkScrollableFrame(
            self.content,
            fg_color=palette.background,
            corner_radius=0,
            border_width=0,
            scrollbar_button_color=palette.border,
            scrollbar_button_hover_color=palette.hover,
        )
        host.columnconfigure(0, weight=1)
        return host

    def _build_sidebar(self) -> None:
        for child in self.sidebar.winfo_children():
            child.destroy()
        self.sidebar_buttons = {}
        self.sidebar_icon_images = []
        space = self.theme.spacing
        palette = self.theme.palette
        collapsed = self.sidebar_collapsed
        width = 72 if collapsed else 188
        self.sidebar.configure(width=width)

        toggle_row = ctk.CTkFrame(self.sidebar, fg_color=palette.surface, corner_radius=0)
        toggle_row.pack(fill="x", padx=10, pady=(10, 4))
        toggle = ctk.CTkButton(
            toggle_row,
            text="" if collapsed else "Collapse menu",
            command=self._toggle_sidebar,
            image=icon_image("sidebar", color=palette.text_muted, size=14),
            compound="left",
            width=44 if collapsed else 154,
            height=26,
            corner_radius=4,
            fg_color="transparent",
            hover_color=palette.hover,
            text_color=palette.text_muted,
            font=(self.theme.typography.family, 10),
            anchor="center" if collapsed else "w",
        )
        toggle.pack(anchor="center" if collapsed else "w", padx=(0 if collapsed else 14, 0))
        self.sidebar_icon_images.append(toggle.cget("image"))
        tooltip(toggle, "Expand menu" if collapsed else "Collapse menu")

        self._build_brand(collapsed)
        nav = ctk.CTkFrame(self.sidebar, fg_color=palette.surface, corner_radius=0)
        nav.pack(fill="x", padx=0, pady=(10, 0))
        for name in self.routes:
            if name == "Design System":
                continue
            nav_icon = icon_image(get_route_icon(name), color=palette.text_muted, size=14)
            self.sidebar_icon_images.append(nav_icon)
            button = ctk.CTkButton(
                nav,
                text="" if collapsed else _nav_label(name),
                command=lambda route=name: self.navigate(route),
                image=nav_icon,
                compound="left",
                width=42 if collapsed else 164,
                height=34,
                corner_radius=4,
                fg_color=palette.selection if name == self.current_route else "transparent",
                hover_color=palette.hover,
                text_color=palette.primary if name == self.current_route else palette.text,
                font=(self.theme.typography.family, 10),
                anchor="center" if collapsed else "w",
            )
            button.pack(
                fill="x" if not collapsed else "none", padx=12 if not collapsed else 0, pady=2
            )
            if collapsed:
                tooltip(button, name)
            self.sidebar_buttons[name] = button

        footer = ctk.CTkFrame(self.sidebar, fg_color=palette.surface, corner_radius=0)
        footer.pack(side="bottom", fill="x", padx=12, pady=(8, 14))
        if not collapsed:
            ctk_button(footer, self.theme, "Start Campaign", command=lambda: self.navigate("Campaigns"), variant="primary", icon="new", height=36).pack(fill="x", pady=(0, 10))
        help_button = _sidebar_footer_button(footer, self.theme, "" if collapsed else "Help", "help", lambda: HelpCenter(self.root), collapsed)
        help_button.pack(fill="x" if not collapsed else "none", pady=1)
        guide_button = _sidebar_footer_button(footer, self.theme, "" if collapsed else "First Run", "info", lambda: FirstRunWizard(self.root), collapsed)
        guide_button.pack(fill="x" if not collapsed else "none", pady=1)
        tooltip(help_button, "Help Center")
        tooltip(guide_button, "First Run Guide")
        if not collapsed:
            ctk.CTkLabel(footer, text="Saved locally", fg_color=palette.surface, text_color=palette.text_muted, font=(self.theme.typography.family, 9)).pack(anchor="w", pady=(8, 0))

    def _toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed
        self._build_sidebar()

    def _build_topbar(self) -> None:
        palette = self.theme.palette
        space = self.theme.spacing
        topbar = ctk.CTkFrame(self.main_area, fg_color=palette.surface, corner_radius=0, height=48, border_width=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        ctk.CTkFrame(topbar, fg_color=palette.border_soft, height=1, corner_radius=0).pack(side="bottom", fill="x")
        search = command_search(
            topbar,
            self.global_search,
            theme=self.theme,
            command=self._run_global_search,
            placeholder="Search campaigns, contacts, SMTP profiles...",
            width=540,
        )
        search.pack(side="left", padx=(18, space.md), pady=9)
        self.global_search_entry = search.entry
        ctk_label(topbar, self.theme, "SafeSend Workspace", role="caption", variant="card", text_color=palette.text, fg_color=palette.surface).pack(side="right", padx=(space.md, 18))
        for icon_name in ["info", "notifications", "settings"]:
            icon_label(topbar, icon_name, theme=self.theme, text_color=palette.text_muted, size=15, surface="card").pack(side="right", padx=8)

    def _focus_global_search(self, _event=None) -> str:
        if self.global_search_entry is not None:
            self.global_search_entry.focus_set()
            self.global_search_entry.select_range(0, "end")
            self.status.set("Search SafeSend by page, feature, or keyword.")
        return "break"

    def _build_search_index(self) -> dict[str, str]:
        aliases = {
            "Dashboard": "home overview metrics analytics health reputation charts status",
            "Design System": "components buttons cards table modal design icons style",
            "Campaigns": "campaign builder preflight draft scheduled archive",
            "Compose": "email composer writing subject preheader merge html editor",
            "Templates": "template library reusable assets favorites categories versions import export",
            "Contacts / Lists": "contacts lists recipients csv import export suppress verification",
            "SMTP Servers": "smtp profile server connection test reputation blacklist dns",
            "Sending Rules": "rules pacing delays limits quiet hours compliance footer",
            "Clustering / Reputation Strategy": "clustering domain strategy concentration queue ordering",
            "Verification": "verification deliverable risky undeliverable emailable api",
            "Sending Queue": "queue build send recipients smtp rotation",
            "Reports / Logs": "reports logs sent failed skipped analytics history",
            "Suppression List": "suppression unsubscribe blocklist do not send",
            "Settings": "settings database folders paths config api key",
        }
        return {route: f"{route} {aliases.get(route, '')}".lower() for route in self.routes}

    def _run_global_search(self) -> None:
        query = self.global_search.get().strip().lower()
        if not query:
            self.status.set("Type a page, feature, or keyword, then press Enter.")
            return
        if query in {"help", "help center", "docs", "documentation"}:
            HelpCenter(self.root)
            self.status.set("Opened Help Center.")
            return
        route_matches = [route for route in self.routes if query in route.lower()]
        matches = route_matches or [route for route, haystack in self.search_index.items() if query in haystack]
        if not matches:
            self.status.set(f"No SafeSend page matched '{self.global_search.get().strip()}'.")
            return
        self.navigate(matches[0])
        self.status.set(f"Search matched {matches[0]}.")

    def _load_theme(self) -> str:
        theme = apply_theme(self.root, self.theme)
        if LOGO_ICO.exists():
            try:
                self.root.iconbitmap(str(LOGO_ICO))
            except tk.TclError:
                pass
        return theme.name

    def _load_logo(self, parent: tk.Widget, collapsed: bool = False) -> None:
        try:
            if LOGO_PNG.exists():
                self.logo_image = image_manager.logo(LOGO_PNG, collapsed=collapsed)
                ctk.CTkLabel(parent, image=self.logo_image, text="", fg_color=self.theme.palette.surface).pack(anchor="center" if collapsed else "w")
                return
        except (tk.TclError, OSError):
            pass
        ctk_label(parent, self.theme, "SafeSend", role="brand", variant="card", fg_color=self.theme.palette.surface).pack(anchor="w")

    def _build_brand(self, collapsed: bool = False) -> None:
        palette = self.theme.palette
        if collapsed:
            holder = ctk.CTkFrame(self.sidebar, fg_color=palette.surface, corner_radius=0)
            holder.pack(fill="x", padx=17, pady=(12, 12))
            self._load_logo(holder, collapsed=True)
            return

        brand = ctk.CTkFrame(self.sidebar, fg_color=palette.surface, corner_radius=0)
        brand.pack(fill="x", padx=18, pady=(12, 2))
        brand.columnconfigure(1, weight=1)
        icon_holder = ctk.CTkFrame(brand, fg_color=palette.primary, width=34, height=34, corner_radius=6)
        icon_holder.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 10), pady=(0, 2))
        icon_holder.grid_propagate(False)
        try:
            if LOGO_PNG.exists():
                self.logo_image = image_manager.logo(LOGO_PNG, collapsed=True, size=(26, 26))
                ctk.CTkLabel(icon_holder, image=self.logo_image, text="", fg_color=palette.primary).place(relx=0.5, rely=0.5, anchor="center")
            else:
                ctk.CTkLabel(icon_holder, text="S", fg_color=palette.primary, text_color=palette.surface, font=(self.theme.typography.family_semibold, 16)).place(relx=0.5, rely=0.5, anchor="center")
        except (tk.TclError, OSError):
            ctk.CTkLabel(icon_holder, text="S", fg_color=palette.primary, text_color=palette.surface, font=(self.theme.typography.family_semibold, 16)).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(
            brand,
            text="SafeSend",
            fg_color=palette.surface,
            text_color=palette.text,
            font=(self.theme.typography.family_semibold, 18),
            anchor="w",
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            brand,
            text="Workspace",
            fg_color=palette.surface,
            text_color=palette.text_muted,
            font=(self.theme.typography.family, 9),
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(1, 0))


def _nav_label(route: str) -> str:
    return {
        "Contacts / Lists": "Contacts",
        "Clustering / Reputation Strategy": "Clustering",
        "Reports / Logs": "Reports",
        "Suppression List": "Suppressions",
        "SMTP Servers": "SMTP Servers",
        "Sending Queue": "Queue",
    }.get(route, route)


def _sidebar_footer_button(parent: tk.Widget, theme, text: str, icon: str, command, collapsed: bool) -> ctk.CTkButton:
    palette = theme.palette
    image = icon_image(icon, color=palette.text_muted, size=14)
    btn = ctk.CTkButton(
        parent,
        text="" if collapsed or not text else text,
        command=command,
        image=image,
        compound="left",
        width=42 if collapsed else 164,
        height=26,
        corner_radius=3,
        fg_color="transparent",
        hover_color=palette.hover,
        text_color=palette.text,
        font=(theme.typography.family, 9),
        anchor="center" if collapsed else "w",
    )
    btn._safesend_icon_image = image
    return btn
