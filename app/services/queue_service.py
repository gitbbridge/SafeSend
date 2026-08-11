from app.database import db
from app.services.clustering_service import ClusteringService
from app.services.rotation_service import RotationService
from app.services.suppression_service import SuppressionService


QUEUE_BATCH_SIZE = 500


class QueueService:
    def build_campaign_queue(
        self,
        campaign_id: int,
        include_risky: bool = False,
        include_unknown: bool = False,
        cluster_mode: str = "interleaved",
        weighted_percentage: int = 20,
        progress_callback=None,
    ) -> dict[str, int]:
        campaign = db.fetch_one("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        if not campaign or not campaign["contact_list_id"]:
            return {"queued": 0, "skipped": 0, "suppressed": 0}

        contacts = [dict(row) for row in db.fetch_all("SELECT * FROM contacts WHERE list_id = ?", (campaign["contact_list_id"],))]
        suppressed = SuppressionService().emails()
        smtp_profiles = [dict(row) for row in db.fetch_all("SELECT * FROM smtp_profiles WHERE enabled = 1 ORDER BY id")]
        rotation = RotationService()
        ordered = ClusteringService().build_order(contacts, cluster_mode, weighted_percentage)

        db.execute("DELETE FROM send_queue WHERE campaign_id = ? AND status = 'Pending'", (campaign_id,))
        queued = skipped = suppressed_count = 0
        total = len(ordered)
        insert_rows = []
        for idx, contact in enumerate(ordered):
            if progress_callback and (idx == 0 or (idx + 1) % 100 == 0 or idx + 1 == total):
                progress_callback(idx + 1, total)
            status = contact.get("verification_status") or "Unknown"
            if contact["email"] in suppressed:
                suppressed_count += 1
                insert_rows.append(self._queue_values(campaign_id, contact, None, "Suppressed"))
                continue
            if status == "Undeliverable" or (status == "Risky" and not include_risky) or (status == "Unknown" and not include_unknown):
                skipped += 1
                insert_rows.append(self._queue_values(campaign_id, contact, None, "Skipped"))
                continue
            profile = rotation.choose_profile(smtp_profiles, "round_robin", idx)
            insert_rows.append(self._queue_values(campaign_id, contact, profile, "Pending"))
            queued += 1
        self._insert_queue_rows(insert_rows)
        return {"queued": queued, "skipped": skipped, "suppressed": suppressed_count}

    def list_queue(self) -> list[dict]:
        rows = db.fetch_all(
            """
            SELECT send_queue.*, campaigns.name AS campaign_name, smtp_profiles.profile_name AS smtp_name
            FROM send_queue
            LEFT JOIN campaigns ON campaigns.id = send_queue.campaign_id
            LEFT JOIN smtp_profiles ON smtp_profiles.id = send_queue.smtp_profile_id
            ORDER BY send_queue.created_at DESC
            LIMIT 500
            """
        )
        return [dict(row) for row in rows]

    def _insert_queue(self, campaign_id: int, contact: dict, profile: dict | None, status: str) -> None:
        self._insert_queue_rows([self._queue_values(campaign_id, contact, profile, status)])

    def _queue_values(self, campaign_id: int, contact: dict, profile: dict | None, status: str) -> tuple:
        name = " ".join(part for part in [contact.get("first_name"), contact.get("last_name")] if part)
        return (
            campaign_id,
            contact["id"],
            profile["id"] if profile else None,
            contact["email"],
            name,
            contact.get("cluster_group") or "",
            contact.get("verification_status") or "Unknown",
            status,
        )

    def _insert_queue_rows(self, rows: list[tuple]) -> None:
        if not rows:
            return
        query = """
            INSERT INTO send_queue (
                campaign_id, contact_id, smtp_profile_id, recipient_email, recipient_name,
                cluster_group, verification_status, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        for index in range(0, len(rows), QUEUE_BATCH_SIZE):
            db.execute_many(query, rows[index : index + QUEUE_BATCH_SIZE])
