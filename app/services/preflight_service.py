import re

from app.database import db
from app.services.campaign_summary_service import CampaignSummaryService

MERGE_FIELD_RE = re.compile(r"{{\s*([A-Za-z0-9_]+)\s*}}")
ALLOWED_MERGE_FIELDS = {
    "FirstName",
    "LastName",
    "Company",
    "Email",
    "State",
    "City",
    "Custom1",
    "Custom2",
    "Custom3",
    "Unsubscribe",
    "first_name",
    "last_name",
    "company",
    "email",
    "state",
    "city",
    "custom1",
    "custom2",
    "custom3",
}


class PreflightService:
    def run(self, campaign_id: int) -> dict:
        summary = CampaignSummaryService().summary(campaign_id)
        campaign = summary["campaign"]
        stats = summary["contacts"]
        checks = []

        self._check(checks, bool((campaign.get("name") or "").strip()), "Campaign name exists", "Campaign name is required.")
        self._check(checks, bool(campaign.get("contact_list_id")), "Contact list selected", "Choose a contact list.")
        self._check(checks, stats["estimated_send_count"] > 0, "Recipient count greater than zero", "Estimated send count must be greater than zero.")
        self._check(checks, bool(campaign.get("template_id")), "Template selected", "Choose a template.")
        self._check(checks, bool((campaign.get("subject") or "").strip()), "Subject exists", "Template subject is required.")
        self._check(checks, bool((campaign.get("html_body") or campaign.get("plain_text_body") or "").strip()), "Body exists", "Template body is required.")
        self._check(checks, bool(campaign.get("smtp_profile_id")), "SMTP profile selected", "Choose an SMTP profile.")

        smtp = self._smtp(campaign.get("smtp_profile_id"))
        if smtp:
            if smtp.get("last_test_status") in {"Success", "Not tested", "", None}:
                checks.append(self._item("warning" if smtp.get("last_test_status") != "Success" else "pass", "SMTP profile test status", "SMTP has not been successfully tested yet." if smtp.get("last_test_status") != "Success" else "SMTP test status is successful."))
            else:
                checks.append(self._item("error", "SMTP profile test status", f"SMTP last test failed: {smtp.get('last_error') or smtp.get('last_test_status')}"))
            self._check(checks, bool((smtp.get("from_email") or "").strip()), "No empty from email", "SMTP profile from email is required.")
            self._check(checks, bool((smtp.get("reply_to_email") or "").strip()), "No empty reply-to email", "SMTP profile reply-to email is required.")
        elif campaign.get("smtp_profile_id"):
            checks.append(self._item("error", "SMTP profile selected", "Selected SMTP profile was not found."))

        unknown_tags = self._invalid_merge_fields(campaign)
        self._check(checks, not unknown_tags, "No invalid merge fields", "Invalid merge fields: " + ", ".join(unknown_tags) if unknown_tags else "")
        self._check(checks, stats["suppressed"] == 0, "No suppressed recipients included", f"{stats['suppressed']} suppressed recipients are in this list.")
        self._check(checks, stats["duplicates"] == 0, "No duplicate recipients", f"{stats['duplicates']} duplicate recipient emails detected.")
        body = f"{campaign.get('html_body') or ''} {campaign.get('plain_text_body') or ''}".lower()
        if "unsubscribe" not in body and "{{unsubscribe" not in body:
            checks.append(self._item("warning", "Unsubscribe/footer placeholder", "No unsubscribe/footer placeholder was found."))

        errors = sum(1 for item in checks if item["level"] == "error")
        warnings = sum(1 for item in checks if item["level"] == "warning")
        return {"checks": checks, "errors": errors, "warnings": warnings, "can_mark_ready": errors == 0}

    def _smtp(self, smtp_profile_id: int | None) -> dict | None:
        if not smtp_profile_id:
            return None
        row = db.fetch_one("SELECT * FROM smtp_profiles WHERE id = ?", (smtp_profile_id,))
        return dict(row) if row else None

    def _invalid_merge_fields(self, campaign: dict) -> list[str]:
        content = " ".join([campaign.get("subject") or "", campaign.get("html_body") or "", campaign.get("plain_text_body") or ""])
        return sorted({field for field in MERGE_FIELD_RE.findall(content) if field not in ALLOWED_MERGE_FIELDS})

    def _check(self, checks: list[dict], passed: bool, label: str, message: str) -> None:
        checks.append(self._item("pass" if passed else "error", label, "Passed." if passed else message))

    def _item(self, level: str, label: str, message: str) -> dict:
        return {"level": level, "label": label, "message": message}
