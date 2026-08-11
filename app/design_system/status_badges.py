from tkinter import ttk


STATUS_LEVELS = {
    "pass": "Success.TLabel",
    "success": "Success.TLabel",
    "ready": "Success.TLabel",
    "healthy": "Success.TLabel",
    "connected": "Success.TLabel",
    "verified": "Success.TLabel",
    "completed": "Success.TLabel",
    "warning": "Warning.TLabel",
    "unknown": "Warning.TLabel",
    "queued": "Info.TLabel",
    "running": "Info.TLabel",
    "sending": "Info.TLabel",
    "paused": "Orange.TLabel",
    "disconnected": "Danger.TLabel",
    "failed": "Danger.TLabel",
    "error": "Danger.TLabel",
    "suppressed": "Danger.TLabel",
}

STATUS_HELP = {
    "healthy": "Healthy means the item is currently in a good operational state, but it should still be monitored over time.",
    "paused": "Paused means activity is intentionally stopped. Review the reason before resuming.",
    "verified": "Verified means the contact or setting has passed the relevant validation check.",
    "risky": "Risky means SafeSend found signals that deserve caution before sending.",
    "suppressed": "Suppressed means SafeSend should avoid future sends to this recipient or domain.",
    "sending": "Sending means work is actively in progress and should be monitored for failures.",
    "completed": "Completed means the workflow finished its current operation.",
    "failed": "Failed means SafeSend could not complete the operation. Review the error before retrying.",
    "queued": "Queued means work is prepared but has not been sent or processed yet.",
    "unknown": "Unknown means SafeSend does not have enough information to consider the item safe.",
}


def configure_status_badge_styles(style: ttk.Style, theme) -> None:
    palette = theme.palette
    typo = theme.typography
    for name, color in {
        "Success": palette.success,
        "Warning": palette.warning,
        "Orange": palette.orange,
        "Danger": palette.danger,
        "Info": palette.info,
    }.items():
        style.configure(f"{name}.TLabel", background=palette.surface, foreground=color, font=(typo.family_semibold, typo.status_badge))


def status_style(level: str) -> str:
    return STATUS_LEVELS.get((level or "").strip().lower(), "Muted.TLabel")


def status_help(level: str) -> str:
    return STATUS_HELP.get((level or "").strip().lower(), "This status indicates the current state of the item.")
