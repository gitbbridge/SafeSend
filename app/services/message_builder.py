from __future__ import annotations

from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from app.database import db


class MessageBuilder:
    def ensure_message_id(self, send_job_id: int, campaign_id: int, recipient_email: str, smtp_profile: dict, sending_domain_id: int | None) -> str:
        existing = db.fetch_one("SELECT message_id FROM send_jobs WHERE id = ?", (send_job_id,))
        if existing and existing["message_id"]:
            return str(existing["message_id"])
        from_domain = (smtp_profile.get("from_email") or "safesend.local").split("@")[-1]
        message_id = make_msgid(domain=from_domain)
        db.execute(
            """
            UPDATE send_jobs SET message_id = ? WHERE id = ?
            """,
            (message_id, send_job_id),
        )
        db.execute(
            """
            INSERT OR IGNORE INTO message_registry (
                campaign_id, send_job_id, message_id, recipient_email, smtp_account_id, sending_domain_id
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (campaign_id, send_job_id, message_id, recipient_email, smtp_profile["id"], sending_domain_id),
        )
        return message_id

    def build(self, campaign: dict, job: dict, smtp_profile: dict, message_id: str) -> EmailMessage:
        message = EmailMessage()
        from_email = smtp_profile.get("from_email") or ""
        from_name = smtp_profile.get("from_name") or ""
        message["From"] = formataddr((from_name, from_email)) if from_name else from_email
        message["To"] = job["email"]
        message["Subject"] = campaign.get("subject") or ""
        if smtp_profile.get("reply_to_email"):
            message["Reply-To"] = smtp_profile["reply_to_email"]
        message["Message-ID"] = message_id
        plain_text = campaign.get("plain_text_body") or ""
        html = campaign.get("html_body") or ""
        if html:
            message.set_content(plain_text or self._html_to_plain(html))
            message.add_alternative(html, subtype="html")
        else:
            message.set_content(plain_text)
        return message

    def mark_sent(self, message_id: str) -> None:
        db.execute("UPDATE message_registry SET sent_at = CURRENT_TIMESTAMP WHERE message_id = ?", (message_id,))

    def _html_to_plain(self, html: str) -> str:
        return html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
