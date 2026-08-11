from app.database import db


class DraftService:
    def save_draft(self, values: dict, template_id: int | None = None) -> int:
        return db.execute(
            """
            INSERT INTO drafts (
                template_id, name, subject, preheader, from_name, from_email, reply_to_email,
                html_body, plain_text_body, source_mode
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                template_id,
                values.get("name", ""),
                values.get("subject", ""),
                values.get("preheader", ""),
                values.get("from_name", ""),
                values.get("from_email", ""),
                values.get("reply_to_email", ""),
                values.get("html_body", ""),
                values.get("plain_text_body", ""),
                1 if values.get("source_mode") else 0,
            ),
        )

    def latest_draft(self, template_id: int | None = None) -> dict | None:
        if template_id:
            row = db.fetch_one("SELECT * FROM drafts WHERE template_id = ? ORDER BY saved_at DESC LIMIT 1", (template_id,))
        else:
            row = db.fetch_one("SELECT * FROM drafts ORDER BY saved_at DESC LIMIT 1")
        return dict(row) if row else None

    def list_drafts(self, template_id: int | None = None) -> list[dict]:
        if template_id:
            rows = db.fetch_all("SELECT * FROM drafts WHERE template_id = ? ORDER BY saved_at DESC LIMIT 50", (template_id,))
        else:
            rows = db.fetch_all("SELECT * FROM drafts ORDER BY saved_at DESC LIMIT 50")
        return [dict(row) for row in rows]

    def get_draft(self, draft_id: int) -> dict | None:
        row = db.fetch_one("SELECT * FROM drafts WHERE id = ?", (draft_id,))
        return dict(row) if row else None
