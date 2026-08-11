from app.database import db
from app.utils.validators import is_valid_email, normalize_email


class SuppressionService:
    def add(
        self,
        email: str,
        reason: str = "",
        scope: str = "Global",
        campaign_id: int | None = None,
        validate: bool = True,
        source: str = "manual",
        message_id: str | None = None,
    ) -> bool:
        normalized = normalize_email(email)
        if validate and not is_valid_email(normalized):
            return False
        if not normalized:
            return False
        db.execute(
            """
            INSERT INTO suppression_list (
                email, normalized_email, reason, scope, campaign_id, source, message_id, active, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(email) DO UPDATE SET
                normalized_email = excluded.normalized_email,
                reason = excluded.reason,
                scope = excluded.scope,
                campaign_id = excluded.campaign_id,
                source = excluded.source,
                message_id = excluded.message_id,
                active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (normalized, normalized, reason, scope, campaign_id, source, message_id),
        )
        return True

    def remove(self, email: str) -> None:
        db.execute(
            "UPDATE suppression_list SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE normalized_email = ? OR email = ?",
            (normalize_email(email), normalize_email(email)),
        )

    def emails(self) -> set[str]:
        return {
            row["normalized_email"] or row["email"]
            for row in db.fetch_all("SELECT email, normalized_email FROM suppression_list WHERE active = 1")
        }

    def is_suppressed(self, email: str) -> bool:
        normalized = normalize_email(email)
        row = db.fetch_one(
            """
            SELECT id FROM suppression_list
            WHERE active = 1 AND (normalized_email = ? OR email = ?)
            """,
            (normalized, normalized),
        )
        return row is not None

    def list_entries(self) -> list[dict]:
        return [dict(row) for row in db.fetch_all("SELECT * FROM suppression_list ORDER BY created_at DESC")]
