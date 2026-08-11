from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

import customtkinter as ctk
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class IconSpec:
    name: str
    label: str
    category: str
    tone: str = "neutral"


ICON_CATEGORIES: dict[str, list[IconSpec]] = {
    "Navigation": [
        IconSpec("dashboard", "Dashboard", "Navigation", "primary"),
        IconSpec("campaigns", "Campaigns", "Navigation", "neutral"),
        IconSpec("compose", "Compose", "Navigation", "primary"),
        IconSpec("contacts", "Contacts", "Navigation", "neutral"),
        IconSpec("lists", "Lists", "Navigation", "neutral"),
        IconSpec("smtp_servers", "SMTP Servers", "Navigation", "neutral"),
        IconSpec("sending_queue", "Sending Queue", "Navigation", "neutral"),
        IconSpec("sending_rules", "Sending Rules", "Navigation", "neutral"),
        IconSpec("deliverability", "Deliverability", "Navigation", "success"),
        IconSpec("verification", "Verification", "Navigation", "success"),
        IconSpec("reports", "Reports", "Navigation", "neutral"),
        IconSpec("templates", "Templates", "Navigation", "neutral"),
        IconSpec("suppression", "Suppression List", "Navigation", "danger"),
        IconSpec("ai_assistant", "AI Assistant", "Navigation", "ai"),
        IconSpec("settings", "Settings", "Navigation", "neutral"),
        IconSpec("help", "Help Center", "Navigation", "info"),
        IconSpec("notifications", "Notifications", "Navigation", "neutral"),
        IconSpec("user_profile", "User Profile", "Navigation", "neutral"),
    ],
    "Email": [
        IconSpec("send", "Send", "Email", "primary"),
        IconSpec("inbox", "Inbox", "Email", "neutral"),
        IconSpec("outbox", "Outbox", "Email", "neutral"),
        IconSpec("drafts", "Drafts", "Email", "neutral"),
        IconSpec("reply", "Reply", "Email", "neutral"),
        IconSpec("attachment", "Attachment", "Email", "neutral"),
        IconSpec("signature", "Signature", "Email", "neutral"),
        IconSpec("subject", "Subject", "Email", "neutral"),
        IconSpec("preheader", "Preheader", "Email", "neutral"),
        IconSpec("preview", "Preview", "Email", "neutral"),
        IconSpec("spam_check", "Spam Check", "Email", "success"),
        IconSpec("read", "Read", "Email", "neutral"),
        IconSpec("unread", "Unread", "Email", "primary"),
        IconSpec("star", "Star", "Email", "warning"),
        IconSpec("flag", "Flag", "Email", "warning"),
        IconSpec("move", "Move", "Email", "neutral"),
        IconSpec("more", "More", "Email", "neutral"),
    ],
    "SMTP & Infrastructure": [
        IconSpec("server", "Server", "SMTP & Infrastructure", "neutral"),
        IconSpec("globe", "Globe / IP", "SMTP & Infrastructure", "neutral"),
        IconSpec("domain", "Domain", "SMTP & Infrastructure", "neutral"),
        IconSpec("dns", "DNS", "SMTP & Infrastructure", "neutral"),
        IconSpec("port", "Port", "SMTP & Infrastructure", "neutral"),
        IconSpec("connection", "Connection", "SMTP & Infrastructure", "success"),
        IconSpec("test_connection", "Test Connection", "SMTP & Infrastructure", "success"),
        IconSpec("authentication", "Authentication", "SMTP & Infrastructure", "neutral"),
        IconSpec("smtp_user", "SMTP User", "SMTP & Infrastructure", "neutral"),
        IconSpec("password", "Password", "SMTP & Infrastructure", "neutral"),
        IconSpec("rotation", "Rotation", "SMTP & Infrastructure", "primary"),
        IconSpec("threads", "Threads", "SMTP & Infrastructure", "neutral"),
        IconSpec("rate_limit", "Rate Limit", "SMTP & Infrastructure", "neutral"),
        IconSpec("retry", "Retry", "SMTP & Infrastructure", "neutral"),
        IconSpec("timeout", "Timeout", "SMTP & Infrastructure", "warning"),
        IconSpec("tls_ssl", "TLS / SSL", "SMTP & Infrastructure", "success"),
        IconSpec("spf", "SPF", "SMTP & Infrastructure", "success"),
        IconSpec("dkim", "DKIM", "SMTP & Infrastructure", "success"),
        IconSpec("dmarc", "DMARC", "SMTP & Infrastructure", "success"),
        IconSpec("mx_record", "MX Record", "SMTP & Infrastructure", "neutral"),
        IconSpec("health_check", "Health Check", "SMTP & Infrastructure", "success"),
    ],
    "Deliverability": [
        IconSpec("deliverability_score", "Deliverability Score", "Deliverability", "success"),
        IconSpec("reputation", "Reputation", "Deliverability", "success"),
        IconSpec("placement", "Placement", "Deliverability", "neutral"),
        IconSpec("blacklist", "Blacklist", "Deliverability", "danger"),
        IconSpec("whitelist", "Whitelist", "Deliverability", "success"),
        IconSpec("warning", "Warning", "Deliverability", "warning"),
        IconSpec("success", "Success", "Deliverability", "success"),
        IconSpec("error", "Error", "Deliverability", "danger"),
        IconSpec("info", "Info", "Deliverability", "info"),
        IconSpec("bounce", "Bounce", "Deliverability", "warning"),
        IconSpec("suppressed", "Suppressed", "Deliverability", "danger"),
        IconSpec("unsubscribe", "Unsubscribe", "Deliverability", "neutral"),
        IconSpec("domain_health", "Domain Health", "Deliverability", "success"),
    ],
    "Contacts & Lists": [
        IconSpec("contact", "Contact", "Contacts & Lists", "neutral"),
        IconSpec("company", "Company", "Contacts & Lists", "neutral"),
        IconSpec("organization", "Organization", "Contacts & Lists", "neutral"),
        IconSpec("email", "Email", "Contacts & Lists", "neutral"),
        IconSpec("phone", "Phone", "Contacts & Lists", "neutral"),
        IconSpec("address", "Address", "Contacts & Lists", "neutral"),
        IconSpec("import", "Import", "Contacts & Lists", "primary"),
        IconSpec("export", "Export", "Contacts & Lists", "primary"),
        IconSpec("add_contact", "Add Contact", "Contacts & Lists", "primary"),
        IconSpec("edit_contact", "Edit Contact", "Contacts & Lists", "neutral"),
        IconSpec("duplicate", "Duplicate", "Contacts & Lists", "neutral"),
        IconSpec("delete", "Delete", "Contacts & Lists", "danger"),
        IconSpec("search", "Search", "Contacts & Lists", "neutral"),
        IconSpec("filter", "Filter", "Contacts & Lists", "neutral"),
        IconSpec("sort", "Sort", "Contacts & Lists", "neutral"),
        IconSpec("tags", "Tags", "Contacts & Lists", "neutral"),
        IconSpec("group", "Group", "Contacts & Lists", "neutral"),
        IconSpec("bulk_edit", "Bulk Edit", "Contacts & Lists", "neutral"),
        IconSpec("verified", "Verified", "Contacts & Lists", "success"),
        IconSpec("unverified", "Unverified", "Contacts & Lists", "neutral"),
        IconSpec("invalid", "Invalid", "Contacts & Lists", "danger"),
        IconSpec("risky", "Risky", "Contacts & Lists", "warning"),
    ],
    "Campaign Analytics": [
        IconSpec("analytics", "Analytics", "Campaign Analytics", "primary"),
        IconSpec("overview", "Overview", "Campaign Analytics", "neutral"),
        IconSpec("opens", "Opens", "Campaign Analytics", "neutral"),
        IconSpec("clicks", "Clicks", "Campaign Analytics", "neutral"),
        IconSpec("replies", "Replies", "Campaign Analytics", "neutral"),
        IconSpec("ctr", "CTR", "Campaign Analytics", "primary"),
        IconSpec("line_chart", "Line Chart", "Campaign Analytics", "primary"),
        IconSpec("bar_chart", "Bar Chart", "Campaign Analytics", "primary"),
        IconSpec("pie_chart", "Pie Chart", "Campaign Analytics", "primary"),
        IconSpec("funnel", "Funnel", "Campaign Analytics", "neutral"),
        IconSpec("calendar", "Calendar", "Campaign Analytics", "neutral"),
        IconSpec("activity", "Activity", "Campaign Analytics", "neutral"),
        IconSpec("trends", "Trends", "Campaign Analytics", "primary"),
        IconSpec("export_report", "Export Report", "Campaign Analytics", "primary"),
    ],
    "AI & Insights": [
        IconSpec("sparkles", "Sparkles", "AI & Insights", "ai"),
        IconSpec("brain", "Brain", "AI & Insights", "ai"),
        IconSpec("recommendation", "Recommendation", "AI & Insights", "ai"),
        IconSpec("optimization", "Optimization", "AI & Insights", "ai"),
        IconSpec("insight", "Insight", "AI & Insights", "warning"),
        IconSpec("auto_fix", "Auto Fix", "AI & Insights", "ai"),
        IconSpec("magic_wand", "Magic Wand", "AI & Insights", "ai"),
        IconSpec("predict", "Predict", "AI & Insights", "ai"),
        IconSpec("analyze", "Analyze", "AI & Insights", "ai"),
        IconSpec("summarize", "Summarize", "AI & Insights", "ai"),
        IconSpec("smart_send", "Smart Send", "AI & Insights", "ai"),
        IconSpec("risk_score", "Risk Score", "AI & Insights", "warning"),
        IconSpec("shield_ai", "Shield AI", "AI & Insights", "success"),
        IconSpec("conversation", "Conversation", "AI & Insights", "neutral"),
        IconSpec("history", "History", "AI & Insights", "neutral"),
        IconSpec("prompt", "Prompt", "AI & Insights", "neutral"),
        IconSpec("generate", "Generate", "AI & Insights", "ai"),
    ],
    "Actions & Controls": [
        IconSpec("new", "Add / New", "Actions & Controls", "primary"),
        IconSpec("edit", "Edit", "Actions & Controls", "neutral"),
        IconSpec("delete", "Delete", "Actions & Controls", "danger"),
        IconSpec("copy", "Copy", "Actions & Controls", "neutral"),
        IconSpec("cut", "Cut", "Actions & Controls", "neutral"),
        IconSpec("paste", "Paste", "Actions & Controls", "neutral"),
        IconSpec("rename", "Rename", "Actions & Controls", "neutral"),
        IconSpec("archive", "Archive", "Actions & Controls", "neutral"),
        IconSpec("restore", "Restore", "Actions & Controls", "neutral"),
        IconSpec("save", "Save", "Actions & Controls", "primary"),
        IconSpec("save_as", "Save As", "Actions & Controls", "primary"),
        IconSpec("download", "Download", "Actions & Controls", "primary"),
        IconSpec("upload", "Upload", "Actions & Controls", "primary"),
        IconSpec("refresh", "Refresh", "Actions & Controls", "neutral"),
        IconSpec("sync", "Sync", "Actions & Controls", "neutral"),
        IconSpec("undo", "Undo", "Actions & Controls", "neutral"),
        IconSpec("redo", "Redo", "Actions & Controls", "neutral"),
        IconSpec("clear", "Clear", "Actions & Controls", "neutral"),
        IconSpec("options", "Options", "Actions & Controls", "neutral"),
    ],
    "Status & Indicators": [
        IconSpec("connected", "Connected", "Status & Indicators", "success"),
        IconSpec("disconnected", "Disconnected", "Status & Indicators", "danger"),
        IconSpec("online", "Online", "Status & Indicators", "success"),
        IconSpec("offline", "Offline", "Status & Indicators", "neutral"),
        IconSpec("healthy", "Healthy", "Status & Indicators", "success"),
        IconSpec("degraded", "Degraded", "Status & Indicators", "warning"),
        IconSpec("critical", "Critical", "Status & Indicators", "danger"),
        IconSpec("pending", "Pending", "Status & Indicators", "neutral"),
        IconSpec("paused", "Paused", "Status & Indicators", "warning"),
        IconSpec("completed", "Completed", "Status & Indicators", "success"),
        IconSpec("cancelled", "Cancelled", "Status & Indicators", "danger"),
        IconSpec("running", "Running", "Status & Indicators", "primary"),
        IconSpec("scheduled", "Scheduled", "Status & Indicators", "primary"),
        IconSpec("queued", "Queued", "Status & Indicators", "primary"),
        IconSpec("idle", "Idle", "Status & Indicators", "neutral"),
        IconSpec("failed", "Failed", "Status & Indicators", "danger"),
    ],
    "UI & Interface": [
        IconSpec("home", "Home", "UI & Interface", "neutral"),
        IconSpec("sidebar", "Sidebar", "UI & Interface", "neutral"),
        IconSpec("layout", "Layout", "UI & Interface", "neutral"),
        IconSpec("panel", "Panel", "UI & Interface", "neutral"),
        IconSpec("card", "Card", "UI & Interface", "neutral"),
        IconSpec("grid", "Grid", "UI & Interface", "neutral"),
        IconSpec("table_view", "Table View", "UI & Interface", "neutral"),
        IconSpec("columns", "Columns", "UI & Interface", "neutral"),
        IconSpec("row", "Row", "UI & Interface", "neutral"),
        IconSpec("close", "Close", "UI & Interface", "neutral"),
        IconSpec("maximize", "Maximize", "UI & Interface", "neutral"),
        IconSpec("minimize", "Minimize", "UI & Interface", "neutral"),
    ],
}

