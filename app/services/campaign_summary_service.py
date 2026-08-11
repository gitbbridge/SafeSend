from app.database import db
from app.services.campaign_rules_service import CampaignRulesService


class CampaignSummaryService:
    def summary(self, campaign_id: int) -> dict:
        campaign = db.fetch_one(
            """
            SELECT campaigns.*, contact_lists.name AS contact_list_name,
                   templates.name AS template_name, templates.preheader AS template_preheader,
                   smtp_profiles.profile_name AS smtp_profile_name
            FROM campaigns
            LEFT JOIN contact_lists ON contact_lists.id = campaigns.contact_list_id
            LEFT JOIN templates ON templates.id = campaigns.template_id
            LEFT JOIN smtp_profiles ON smtp_profiles.id = campaigns.smtp_profile_id
            WHERE campaigns.id = ?
            """,
            (campaign_id,),
        )
        if not campaign:
            raise ValueError("Campaign was not found.")
        list_id = campaign["contact_list_id"]
        stats = self.contact_stats(list_id) if list_id else self.empty_stats()
        return {
            "campaign": self._campaign_dict(campaign),
            "rules": CampaignRulesService().get_rules(campaign_id),
            "contacts": stats,
        }

    def contact_stats(self, list_id: int) -> dict:
        stats = self.empty_stats()
        total = db.fetch_one("SELECT COUNT(*) AS total FROM contacts WHERE list_id = ?", (list_id,))
        stats["total"] = int(total["total"]) if total else 0
        suppression_rows = db.fetch_all(
            """
            SELECT contacts.email, contacts.verification_status,
                   CASE WHEN contacts.is_suppressed = 1 OR suppression_list.id IS NOT NULL THEN 1 ELSE 0 END AS suppressed
            FROM contacts
            LEFT JOIN suppression_list ON suppression_list.email = contacts.email
            WHERE contacts.list_id = ?
            """,
            (list_id,),
        )
        seen: set[str] = set()
        duplicate_emails: set[str] = set()
        for row in suppression_rows:
            email = row["email"]
            if email in seen:
                duplicate_emails.add(email)
            seen.add(email)
            status = row["verification_status"] or "Unknown"
            key = status if status in {"Deliverable", "Risky", "Unknown", "Undeliverable"} else "Unknown"
            stats[key] += 1
            if row["suppressed"]:
                stats["suppressed"] += 1
        stats["duplicates"] = len(duplicate_emails)
        stats["estimated_send_count"] = max(0, stats["total"] - stats["suppressed"] - stats["duplicates"])
        return stats

    def empty_stats(self) -> dict:
        return {
            "total": 0,
            "suppressed": 0,
            "duplicates": 0,
            "Deliverable": 0,
            "Risky": 0,
            "Unknown": 0,
            "Undeliverable": 0,
            "estimated_send_count": 0,
        }

    def _campaign_dict(self, row) -> dict:
        data = dict(row)
        data["template_name"] = data.get("template_name") or ""
        data["smtp_profile_name"] = data.get("smtp_profile_name") or ""
        data["contact_list_name"] = data.get("contact_list_name") or ""
        return data
