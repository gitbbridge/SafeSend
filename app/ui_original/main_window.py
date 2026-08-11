import tkinter as tk
from tkinter import ttk

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
from app.services.queue_service import QueueService
from app.services.preflight_service import PreflightService
from app.services.signature_service import SignatureService
from app.services.spam_analysis_service import SpamAnalysisService
from app.services.smtp_service import SMTPService
from app.services.subject_service import SubjectService
from app.services.suppression_service import SuppressionService
from app.services.template_service import TemplateService
from app.services.verification_service import VerificationService
from app.ui import campaigns, clustering, compose, contacts, dashboard, queue, reports, sending_rules, settings, smtp_servers, suppression, verification
from app.ui.shared import StatusBar, clear_frame


class SafeSendApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SafeSend")
        self.root.geometry("1260x780")
        self.root.minsize(1040, 680)
        self.theme_name = self._load_theme()

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
        self.suppression_service = SuppressionService()
        self.verification_service = VerificationService()

        self.shell = ttk.Frame(self.root)
        self.shell.pack(fill="both", expand=True)
        self.sidebar = ttk.Frame(self.shell, width=230, style="Sidebar.TFrame")
        self.sidebar.pack(side="left", fill="y")
        self.content = ttk.Frame(self.shell)
        self.content.pack(side="right", fill="both", expand=True)
        self.status = StatusBar(self.root)
        self.status.pack(fill="x", side="bottom", padx=8, pady=4)

        self.routes = {
            "Dashboard": dashboard.build,
            "Campaigns": campaigns.build,
            "Compose": compose.build,
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
        self._build_sidebar()
        self.navigate("Dashboard")

    def run(self) -> None:
        self.root.mainloop()

    def navigate(self, name: str) -> None:
        clear_frame(self.content)
        self.status.set(name)
        self.routes[name](self.content, self)

    def _build_sidebar(self) -> None:
        ttk.Label(self.sidebar, text="SafeSend", style="Brand.TLabel").pack(anchor="w", padx=18, pady=(20, 2))
        ttk.Label(self.sidebar, text="Commercial SMTP sender", style="SidebarMuted.TLabel").pack(anchor="w", padx=18, pady=(0, 16))
        for name in self.routes:
            ttk.Button(self.sidebar, text=name, style="Sidebar.TButton", command=lambda route=name: self.navigate(route)).pack(
                fill="x", padx=12, pady=2
            )

    def _load_theme(self) -> str:
        try:
            import TKinterModernThemes  # noqa: F401

            theme_name = "azure"
        except Exception:
            theme_name = "azure-inspired"
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        bg = "#f5f8fb"
        panel = "#ffffff"
        ink = "#172033"
        muted = "#65758b"
        azure = "#0f75bc"
        azure_dark = "#0a4f85"
        self.root.configure(bg=bg)
        style.configure(".", font=("Segoe UI", 10), background=bg, foreground=ink)
        style.configure("TFrame", background=bg)
        style.configure("Card.TFrame", background=panel, relief="solid", borderwidth=1)
        style.configure("Sidebar.TFrame", background="#102a43")
        style.configure("Brand.TLabel", background="#102a43", foreground="#ffffff", font=("Segoe UI Semibold", 18))
        style.configure("SidebarMuted.TLabel", background="#102a43", foreground="#b9c9d8", font=("Segoe UI", 9))
        style.configure("Sidebar.TButton", anchor="w", padding=(12, 9), background="#102a43", foreground="#eef6ff", borderwidth=0)
        style.map("Sidebar.TButton", background=[("active", "#173d5f")], foreground=[("active", "#ffffff")])
        style.configure("Title.TLabel", font=("Segoe UI Semibold", 20), background=bg, foreground=ink)
        style.configure("PanelTitle.TLabel", font=("Segoe UI Semibold", 12), background=panel, foreground=ink)
        style.configure("Muted.TLabel", foreground=muted, background=bg)
        style.configure("CardMuted.TLabel", foreground=muted, background=panel)
        style.configure("TButton", padding=(12, 7), background=azure, foreground="#ffffff")
        style.map("TButton", background=[("active", azure_dark)])
        style.configure("Treeview", rowheight=28, fieldbackground=panel, background=panel)
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9))
        return theme_name
