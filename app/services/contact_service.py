from app.database import db
from app.services.contact_list_service import ContactListService
from app.services.suppression_service import SuppressionService
from app.utils.validators import is_valid_email, normalize_email

CONTACT_FIELDS = [
    "email",
    "first_name",
    "last_name",
    "company",
    "phone",
    "address",
    "city",
    "state",
    "zip",
    "country",
    "custom1",
    "custom2",
    "custom3",
    "verification_status",
    "last_sent_at",
    "last_verified_at",
]


class ContactService:
    def list_contacts(
        self,
        list_id: int | None = None,
        search: str = "",
        verification_status: str = "All",
        suppressed_filter: str = "All",
        sort_by: str = "email",
        descending: bool = False,
    ) -> list[dict]:
        params: list[object] = []
        clauses: list[str] = []
        if list_id:
            clauses.append("contacts.list_id = ?")
            params.append(list_id)
        if search.strip():
            like = f"%{search.strip()}%"
            clauses.append(
                """
                (
                    contacts.email LIKE ? OR contacts.first_name LIKE ? OR contacts.last_name LIKE ?
                    OR contacts.company LIKE ? OR contacts.state LIKE ?
                )
                """
            )
            params.extend([like, like, like, like, like])
        if verification_status != "All":
            clauses.append("contacts.verification_status = ?")
            params.append(verification_status)
        if suppressed_filter == "Suppressed":
            clauses.append("(contacts.is_suppressed = 1 OR suppression_list.id IS NOT NULL)")
        elif suppressed_filter == "Not suppressed":
            clauses.append("(contacts.is_suppressed = 0 AND suppression_list.id IS NULL)")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        safe_sort = sort_by if sort_by in self.sortable_columns() else "email"
        direction = "DESC" if descending else "ASC"
        rows = db.fetch_all(
            f"""
            SELECT contacts.*, contact_lists.name AS list_name,
                   CASE WHEN contacts.is_suppressed = 1 OR suppression_list.id IS NOT NULL THEN 1 ELSE 0 END AS suppressed
            FROM contacts
            JOIN contact_lists ON contact_lists.id = contacts.list_id
            LEFT JOIN suppression_list ON suppression_list.email = contacts.email
            {where}
            ORDER BY {safe_sort} {direction}, contacts.id ASC
            LIMIT 5000
            """,
            params,
        )
        return [dict(row) for row in rows]

    def get_contact(self, contact_id: int) -> dict | None:
        row = db.fetch_one(
            """
            SELECT contacts.*,
                   CASE WHEN contacts.is_suppressed = 1 OR suppression_list.id IS NOT NULL THEN 1 ELSE 0 END AS suppressed
            FROM contacts
            LEFT JOIN suppression_list ON suppression_list.email = contacts.email
            WHERE contacts.id = ?
            """,
            (contact_id,),
        )
        return dict(row) if row else None

    def save_contact(self, list_id: int, values: dict, contact_id: int | None = None) -> int:
        email = normalize_email(values.get("email", ""))
        if not is_valid_email(email):
            raise ValueError("A valid email address is required.")
        existing = db.fetch_one(
            "SELECT id FROM contacts WHERE list_id = ? AND email = ? AND id <> ?",
            (list_id, email, contact_id or 0),
        )
        if existing:
            raise ValueError("This list already contains that email address.")
        row_values = self._values(values, email)
        if contact_id:
            previous = self.get_contact(contact_id)
            db.execute(
                """
                UPDATE contacts
                SET email = ?, first_name = ?, last_name = ?, company = ?, phone = ?, address = ?,
                    city = ?, state = ?, zip = ?, country = ?, custom1 = ?, custom2 = ?, custom3 = ?,
                    verification_status = ?, last_sent_at = ?, last_verified_at = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (*row_values, contact_id),
            )
            if previous:
                ContactListService().refresh_counts(int(previous["list_id"]))
            return contact_id
        new_id = db.execute(
            """
            INSERT INTO contacts (
                list_id, email, first_name, last_name, company, phone, address, city, state, zip,
                country, custom1, custom2, custom3, verification_status, last_sent_at, last_verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (list_id, *row_values),
        )
        ContactListService().refresh_counts(list_id)
        return new_id

    def delete_contacts(self, contact_ids: list[int]) -> None:
        list_ids = {int(contact["list_id"]) for contact in self._contacts_by_ids(contact_ids)}
        for contact_id in contact_ids:
            db.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        for list_id in list_ids:
            ContactListService().refresh_counts(list_id)

    def suppress_contacts(self, contact_ids: list[int], reason: str = "Contact suppressed") -> int:
        service = SuppressionService()
        changed = 0
        for contact in self._contacts_by_ids(contact_ids):
            if service.add(contact["email"], reason):
                db.execute("UPDATE contacts SET is_suppressed = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (contact["id"],))
                changed += 1
        return changed

    def unsuppress_contacts(self, contact_ids: list[int]) -> int:
        service = SuppressionService()
        changed = 0
        for contact in self._contacts_by_ids(contact_ids):
            service.remove(contact["email"])
            db.execute("UPDATE contacts SET is_suppressed = 0, updated_at = CURRENT_TIMESTAMP WHERE email = ?", (contact["email"],))
            changed += 1
        return changed

    def move_contacts(self, contact_ids: list[int], target_list_id: int) -> dict[str, int]:
        moved = duplicates = 0
        source_list_ids: set[int] = set()
        for contact in self._contacts_by_ids(contact_ids):
            exists = db.fetch_one(
                "SELECT id FROM contacts WHERE list_id = ? AND email = ?",
                (target_list_id, contact["email"]),
            )
            if exists:
                duplicates += 1
                continue
            source_list_ids.add(int(contact["list_id"]))
            db.execute(
                "UPDATE contacts SET list_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (target_list_id, contact["id"]),
            )
            moved += 1
        for list_id in source_list_ids | {target_list_id}:
            ContactListService().refresh_counts(list_id)
        return {"moved": moved, "duplicates": duplicates}

    def copy_contacts(self, contact_ids: list[int], target_list_id: int) -> dict[str, int]:
        copied = duplicates = 0
        for contact in self._contacts_by_ids(contact_ids):
            exists = db.fetch_one(
                "SELECT id FROM contacts WHERE list_id = ? AND email = ?",
                (target_list_id, contact["email"]),
            )
            if exists:
                duplicates += 1
                continue
            db.execute(
                """
                INSERT INTO contacts (
                    list_id, email, first_name, last_name, company, phone, address, city, state, zip,
                    country, custom1, custom2, custom3, source_list, verification_status,
                    verification_category, is_suppressed, last_sent_at, last_verified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target_list_id,
                    contact["email"],
                    contact.get("first_name") or "",
                    contact.get("last_name") or "",
                    contact.get("company") or "",
                    contact.get("phone") or "",
                    contact.get("address") or "",
                    contact.get("city") or "",
                    contact.get("state") or "",
                    contact.get("zip") or "",
                    contact.get("country") or "",
                    contact.get("custom1") or "",
                    contact.get("custom2") or "",
                    contact.get("custom3") or "",
                    contact.get("source_list") or "",
                    contact.get("verification_status") or "Unknown",
                    contact.get("verification_category") or "",
                    int(contact.get("is_suppressed") or 0),
                    contact.get("last_sent_at"),
                    contact.get("last_verified_at"),
                ),
            )
            copied += 1
        ContactListService().refresh_counts(target_list_id)
        return {"copied": copied, "duplicates": duplicates}

    def sortable_columns(self) -> set[str]:
        return {
            "email",
            "first_name",
            "last_name",
            "company",
            "phone",
            "city",
            "state",
            "verification_status",
            "last_sent_at",
            "last_verified_at",
            "created_at",
            "is_suppressed",
        }

    def _contacts_by_ids(self, contact_ids: list[int]) -> list[dict]:
        if not contact_ids:
            return []
        placeholders = ",".join("?" for _ in contact_ids)
        return [dict(row) for row in db.fetch_all(f"SELECT * FROM contacts WHERE id IN ({placeholders})", contact_ids)]

    def _values(self, values: dict, email: str) -> tuple:
        return (
            email,
            (values.get("first_name") or "").strip(),
            (values.get("last_name") or "").strip(),
            (values.get("company") or "").strip(),
            (values.get("phone") or "").strip(),
            (values.get("address") or "").strip(),
            (values.get("city") or "").strip(),
            (values.get("state") or "").strip(),
            (values.get("zip") or "").strip(),
            (values.get("country") or "").strip(),
            (values.get("custom1") or "").strip(),
            (values.get("custom2") or "").strip(),
            (values.get("custom3") or "").strip(),
            values.get("verification_status") or "Unknown",
            values.get("last_sent_at") or None,
            values.get("last_verified_at") or None,
        )