ICONS: dict[str, IconSpec] = {spec.name: spec for specs in ICON_CATEGORIES.values() for spec in specs}

ROUTE_ICONS = {
    "Dashboard": "dashboard",
    "Design System": "grid",
    "Campaigns": "campaigns",
    "Compose": "compose",
    "Templates": "templates",
    "Contacts / Lists": "contacts",
    "SMTP Servers": "smtp_servers",
    "Sending Rules": "sending_rules",
    "Clustering / Reputation Strategy": "dns",
    "Verification": "verification",
    "Sending Queue": "sending_queue",
    "Reports / Logs": "reports",
    "Suppression List": "suppression",
    "Settings": "settings",
}

BUTTON_ICONS = {
    "new": "new",
    "edit": "edit",
    "delete": "delete",
    "archive": "archive",
    "duplicate": "duplicate",
    "copy": "copy",
    "refresh": "refresh",
    "sync": "sync",
    "save": "save",
    "search": "search",
    "export": "export",
    "import": "import",
    "upload": "upload",
    "download": "download",
    "help": "help",
    "test": "test_connection",
    "reputation": "reputation",
    "send": "send",
}

TONE_COLORS = {
    "neutral": "#33475B",
    "primary": "#FF5C35",
    "success": "#00A38D",
    "warning": "#FFB020",
    "danger": "#D94C53",
    "info": "#0091AE",
    "ai": "#6A4FD8",
}

