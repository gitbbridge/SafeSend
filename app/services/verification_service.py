import json
import urllib.parse
import urllib.request
import urllib.error

from app.database import db


class VerificationService:
    def settings_key(self) -> str:
        row = db.fetch_one("SELECT value FROM app_settings WHERE key = 'emailable_api_key'")
        return row["value"] if row else ""

    def save_api_key(self, api_key: str) -> None:
        db.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES ('emailable_api_key', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """,
            (api_key.strip(),),
        )

    def verify_contact(self, contact_id: int) -> tuple[str, str]:
        api_key = self.settings_key()
        contact = db.fetch_one("SELECT email FROM contacts WHERE id = ?", (contact_id,))
        if not contact:
            return "Unknown", "Contact not found"
        if not api_key:
            return "Unknown", "Missing Emailable API key"
        params = urllib.parse.urlencode({"email": contact["email"], "api_key": api_key})
        url = f"https://api.emailable.com/v1/verify?{params}"
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            category = f"Verification request failed: {exc}"
            db.execute(
                "UPDATE contacts SET verification_status = ?, verification_category = ? WHERE id = ?",
                ("Unknown", category, contact_id),
            )
            db.execute(
                "INSERT INTO verification_results (contact_id, status, category, raw_response) VALUES (?, ?, ?, ?)",
                (contact_id, "Unknown", category, json.dumps({"error": str(exc)})),
            )
            return "Unknown", category
        status = str(payload.get("state") or payload.get("status") or "Unknown").title()
        category = str(payload.get("reason") or "")
        db.execute(
            "UPDATE contacts SET verification_status = ?, verification_category = ? WHERE id = ?",
            (status, category, contact_id),
        )
        db.execute(
            "INSERT INTO verification_results (contact_id, status, category, raw_response) VALUES (?, ?, ?, ?)",
            (contact_id, status, category, json.dumps(payload)),
        )
        return status, category

    def summary(self, list_id: int | None = None) -> dict[str, int]:
        params: tuple[int, ...] = ()
        where = ""
        if list_id:
            where = "WHERE list_id = ?"
            params = (list_id,)
        rows = db.fetch_all(
            f"SELECT verification_status, COUNT(*) AS total FROM contacts {where} GROUP BY verification_status",
            params,
        )
        summary = {"Deliverable": 0, "Undeliverable": 0, "Risky": 0, "Unknown": 0}
        for row in rows:
            status = row["verification_status"] or "Unknown"
            summary[status if status in summary else "Unknown"] += int(row["total"])
        return summary
