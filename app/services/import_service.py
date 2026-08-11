import csv
from pathlib import Path
from typing import Callable

from app.database import db
from app.services.contact_list_service import ContactListService
from app.utils.csv_tools import detect_email_column, read_csv_preview
from app.utils.validators import is_valid_email, normalize_email

SUPPORTED_FIELDS = [
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
]


IMPORT_BATCH_SIZE = 500


class ImportService:
    def preview_csv(self, path: str) -> dict:
        headers, rows = read_csv_preview(path, 25)
        return {"headers": headers, "rows": rows, "email_column": detect_email_column(headers)}

    def import_csv(
        self,
        path: str,
        list_name: str,
        email_column: str,
        field_map: dict[str, str],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict:
        list_id = self._ensure_list(list_name, str(Path(path)))
        return self.import_into_list(
            path,
            list_id,
            {"email": email_column, **field_map},
            {
                "skip_duplicates": True,
                "update_existing": False,
                "ignore_blank_emails": True,
                "validate_email_format": True,
                "suppress_invalid_emails": False,
            },
            progress_callback=progress_callback,
        )

    def import_into_list(
        self,
        path: str,
        list_id: int,
        field_map: dict[str, str],
        options: dict,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict:
        email_column = field_map.get("email", "")
        if not email_column:
            raise ValueError("Email column mapping is required.")
        total_rows = self._count_data_rows(path)

        summary = {
            "list_id": list_id,
            "processed": 0,
            "inserted": 0,
            "updated": 0,
            "duplicates": 0,
            "invalid": 0,
            "blank": 0,
            "suppressed_invalid": 0,
            "skipped": 0,
        }
        seen_in_file: set[str] = set()

        insert_rows: list[tuple] = []
        update_rows: list[tuple] = []
        suppression_rows: list[tuple] = []

        with db.get_connection() as conn:
            existing_by_email = {
                row["email"]: int(row["id"])
                for row in conn.execute("SELECT id, email FROM contacts WHERE list_id = ?", (list_id,)).fetchall()
            }

            def flush() -> None:
                if insert_rows:
                    conn.executemany(
                        """
                        INSERT INTO contacts (
                            list_id, email, first_name, last_name, company, phone, address, city, state, zip,
                            country, custom1, custom2, custom3, source_list, verification_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        insert_rows,
                    )
                    insert_rows.clear()
                if update_rows:
                    conn.executemany(
                        """
                        UPDATE contacts
                        SET first_name = ?, last_name = ?, company = ?, phone = ?, address = ?, city = ?,
                            state = ?, zip = ?, country = ?, custom1 = ?, custom2 = ?, custom3 = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        update_rows,
                    )
                    update_rows.clear()
                if suppression_rows:
                    conn.executemany(
                        """
                        INSERT INTO suppression_list (
                            email, normalized_email, reason, scope, source, active, updated_at
                        ) VALUES (?, ?, 'Invalid email from import', 'Global', 'import', 1, CURRENT_TIMESTAMP)
                        ON CONFLICT(email) DO UPDATE SET
                            normalized_email = excluded.normalized_email,
                            reason = excluded.reason,
                            source = excluded.source,
                            active = 1,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        suppression_rows,
                    )
                    suppression_rows.clear()
                conn.commit()

            with Path(path).open("r", newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    summary["processed"] += 1
                    if progress_callback and (summary["processed"] == 1 or summary["processed"] % 100 == 0):
                        progress_callback(summary["processed"], total_rows)
                    raw_email = row.get(email_column, "")
                    email = normalize_email(raw_email)
                    if not email:
                        summary["blank"] += 1
                        if options.get("ignore_blank_emails", True):
                            summary["skipped"] += 1
                            continue
                    if options.get("validate_email_format", True) and not is_valid_email(email):
                        summary["invalid"] += 1
                        if options.get("suppress_invalid_emails") and email:
                            suppression_rows.append((email, email))
                            summary["suppressed_invalid"] += 1
                        summary["skipped"] += 1
                        if summary["processed"] % IMPORT_BATCH_SIZE == 0:
                            flush()
                        continue
                    if email in seen_in_file:
                        summary["duplicates"] += 1
                        if options.get("skip_duplicates", True):
                            summary["skipped"] += 1
                            continue
                    seen_in_file.add(email)

                    values = self._mapped_values(row, field_map, email)
                    existing_id = existing_by_email.get(email)
                    if existing_id:
                        summary["duplicates"] += 1
                        if options.get("update_existing"):
                            update_rows.append(self._update_values(existing_id, values))
                            summary["updated"] += 1
                        elif options.get("skip_duplicates", True):
                            summary["skipped"] += 1
                        if summary["processed"] % IMPORT_BATCH_SIZE == 0:
                            flush()
                        continue

                    insert_rows.append(self._insert_values(list_id, values))
                    existing_by_email[email] = -1
                    summary["inserted"] += 1
                    if len(insert_rows) + len(update_rows) + len(suppression_rows) >= IMPORT_BATCH_SIZE:
                        flush()
            flush()
            conn.execute(
                """
                UPDATE contact_lists
                SET source_file = ?, last_imported_at = CURRENT_TIMESTAMP,
                    duplicate_count = duplicate_count + ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (str(Path(path)), summary["duplicates"], list_id),
            )
            conn.commit()
        if progress_callback:
            progress_callback(summary["processed"], total_rows)
        ContactListService().refresh_counts(list_id)
        return summary

    def _count_data_rows(self, path: str) -> int:
        with Path(path).open("r", newline="", encoding="utf-8-sig") as fh:
            count = sum(1 for _line in fh)
        return max(0, count - 1)

    def list_contact_lists(self, include_archived: bool = False) -> list[dict]:
        return ContactListService().list_lists(include_archived)

    def _ensure_list(self, list_name: str, source_file: str = "") -> int:
        name = (list_name or "Imported List").strip()
        row = db.fetch_one("SELECT id FROM contact_lists WHERE name = ?", (name,))
        if row:
            return int(row["id"])
        return db.execute("INSERT INTO contact_lists (name, source_file) VALUES (?, ?)", (name, source_file))

    def _mapped_values(self, row: dict[str, str], field_map: dict[str, str], email: str) -> dict:
        values = {"email": email}
        for field in SUPPORTED_FIELDS:
            if field == "email":
                continue
            source = field_map.get(field, "")
            values[field] = (row.get(source, "") if source else "").strip()
        values["verification_status"] = "Unknown"
        return values

    def _insert_contact(self, list_id: int, values: dict) -> int:
        return db.execute(
            """
            INSERT INTO contacts (
                list_id, email, first_name, last_name, company, phone, address, city, state, zip,
                country, custom1, custom2, custom3, source_list, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                list_id,
                values["email"],
                values.get("first_name", ""),
                values.get("last_name", ""),
                values.get("company", ""),
                values.get("phone", ""),
                values.get("address", ""),
                values.get("city", ""),
                values.get("state", ""),
                values.get("zip", ""),
                values.get("country", ""),
                values.get("custom1", ""),
                values.get("custom2", ""),
                values.get("custom3", ""),
                values.get("source_list", ""),
                values.get("verification_status", "Unknown"),
            ),
        )

    def _update_contact(self, contact_id: int, values: dict) -> None:
        db.execute(
            """
            UPDATE contacts
            SET first_name = ?, last_name = ?, company = ?, phone = ?, address = ?, city = ?,
                state = ?, zip = ?, country = ?, custom1 = ?, custom2 = ?, custom3 = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                values.get("first_name", ""),
                values.get("last_name", ""),
                values.get("company", ""),
                values.get("phone", ""),
                values.get("address", ""),
                values.get("city", ""),
                values.get("state", ""),
                values.get("zip", ""),
                values.get("country", ""),
                values.get("custom1", ""),
                values.get("custom2", ""),
                values.get("custom3", ""),
                contact_id,
            ),
        )

    def _insert_values(self, list_id: int, values: dict) -> tuple:
        return (
            list_id,
            values["email"],
            values.get("first_name", ""),
            values.get("last_name", ""),
            values.get("company", ""),
            values.get("phone", ""),
            values.get("address", ""),
            values.get("city", ""),
            values.get("state", ""),
            values.get("zip", ""),
            values.get("country", ""),
            values.get("custom1", ""),
            values.get("custom2", ""),
            values.get("custom3", ""),
            values.get("source_list", ""),
            values.get("verification_status", "Unknown"),
        )

    def _update_values(self, contact_id: int, values: dict) -> tuple:
        return (
            values.get("first_name", ""),
            values.get("last_name", ""),
            values.get("company", ""),
            values.get("phone", ""),
            values.get("address", ""),
            values.get("city", ""),
            values.get("state", ""),
            values.get("zip", ""),
            values.get("country", ""),
            values.get("custom1", ""),
            values.get("custom2", ""),
            values.get("custom3", ""),
            contact_id,
        )