ICON_SENTINEL = "::safesend-icon::"


def all_icons() -> Iterable[IconSpec]:
    return ICONS.values()


def get_route_icon(route: str) -> str:
    return ROUTE_ICONS.get(route, "panel")


def get_button_icon(action: str) -> str:
    return BUTTON_ICONS.get(action, "")


def icon_text(icon_key: str, text: str) -> str:
    icon_name = get_button_icon(icon_key)
    return f"{ICON_SENTINEL}{icon_name}::{text}" if icon_name else text


def parse_icon_text(text: str) -> tuple[str, str]:
    if not isinstance(text, str) or not text.startswith(ICON_SENTINEL):
        return "", text
    payload = text[len(ICON_SENTINEL) :]
    icon_name, _, clean_text = payload.partition("::")
    return icon_name, clean_text


def icon_color(name: str, fallback: str = "#0F172A") -> str:
    spec = ICONS.get(name)
    return TONE_COLORS.get(spec.tone, fallback) if spec else fallback


@lru_cache(maxsize=512)
def icon_image(name: str, *, color: str | None = None, size: int = 20) -> ctk.CTkImage:
    color = color or icon_color(name)
    image = _draw_icon_cached(name, color, size)
    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))


@lru_cache(maxsize=512)
def _draw_icon_cached(name: str, color: str, size: int) -> Image.Image:
    scale = 4
    canvas_size = size * scale
    stroke = max(2, int(round(2 * scale)))
    image = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    def p(value: float) -> int:
        return int(round(value / 24 * canvas_size))

    def line(points: list[tuple[float, float]]) -> None:
        draw.line([(p(x), p(y)) for x, y in points], fill=color, width=stroke, joint="curve")

    def rect(x1: float, y1: float, x2: float, y2: float, radius: float = 2) -> None:
        draw.rounded_rectangle((p(x1), p(y1), p(x2), p(y2)), radius=p(radius), outline=color, width=stroke)

    def fill_rect(x1: float, y1: float, x2: float, y2: float, radius: float = 2) -> None:
        draw.rounded_rectangle((p(x1), p(y1), p(x2), p(y2)), radius=p(radius), fill=color)

    def oval(x1: float, y1: float, x2: float, y2: float) -> None:
        draw.ellipse((p(x1), p(y1), p(x2), p(y2)), outline=color, width=stroke)

    def fill_oval(x1: float, y1: float, x2: float, y2: float) -> None:
        draw.ellipse((p(x1), p(y1), p(x2), p(y2)), fill=color)

    def arc(x1: float, y1: float, x2: float, y2: float, start: int, end: int) -> None:
        draw.arc((p(x1), p(y1), p(x2), p(y2)), start=start, end=end, fill=color, width=stroke)

    def check() -> None:
        line([(7, 12), (10.5, 15.5), (17, 8.5)])

    def x_mark() -> None:
        line([(8, 8), (16, 16)])
        line([(16, 8), (8, 16)])

    def plus() -> None:
        line([(12, 5), (12, 19)])
        line([(5, 12), (19, 12)])

    def arrow_down() -> None:
        line([(12, 4), (12, 16), (8, 12)])
        line([(12, 16), (16, 12)])
        line([(5, 20), (19, 20)])

    def arrow_up() -> None:
        line([(12, 20), (12, 8), (8, 12)])
        line([(12, 8), (16, 12)])
        line([(5, 4), (19, 4)])

    def shield(with_check: bool = False) -> None:
        pts = [(12, 3), (19, 6), (18, 14), (12, 21), (6, 14), (5, 6)]
        draw.line([(p(x), p(y)) for x, y in pts + [pts[0]]], fill=color, width=stroke, joint="curve")
        if with_check:
            check()

    def envelope() -> None:
        rect(4, 6, 20, 18, 2)
        line([(5, 8), (12, 13), (19, 8)])

    if name in {"new", "add_contact"}:
        plus()
    elif name in {"delete", "trash"}:
        rect(7, 8, 17, 20, 1.5)
        line([(6, 8), (18, 8)])
        line([(9, 8), (10, 5), (14, 5), (15, 8)])
        line([(10, 11), (10, 17)])
        line([(14, 11), (14, 17)])
    elif name in {"edit", "compose", "signature", "edit_contact", "rename", "bulk_edit"}:
        rect(5, 5, 17, 19, 2)
        line([(10, 15), (18.5, 6.5)])
        line([(16, 5), (19, 8)])
    elif name in {"copy", "duplicate"}:
        rect(8, 8, 19, 19, 2)
        rect(5, 5, 16, 16, 2)
    elif name in {"archive"}:
        rect(5, 7, 19, 19, 2)
        line([(5, 10), (19, 10)])
        line([(12, 12), (12, 17), (9, 14)])
        line([(12, 17), (15, 14)])
    elif name in {"save", "save_as"}:
        rect(5, 4, 19, 20, 2)
        fill_rect(8, 5.5, 15, 9, 1)
        rect(8, 14, 16, 20, 1)
    elif name in {"download", "import"}:
        arrow_down()
    elif name in {"upload", "export", "export_report"}:
        arrow_up()
    elif name in {"refresh", "sync", "rotation", "retry"}:
        arc(5, 5, 19, 19, 40, 320)
        line([(18, 5), (19, 10), (14, 9)])
    elif name in {"search"}:
        oval(5, 5, 15, 15)
        line([(14, 14), (20, 20)])
    elif name in {"filter", "funnel"}:
        line([(5, 6), (19, 6), (14, 12), (14, 18), (10, 20), (10, 12), (5, 6)])
    elif name in {"sort"}:
        line([(8, 5), (8, 19), (5, 16)])
        line([(8, 19), (11, 16)])
        line([(16, 19), (16, 5), (13, 8)])
        line([(16, 5), (19, 8)])
    elif name in {"dashboard", "grid", "overview"}:
        for x in (5, 14):
            for y in (5, 14):
                rect(x, y, x + 5, y + 5, 1)
    elif name in {"campaigns", "templates", "box"}:
        rect(5, 7, 19, 18, 2)
        line([(5, 9), (12, 4), (19, 9)])
        line([(12, 4), (12, 15)])
    elif name in {"contacts", "contact", "smtp_user", "user_profile"}:
        oval(8, 4, 16, 12)
        arc(5, 11, 19, 23, 205, 335)
    elif name in {"lists", "queue", "sending_queue", "reports", "subject"}:
        for y in (7, 12, 17):
            fill_oval(5, y - 1, 7, y + 1)
            line([(10, y), (19, y)])
    elif name in {"smtp_servers", "server", "mx_record"}:
        for y in (5, 11, 17):
            rect(5, y, 19, y + 4, 1.5)
            fill_oval(16, y + 1.2, 17.6, y + 2.8)
    elif name in {"sending_rules", "sliders", "rate_limit"}:
        line([(5, 7), (19, 7)])
        line([(5, 12), (19, 12)])
        line([(5, 17), (19, 17)])
        fill_oval(9, 5.5, 12, 8.5)
        fill_oval(14, 10.5, 17, 13.5)
        fill_oval(7, 15.5, 10, 18.5)
    elif name in {"dns", "clustering", "threads", "group", "organization"}:
        for cx, cy in ((12, 5), (6, 17), (18, 17)):
            oval(cx - 2, cy - 2, cx + 2, cy + 2)
        line([(10, 7), (7, 15)])
        line([(14, 7), (17, 15)])
        line([(8, 17), (16, 17)])
    elif name in {"verification", "deliverability", "deliverability_score", "reputation", "shield_ai", "healthy", "spf", "dkim", "dmarc"}:
        shield(True)
    elif name in {"suppression", "blacklist", "blocked", "cancelled", "disconnected"}:
        oval(5, 5, 19, 19)
        line([(7, 17), (17, 7)])
    elif name in {"settings", "options"}:
        oval(8, 8, 16, 16)
        for x1, y1, x2, y2 in [(12, 3, 12, 6), (12, 18, 12, 21), (3, 12, 6, 12), (18, 12, 21, 12), (5, 5, 7, 7), (17, 17, 19, 19), (19, 5, 17, 7), (7, 17, 5, 19)]:
            line([(x1, y1), (x2, y2)])
    elif name in {"help", "question"}:
        oval(5, 5, 19, 19)
        draw.text((p(9), p(5.2)), "?", fill=color)
    elif name in {"warning", "degraded", "risky"}:
        pts = [(12, 4), (21, 20), (3, 20), (12, 4)]
        draw.line([(p(x), p(y)) for x, y in pts], fill=color, width=stroke, joint="curve")
        line([(12, 9), (12, 14)])
        fill_oval(11.2, 16.5, 12.8, 18.1)
    elif name in {"success", "connected", "online", "completed", "verified", "test_connection", "health_check"}:
        oval(5, 5, 19, 19)
        check()
    elif name in {"error", "failed", "critical", "invalid"}:
        oval(5, 5, 19, 19)
        x_mark()
    elif name in {"info"}:
        oval(5, 5, 19, 19)
        line([(12, 11), (12, 17)])
        fill_oval(11, 7, 13, 9)
    elif name in {"ai_assistant", "sparkles", "magic_wand", "recommendation", "optimization", "generate", "auto_fix"}:
        line([(12, 3), (13.5, 9), (20, 12), (13.5, 15), (12, 21), (10.5, 15), (4, 12), (10.5, 9), (12, 3)])
        line([(5, 5), (8, 8)])
        line([(19, 5), (16, 8)])
    elif name in {"analytics", "line_chart", "trends", "activity"}:
        line([(4, 19), (4, 5)])
        line([(4, 19), (20, 19)])
        line([(6, 16), (10, 12), (14, 14), (19, 7)])
    elif name in {"bar_chart"}:
        for idx, h in enumerate((8, 13, 6)):
            fill_rect(6 + idx * 5, 20 - h, 9 + idx * 5, 20, 1)
    elif name in {"pie_chart"}:
        oval(5, 5, 19, 19)
        line([(12, 12), (12, 5)])
        line([(12, 12), (18, 16)])
    elif name in {"calendar", "scheduled"}:
        rect(5, 6, 19, 20, 2)
        line([(5, 10), (19, 10)])
        line([(9, 4), (9, 8)])
        line([(15, 4), (15, 8)])
    elif name in {"phone"}:
        line([(8, 5), (6, 7), (8, 14), (14, 20), (17, 18), (15, 15)])
    elif name in {"address", "placement"}:
        oval(7, 4, 17, 14)
        fill_oval(11, 8, 13, 10)
        line([(12, 14), (12, 21)])
    elif name in {"email", "inbox", "outbox", "drafts", "preheader", "send"}:
        envelope()
        if name == "send":
            line([(5, 19), (19, 5), (15, 18), (11, 13), (5, 19)])
    elif name in {"globe", "domain"}:
        oval(4, 4, 20, 20)
        line([(4, 12), (20, 12)])
        line([(12, 4), (12, 20)])
        arc(7, 4, 17, 20, 90, 270)
        arc(7, 4, 17, 20, 270, 90)
    elif name in {"connection", "link"}:
        arc(4, 8, 13, 17, 90, 270)
        arc(11, 8, 20, 17, 270, 90)
        line([(9, 12), (15, 12)])
    elif name in {"authentication", "password", "tls_ssl", "lock"}:
        rect(6, 10, 18, 20, 2)
        arc(8, 4, 16, 14, 180, 360)
    elif name in {"more"}:
        for x in (7, 12, 17):
            fill_oval(x - 1.4, 11 - 1.4, x + 1.4, 11 + 1.4)
    else:
        rect(5, 5, 19, 19, 3)
        line([(8, 12), (16, 12)])

    return image.resize((size, size), Image.Resampling.LANCZOS)
