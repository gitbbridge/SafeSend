from app.database import db


class SignatureService:
    def list_signatures(self, include_archived: bool = False) -> list[dict]:
        where = "" if include_archived else "WHERE archived = 0"
        rows = db.fetch_all(f"SELECT * FROM signatures {where} ORDER BY is_default DESC, name ASC")
        return [dict(row) for row in rows]

    def get_signature(self, signature_id: int) -> dict | None:
        row = db.fetch_one("SELECT * FROM signatures WHERE id = ?", (signature_id,))
        return dict(row) if row else None

    def save_signature(self, name: str, html_body: str, plain_text_body: str = "", is_default: bool = False, signature_id: int | None = None) -> int:
        name = name.strip()
        if not name:
            raise ValueError("Signature name is required.")
        if is_default:
            db.execute("UPDATE signatures SET is_default = 0")
        if signature_id:
            db.execute(
                """
                UPDATE signatures
                SET name = ?, html_body = ?, plain_text_body = ?, is_default = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, html_body, plain_text_body, 1 if is_default else 0, signature_id),
            )
            return signature_id
        return db.execute(
            "INSERT INTO signatures (name, html_body, plain_text_body, is_default) VALUES (?, ?, ?, ?)",
            (name, html_body, plain_text_body, 1 if is_default else 0),
        )

    def archive_signature(self, signature_id: int) -> None:
        db.execute("UPDATE signatures SET archived = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (signature_id,))

    def default_signature(self) -> dict | None:
        row = db.fetch_one("SELECT * FROM signatures WHERE is_default = 1 AND archived = 0 ORDER BY updated_at DESC LIMIT 1")
        return dict(row) if row else None
