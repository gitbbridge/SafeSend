from app.database import db


class ContactListService:
    def list_lists(self, include_archived: bool = False) -> list[dict]:
        where = "" if include_archived else "WHERE archived = 0"
        rows = db.fetch_all(
            f"""
            SELECT *
            FROM contact_lists
            {where}
            ORDER BY archived ASC, updated_at DESC, created_at DESC
            """
        )
        return [dict(row) for row in rows]

    def get_list(self, list_id: int) -> dict | None:
        row = db.fetch_one("SELECT * FROM contact_lists WHERE id = ?", (list_id,))
        return dict(row) if row else None

    def create_list(self, name: str, notes: str = "") -> int:
        name = name.strip()
        if not name:
            raise ValueError("List name is required.")
        return db.execute(
            "INSERT INTO contact_lists (name, notes) VALUES (?, ?)",
            (name, notes.strip()),
        )

    def rename_list(self, list_id: int, name: str, notes: str = "") -> None:
        name = name.strip()
        if not name:
            raise ValueError("List name is required.")
        db.execute(
            """
            UPDATE contact_lists
            SET name = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (name, notes.strip(), list_id),
        )

    def duplicate_list(self, list_id: int) -> int:
        source = self.get_list(list_id)
        if not source:
            raise ValueError("Contact list was not found.")
        new_name = self._copy_name(source["name"])
        new_id = db.execute(
            """
            INSERT INTO contact_lists (
                name, source_file, total_contacts, duplicate_count, notes, last_imported_at, last_verified_at
            ) VALUES (?, ?, 0, ?, ?, ?, ?)
            """,
            (
                new_name,
                source.get("source_file") or "",
                int(source.get("duplicate_count") or 0),
                source.get("notes") or "",
                source.get("last_imported_at"),
                source.get("last_verified_at"),
            ),
        )
        contacts = db.fetch_all(
            """
            SELECT email, first_name, last_name, company, phone, address, city, state, zip, country,
                   custom1, custom2, custom3, source_list, cluster_key, cluster_group, cluster_size,
                   is_clustered, is_suppressed, verification_status, verification_category, send_priority,
                   last_sent_at, last_verified_at
            FROM contacts
            WHERE list_id = ?
            """,
            (list_id,),
        )
        for contact in contacts:
            db.execute(
                """
                INSERT OR IGNORE INTO contacts (
                    list_id, email, first_name, last_name, company, phone, address, city, state, zip,
                    country, custom1, custom2, custom3, source_list, cluster_key, cluster_group,
                    cluster_size, is_clustered, is_suppressed, verification_status, verification_category,
                    send_priority, last_sent_at, last_verified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (new_id, *tuple(contact)),
            )
        self.refresh_counts(new_id)
        return new_id

    def archive_list(self, list_id: int, archived: bool = True) -> None:
        db.execute(
            "UPDATE contact_lists SET archived = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if archived else 0, list_id),
        )

    def delete_list(self, list_id: int) -> None:
        db.execute("DELETE FROM contact_lists WHERE id = ?", (list_id,))

    def refresh_counts(self, list_id: int) -> None:
        total = db.fetch_one("SELECT COUNT(*) AS total FROM contacts WHERE list_id = ?", (list_id,))
        db.execute(
            """
            UPDATE contact_lists
            SET total_contacts = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (int(total["total"]) if total else 0, list_id),
        )

    def stats(self, list_id: int | None = None) -> dict[str, int]:
        where = "WHERE list_id = ?" if list_id else ""
        params = (list_id,) if list_id else ()
        stats = {
            "total": 0,
            "Deliverable": 0,
            "Risky": 0,
            "Unknown": 0,
            "Undeliverable": 0,
            "suppressed": 0,
            "duplicates": 0,
        }
        total = db.fetch_one(f"SELECT COUNT(*) AS total FROM contacts {where}", params)
        stats["total"] = int(total["total"]) if total else 0
        rows = db.fetch_all(
            f"SELECT verification_status, COUNT(*) AS total FROM contacts {where} GROUP BY verification_status",
            params,
        )
        for row in rows:
            key = row["verification_status"] or "Unknown"
            stats[key if key in stats else "Unknown"] += int(row["total"])
        suppressed = db.fetch_one(
            f"""
            SELECT COUNT(*) AS total
            FROM contacts
            LEFT JOIN suppression_list ON suppression_list.email = contacts.email
            {where}
            {'AND' if where else 'WHERE'} (contacts.is_suppressed = 1 OR suppression_list.id IS NOT NULL)
            """,
            params,
        )
        stats["suppressed"] = int(suppressed["total"]) if suppressed else 0
        dupes = db.fetch_one(
            f"""
            SELECT COUNT(*) AS total
            FROM (
                SELECT email
                FROM contacts
                {where}
                GROUP BY email
                HAVING COUNT(*) > 1
            )
            """,
            params,
        )
        stats["duplicates"] = int(dupes["total"]) if dupes else 0
        return stats

    def _copy_name(self, name: str) -> str:
        candidate = f"{name} Copy"
        index = 2
        while db.fetch_one("SELECT id FROM contact_lists WHERE name = ?", (candidate,)):
            candidate = f"{name} Copy {index}"
            index += 1
        return candidate
