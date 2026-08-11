from app.database import db


DEFAULT_RULES = {
    "send_rate": "",
    "delay_between_emails": "",
    "max_per_hour": "",
    "max_per_day": "",
    "business_hours": "",
    "quiet_hours": "",
}


class CampaignRulesService:
    def get_rules(self, campaign_id: int) -> dict:
        row = db.fetch_one("SELECT * FROM campaign_rules WHERE campaign_id = ?", (campaign_id,))
        if not row:
            return {"campaign_id": campaign_id, **DEFAULT_RULES}
        result = dict(row)
        for key, value in DEFAULT_RULES.items():
            result.setdefault(key, value)
        return result

    def save_rules(self, campaign_id: int, values: dict) -> None:
        db.execute(
            """
            INSERT INTO campaign_rules (
                campaign_id, send_rate, delay_between_emails, max_per_hour, max_per_day,
                business_hours, quiet_hours, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(campaign_id) DO UPDATE SET
                send_rate = excluded.send_rate,
                delay_between_emails = excluded.delay_between_emails,
                max_per_hour = excluded.max_per_hour,
                max_per_day = excluded.max_per_day,
                business_hours = excluded.business_hours,
                quiet_hours = excluded.quiet_hours,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                campaign_id,
                values.get("send_rate", ""),
                values.get("delay_between_emails", ""),
                values.get("max_per_hour", ""),
                values.get("max_per_day", ""),
                values.get("business_hours", ""),
                values.get("quiet_hours", ""),
            ),
        )
