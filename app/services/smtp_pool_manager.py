from __future__ import annotations

from datetime import datetime, timezone

from app.database import db
from app.services.dns_mx_service import DomainMXService


SMTP_AVAILABLE = "AVAILABLE"


class SMTPPoolManager:
    def __init__(self, mx_service: DomainMXService | None = None) -> None:
        self.mx_service = mx_service or DomainMXService()

    def ensure_sending_domain(self, from_email: str) -> int | None:
        domain = self.mx_service.domain_from_email(from_email)
        if not domain:
            return None
        row = db.fetch_one("SELECT id FROM sending_domains WHERE domain = ?", (domain,))
        if row:
            return int(row["id"])
        return db.execute(
            """
            INSERT INTO sending_domains (domain, display_name, enabled, verified)
            VALUES (?, ?, 1, 1)
            """,
            (domain, domain),
        )

    def eligible_profiles(self, campaign_id: int | None = None, sending_domain_id: int | None = None) -> list[dict]:
        campaign = db.fetch_one("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)) if campaign_id else None
        params: list[object] = []
        where = ["smtp_profiles.enabled = 1"]
        if campaign and campaign["smtp_profile_id"]:
            where.append("smtp_profiles.id = ?")
            params.append(campaign["smtp_profile_id"])
        rows = db.fetch_all(
            f"""
            SELECT smtp_profiles.*,
                   COALESCE(smtp_account_state.state, 'AVAILABLE') AS account_state,
                   COALESCE(smtp_account_state.sent_today, smtp_profiles.sent_today, 0) AS account_sent_today,
                   COALESCE(smtp_account_state.sent_this_hour, 0) AS account_sent_this_hour,
                   smtp_account_state.cooldown_until
            FROM smtp_profiles
            LEFT JOIN smtp_account_state ON smtp_account_state.smtp_profile_id = smtp_profiles.id
            WHERE {' AND '.join(where)}
            ORDER BY smtp_profiles.id
            """,
            params,
        )
        eligible: list[dict] = []
        for row in rows:
            profile = dict(row)
            if profile.get("account_state") not in {SMTP_AVAILABLE, None, ""}:
                continue
            if profile.get("cooldown_until") and str(profile["cooldown_until"]) > self._now():
                continue
            if int(profile.get("daily_limit") or 0) and int(profile.get("account_sent_today") or 0) >= int(profile["daily_limit"]):
                continue
            if int(profile.get("hourly_limit") or 0) and int(profile.get("account_sent_this_hour") or 0) >= int(profile["hourly_limit"]):
                continue
            if sending_domain_id and not self.profile_matches_domain(profile, sending_domain_id):
                continue
            eligible.append(profile)
        return eligible

    def choose_profile(self, campaign_id: int | None = None, sending_domain_id: int | None = None) -> dict | None:
        profiles = self.eligible_profiles(campaign_id, sending_domain_id)
        if not profiles:
            return None
        return sorted(profiles, key=lambda p: (int(p.get("account_sent_today") or 0), int(p["id"])))[0]

    def profile_matches_domain(self, profile: dict, sending_domain_id: int) -> bool:
        domain_row = db.fetch_one("SELECT domain, enabled FROM sending_domains WHERE id = ?", (sending_domain_id,))
        if not domain_row or not int(domain_row["enabled"] or 0):
            return False
        from_domain = self.mx_service.domain_from_email(profile.get("from_email") or "")
        return from_domain == domain_row["domain"]

    def record_success(self, smtp_profile_id: int) -> None:
        now = self._now()
        db.execute(
            """
            INSERT INTO smtp_account_state (
                smtp_profile_id, state, sent_today, sent_this_hour, last_send_at, auth_health, updated_at
            ) VALUES (?, 'AVAILABLE', 1, 1, ?, 'OK', ?)
            ON CONFLICT(smtp_profile_id) DO UPDATE SET
                state = 'AVAILABLE',
                sent_today = sent_today + 1,
                sent_this_hour = sent_this_hour + 1,
                last_send_at = excluded.last_send_at,
                auth_health = 'OK',
                updated_at = excluded.updated_at
            """,
            (smtp_profile_id, now, now),
        )
        db.execute(
            """
            UPDATE smtp_profiles
            SET sent_today = sent_today + 1, last_successful_send_at = ?, last_used_at = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (now, now, smtp_profile_id),
        )

    def record_failure(self, smtp_profile_id: int, status: str, error: str) -> None:
        now = self._now()
        state = "AUTH_ERROR" if status == "AUTH_ERROR" else "AVAILABLE"
        db.execute(
            """
            INSERT INTO smtp_account_state (
                smtp_profile_id, state, failed_today, auth_health, last_error, updated_at
            ) VALUES (?, ?, 1, ?, ?, ?)
            ON CONFLICT(smtp_profile_id) DO UPDATE SET
                state = excluded.state,
                failed_today = failed_today + 1,
                auth_health = excluded.auth_health,
                last_error = excluded.last_error,
                updated_at = excluded.updated_at
            """,
            (smtp_profile_id, state, status, error, now),
        )
        db.execute(
            """
            UPDATE smtp_profiles
            SET failed_today = failed_today + 1, error_counter = error_counter + 1, last_error = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (error, smtp_profile_id),
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")
