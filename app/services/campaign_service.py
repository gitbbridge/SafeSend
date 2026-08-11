from app.database import db
from app.models.campaign import Campaign


class CampaignService:
    def list_campaigns(self, search: str = "", include_archived: bool = False) -> list[dict]:
        clauses = []
        params: list[object] = []
        if not include_archived:
            clauses.append("campaigns.archived = 0")
        if search.strip():
            clauses.append("(campaigns.name LIKE ? OR campaigns.tags LIKE ? OR templates.name LIKE ? OR contact_lists.name LIKE ?)")
            like = f"%{search.strip()}%"
            params.extend([like, like, like, like])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = db.fetch_all(
            f"""
            SELECT campaigns.*,
                   contact_lists.name AS list_name,
                   templates.name AS template_name,
                   smtp_profiles.profile_name AS smtp_profile_name,
                   (
                       SELECT COUNT(*)
                       FROM contacts
                       WHERE contacts.list_id = campaigns.contact_list_id
                   ) AS recipient_count
            FROM campaigns
            LEFT JOIN contact_lists ON contact_lists.id = campaigns.contact_list_id
            LEFT JOIN templates ON templates.id = campaigns.template_id
            LEFT JOIN smtp_profiles ON smtp_profiles.id = campaigns.smtp_profile_id
            {where}
            ORDER BY campaigns.updated_at DESC, campaigns.created_at DESC
            """,
            params,
        )
        return [dict(row) for row in rows]

    def get_campaign(self, campaign_id: int) -> dict | None:
        row = db.fetch_one("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        return dict(row) if row else None

    def create_campaign(self, name: str = "Untitled Campaign") -> int:
        return db.execute(
            """
            INSERT INTO campaigns (name, subject, status)
            VALUES (?, '', 'Draft')
            """,
            (self._unique_name(name),),
        )

    def save_builder(self, values: dict, campaign_id: int | None = None) -> int:
        name = (values.get("name") or "").strip()
        if not name:
            raise ValueError("Campaign name is required.")
        subject = values.get("subject", "")
        html_body = values.get("html_body", "")
        params = (
            name,
            values.get("description", "").strip(),
            values.get("tags", "").strip(),
            values.get("internal_notes", "").strip(),
            subject,
            html_body,
            values.get("plain_text_body", ""),
            values.get("contact_list_id"),
            values.get("template_id"),
            values.get("smtp_profile_id"),
            values.get("smtp_pool", ""),
            values.get("attachments", ""),
            values.get("footer_text", ""),
            values.get("status", "Draft"),
            values.get("scheduled_at", ""),
        )
        if campaign_id:
            db.execute(
                """
                UPDATE campaigns
                SET name = ?, description = ?, tags = ?, internal_notes = ?, subject = ?,
                    html_body = ?, plain_text_body = ?, contact_list_id = ?, template_id = ?,
                    smtp_profile_id = ?, smtp_pool = ?, attachments = ?, footer_text = ?,
                    status = ?, scheduled_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*params, campaign_id),
            )
            self._sync_campaign_links(campaign_id, values.get("contact_list_id"), values.get("template_id"))
            return campaign_id
        new_id = db.execute(
            """
            INSERT INTO campaigns (
                name, description, tags, internal_notes, subject, html_body, plain_text_body,
                contact_list_id, template_id, smtp_profile_id, smtp_pool, attachments,
                footer_text, status, scheduled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            params,
        )
        self._sync_campaign_links(new_id, values.get("contact_list_id"), values.get("template_id"))
        return new_id

    def save_campaign(self, campaign: Campaign) -> int:
        return self.save_builder(
            {
                "name": campaign.name,
                "subject": campaign.subject,
                "html_body": campaign.html_body,
                "plain_text_body": campaign.plain_text_body,
                "contact_list_id": campaign.contact_list_id,
                "smtp_pool": campaign.smtp_pool,
                "attachments": campaign.attachments,
                "footer_text": campaign.footer_text,
                "status": campaign.status,
                "scheduled_at": campaign.scheduled_at,
            },
            campaign.id,
        )

    def duplicate_campaign(self, campaign_id: int) -> int:
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign was not found.")
        rules = db.fetch_one("SELECT * FROM campaign_rules WHERE campaign_id = ?", (campaign_id,))
        new_id = self.save_builder(
            {
                "name": self._unique_name(f"{campaign['name']} Copy"),
                "description": campaign.get("description") or "",
                "tags": campaign.get("tags") or "",
                "internal_notes": campaign.get("internal_notes") or "",
                "subject": campaign.get("subject") or "",
                "html_body": campaign.get("html_body") or "",
                "plain_text_body": campaign.get("plain_text_body") or "",
                "contact_list_id": campaign.get("contact_list_id"),
                "template_id": campaign.get("template_id"),
                "smtp_profile_id": campaign.get("smtp_profile_id"),
                "smtp_pool": campaign.get("smtp_pool") or "",
                "attachments": campaign.get("attachments") or "",
                "footer_text": campaign.get("footer_text") or "",
                "status": "Draft",
                "scheduled_at": "",
            }
        )
        if rules:
            db.execute(
                """
                INSERT OR REPLACE INTO campaign_rules (
                    campaign_id, send_rate, delay_between_emails, max_per_hour, max_per_day,
                    business_hours, quiet_hours
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id,
                    rules["send_rate"],
                    rules["delay_between_emails"],
                    rules["max_per_hour"],
                    rules["max_per_day"],
                    rules["business_hours"],
                    rules["quiet_hours"],
                ),
            )
        return new_id

    def delete_campaign(self, campaign_id: int) -> None:
        db.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))

    def archive_campaign(self, campaign_id: int, archived: bool = True) -> None:
        db.execute(
            """
            UPDATE campaigns
            SET archived = ?, status = CASE WHEN ? = 1 THEN 'Archived' ELSE status END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if archived else 0, 1 if archived else 0, campaign_id),
        )

    def mark_ready(self, campaign_id: int) -> None:
        db.execute("UPDATE campaigns SET status = 'Ready', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (campaign_id,))

    def mark_draft(self, campaign_id: int) -> None:
        db.execute("UPDATE campaigns SET status = 'Draft', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (campaign_id,))

    def _sync_campaign_links(self, campaign_id: int, contact_list_id: int | None, template_id: int | None) -> None:
        db.execute("DELETE FROM campaign_lists WHERE campaign_id = ?", (campaign_id,))
        if contact_list_id:
            db.execute(
                "INSERT OR IGNORE INTO campaign_lists (campaign_id, contact_list_id) VALUES (?, ?)",
                (campaign_id, contact_list_id),
            )
        if template_id:
            db.execute(
                """
                INSERT INTO campaign_templates (campaign_id, template_id, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(campaign_id) DO UPDATE SET template_id = excluded.template_id, updated_at = CURRENT_TIMESTAMP
                """,
                (campaign_id, template_id),
            )

    def _unique_name(self, name: str) -> str:
        base = (name or "Untitled Campaign").strip()
        candidate = base
        idx = 2
        while db.fetch_one("SELECT id FROM campaigns WHERE name = ?", (candidate,)):
            candidate = f"{base} {idx}"
            idx += 1
        return candidate
