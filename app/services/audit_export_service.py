from __future__ import annotations

import csv
from pathlib import Path

from app.database import db


class AuditExportService:
    def export_validation_audit(self, path: str | Path) -> Path:
        return self._export(
            path,
            "validation_audit_log",
            [
                "id",
                "normalized_email",
                "validation_source",
                "paid_lookup",
                "cache_hit",
                "result_status",
                "reason",
                "campaign_id",
                "created_at",
            ],
        )

    def export_mx_audit(self, path: str | Path) -> Path:
        return self._export(
            path,
            "mx_audit_log",
            [
                "id",
                "domain",
                "lookup_source",
                "paid_lookup",
                "cache_hit",
                "mx_status",
                "provider_cluster",
                "error_message",
                "campaign_id",
                "created_at",
            ],
        )

    def usage_summary(self) -> dict[str, int]:
        validation = db.fetch_one(
            """
            SELECT
                SUM(CASE WHEN paid_lookup = 1 THEN 1 ELSE 0 END) AS paid,
                SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) AS cache_hits,
                COUNT(*) AS total
            FROM validation_audit_log
            """
        )
        mx = db.fetch_one(
            """
            SELECT
                SUM(CASE WHEN paid_lookup = 1 THEN 1 ELSE 0 END) AS paid,
                SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) AS cache_hits,
                COUNT(*) AS total
            FROM mx_audit_log
            """
        )
        return {
            "validation_total": int(validation["total"] or 0) if validation else 0,
            "validation_paid": int(validation["paid"] or 0) if validation else 0,
            "validation_cache_hits": int(validation["cache_hits"] or 0) if validation else 0,
            "mx_total": int(mx["total"] or 0) if mx else 0,
            "mx_paid": int(mx["paid"] or 0) if mx else 0,
            "mx_cache_hits": int(mx["cache_hits"] or 0) if mx else 0,
        }

    def _export(self, path: str | Path, table: str, columns: list[str]) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        rows = db.fetch_all(f"SELECT {', '.join(columns)} FROM {table} ORDER BY id")
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row[key] for key in columns})
        return output
