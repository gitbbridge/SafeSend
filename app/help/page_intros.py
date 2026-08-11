PAGE_INTROS = {
    "Dashboard": "Your command center for SafeSend. Use this page to understand overall sending readiness, contact volume, SMTP health, queue state, and recent activity before you make operational decisions.",
    "Campaigns": "Build and preflight campaigns here. SafeSend encourages conservative pacing, verified contacts, compliant content, and reviewed infrastructure before any campaign becomes ready.",
    "Compose": "Create reusable email templates, subjects, signatures, and merge previews. Good templates are clear, compliant, easy to read, and safe for deliverability.",
    "Contacts / Lists": "Manage recipient databases, imports, suppressions, verification status, and exports. Healthy lists reduce bounces, protect reputation, and keep sending compliant.",
    "SMTP Servers": "Configure SMTP profiles, test connectivity, and review reputation signals. Conservative limits and clean authentication protect sender reputation.",
    "Sending Rules": "Set pacing, quiet hours, and compliance defaults. These controls help SafeSend send like a careful human-operated system rather than a risky burst sender.",
    "Clustering / Reputation Strategy": "Analyze recipient infrastructure and group similar destinations. Clustering helps avoid overloading one provider or reputation pool.",
    "Verification": "Connect verification providers and review deliverability categories. Verification helps avoid invalid, risky, or unknown contacts before sending.",
    "Sending Queue": "Prepare and review queued recipients before sending. Queue review helps catch pacing, suppression, verification, and campaign readiness issues early.",
    "Reports / Logs": "Review outcomes and operational history. Reports help you learn from delivery patterns, failures, suppressions, and future optimization opportunities.",
    "Suppression List": "Maintain addresses and domains that must not be contacted. Suppression protects compliance, brand trust, and deliverability.",
    "Settings": "Manage local application configuration, learning mode, folders, and stored settings. Keep these values understandable and conservative.",
}


def get_page_intro(page: str) -> str:
    return PAGE_INTROS.get(page, "This page includes SafeSend configuration and operational controls. Review recommendations before changing values.")

