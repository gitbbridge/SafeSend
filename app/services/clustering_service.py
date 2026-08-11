from collections import defaultdict, deque

from app.database import db


CLUSTER_BATCH_SIZE = 500


class ClusteringService:
    def cluster_contacts(self, list_id: int, field: str = "domain", threshold: int = 5, progress_callback=None) -> dict[str, int]:
        contacts = [dict(row) for row in db.fetch_all("SELECT * FROM contacts WHERE list_id = ?", (list_id,))]
        grouped: dict[str, list[dict]] = defaultdict(list)
        total = len(contacts)
        for index, contact in enumerate(contacts, start=1):
            if progress_callback and (index == 1 or index % 100 == 0 or index == total):
                progress_callback(index, total)
            key = self._cluster_key(contact, field)
            grouped[key].append(contact)

        clustered = 0
        updated = 0
        pending_updates = []
        pending_groups = []
        with db.get_connection() as conn:
            conn.execute("DELETE FROM cluster_groups WHERE list_id = ?", (list_id,))
            for key, items in grouped.items():
                is_clustered = len(items) >= threshold
                group_name = f"{field}:{key}" if key else ""
                for item in items:
                    updated += 1
                    if progress_callback and (updated == 1 or updated % 100 == 0 or updated == total):
                        progress_callback(updated, total)
                    pending_updates.append((key, group_name, len(items), 1 if is_clustered else 0, item["id"]))
                    if len(pending_updates) >= CLUSTER_BATCH_SIZE:
                        conn.executemany(
                            """
                            UPDATE contacts
                            SET cluster_key = ?, cluster_group = ?, cluster_size = ?, is_clustered = ?
                            WHERE id = ?
                            """,
                            pending_updates,
                        )
                        pending_updates.clear()
                if is_clustered:
                    clustered += len(items)
                    pending_groups.append((list_id, key, group_name, len(items), "Threshold reached"))
            if pending_updates:
                conn.executemany(
                    """
                    UPDATE contacts
                    SET cluster_key = ?, cluster_group = ?, cluster_size = ?, is_clustered = ?
                    WHERE id = ?
                    """,
                    pending_updates,
                )
            if pending_groups:
                conn.executemany(
                    """
                    INSERT INTO cluster_groups (list_id, cluster_key, cluster_group, cluster_size, risk_notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    pending_groups,
                )
            conn.commit()
        return {"total": len(contacts), "clustered": clustered, "groups": sum(1 for rows in grouped.values() if len(rows) >= threshold)}

    def preview(self, list_id: int) -> list[dict]:
        rows = db.fetch_all(
            """
            SELECT cluster_group, cluster_size, COUNT(*) AS contacts
            FROM contacts
            WHERE list_id = ? AND is_clustered = 1
            GROUP BY cluster_group, cluster_size
            ORDER BY cluster_size DESC, cluster_group
            """,
            (list_id,),
        )
        return [dict(row) for row in rows]

    def build_order(self, contacts: list[dict], mode: str = "interleaved", weighted_percentage: int = 20) -> list[dict]:
        if mode == "standard":
            return contacts
        normal = [c for c in contacts if not c.get("is_clustered")]
        clustered = [c for c in contacts if c.get("is_clustered")]
        if mode == "cluster_last":
            return normal + clustered
        if mode == "weighted":
            return self._weighted_order(normal, clustered, weighted_percentage)
        return self._interleaved_order(normal, clustered)

    def _cluster_key(self, contact: dict, field: str) -> str:
        if field == "company":
            return (contact.get("company") or "").strip().lower()
        if field == "source_list":
            return (contact.get("source_list") or "").strip().lower()
        if field == "verification_category":
            return (contact.get("verification_category") or contact.get("verification_status") or "").strip().lower()
        if field == "custom1":
            return (contact.get("custom1") or "").strip().lower()
        email = contact.get("email") or ""
        return email.split("@", 1)[1].lower() if "@" in email else ""

    def _interleaved_order(self, normal: list[dict], clustered: list[dict]) -> list[dict]:
        clusters: dict[str, deque[dict]] = defaultdict(deque)
        for contact in clustered:
            clusters[contact.get("cluster_group") or "cluster"].append(contact)
        result = list(normal)
        last_group = ""
        while any(clusters.values()):
            for group, queue in list(clusters.items()):
                if queue and group != last_group:
                    result.append(queue.popleft())
                    last_group = group
        return result

    def _weighted_order(self, normal: list[dict], clustered: list[dict], weighted_percentage: int) -> list[dict]:
        result: list[dict] = []
        normal_queue = deque(normal)
        clustered_queue = deque(clustered)
        cluster_every = max(1, round(100 / max(1, weighted_percentage)))
        step = 0
        while normal_queue or clustered_queue:
            step += 1
            if clustered_queue and step % cluster_every == 0:
                result.append(clustered_queue.popleft())
            elif normal_queue:
                result.append(normal_queue.popleft())
            elif clustered_queue:
                result.append(clustered_queue.popleft())
        return result
