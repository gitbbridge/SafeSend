import socket
import smtplib
import ssl
from datetime import datetime

from app.database import db
from app.models.smtp_profile import SMTPProfile
from app.utils.encryption import decrypt_value, encrypt_value
from app.utils.validators import is_valid_email

MAX_SMTP_PROFILES = 10
SECURITY_TYPES = ("None", "SSL/TLS", "STARTTLS")


class SMTPService:
    def list_profiles(self) -> list[dict]:
        rows = db.fetch_all(
            """
            SELECT id, profile_name, host, port, from_email, security_mode, enabled,
                   daily_limit, hourly_limit, max_connections, sent_today, failed_today,
                   error_counter, last_test_at, last_test_status, last_error, resolved_ip,
                   resolved_hostname, last_successful_send_at, notes, created_at, updated_at
            FROM smtp_profiles
            ORDER BY enabled DESC, profile_name
            """
        )
        return [dict(row) for row in rows]

    def get_profile(self, profile_id: int) -> dict | None:
        row = db.fetch_one("SELECT * FROM smtp_profiles WHERE id = ?", (profile_id,))
        if not row:
            return None
        profile = dict(row)
        profile["password"] = decrypt_value(profile.get("password") or "")
        return profile

    def save_profile(self, profile: SMTPProfile) -> int:
        self._validate_profile(profile)
        if profile.id is None:
            count = db.fetch_one("SELECT COUNT(*) AS total FROM smtp_profiles")
            if count and int(count["total"]) >= MAX_SMTP_PROFILES:
                raise ValueError("SafeSend supports up to 10 SMTP profiles.")
            return db.execute(
                """
                INSERT INTO smtp_profiles (
                    profile_name, host, port, username, password, from_name, from_email,
                    reply_to_email, security_mode, daily_limit, hourly_limit,
                    max_connections, enabled, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._profile_values(profile),
            )
        db.execute(
            """
            UPDATE smtp_profiles
            SET profile_name = ?, host = ?, port = ?, username = ?, password = ?,
                from_name = ?, from_email = ?, reply_to_email = ?, security_mode = ?,
                daily_limit = ?, hourly_limit = ?, max_connections = ?, enabled = ?,
                notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (*self._profile_values(profile), profile.id),
        )
        return profile.id

    def delete_profile(self, profile_id: int) -> None:
        db.execute("DELETE FROM smtp_profiles WHERE id = ?", (profile_id,))

    def duplicate_profile(self, profile_id: int) -> int:
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError("SMTP profile was not found.")
        copy = SMTPProfile(
            profile_name=f"{profile['profile_name']} Copy",
            host=profile["host"],
            port=int(profile["port"]),
            username=profile.get("username") or "",
            password=profile.get("password") or "",
            from_name=profile.get("from_name") or "",
            from_email=profile["from_email"],
            reply_to_email=profile.get("reply_to_email") or "",
            security_mode=profile.get("security_mode") or "STARTTLS",
            daily_limit=int(profile.get("daily_limit") or 500),
            hourly_limit=int(profile.get("hourly_limit") or 100),
            max_connections=int(profile.get("max_connections") or 1),
            enabled=bool(profile.get("enabled")),
            notes=profile.get("notes") or "",
        )
        return self.save_profile(copy)

    def test_connection(self, profile_id: int) -> tuple[bool, str, dict]:
        profile = self.get_profile(profile_id)
        if not profile:
            return False, "SMTP profile was not found.", {}

        now = datetime.now().isoformat(timespec="seconds")
        resolved = self.resolve_host(profile["host"])
        try:
            with self._connect(profile):
                pass
            self._record_test_result(profile_id, now, "Success", "", resolved)
            return True, "Connection and authentication succeeded.", resolved
        except Exception as exc:
            message = str(exc) or exc.__class__.__name__
            self._record_test_result(profile_id, now, "Failed", message, resolved)
            db.execute(
                "UPDATE smtp_profiles SET error_counter = error_counter + 1, failed_today = failed_today + 1 WHERE id = ?",
                (profile_id,),
            )
            return False, message, resolved

    def resolve_host(self, host: str) -> dict:
        result = {"resolved_ip": "", "resolved_hostname": ""}
        try:
            infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
            if infos:
                result["resolved_ip"] = infos[0][4][0]
        except OSError:
            return result
        if result["resolved_ip"]:
            try:
                result["resolved_hostname"] = socket.gethostbyaddr(result["resolved_ip"])[0]
            except OSError:
                result["resolved_hostname"] = socket.getfqdn(host)
        return result

    def blacklist_results(self, profile_id: int) -> list[dict]:
        rows = db.fetch_all(
            """
            SELECT zone, query, listed, response, error_message, checked_at
            FROM smtp_blacklist_checks
            WHERE smtp_profile_id = ?
            ORDER BY checked_at DESC, zone
            """,
            (profile_id,),
        )
        return [dict(row) for row in rows]

    def _profile_values(self, profile: SMTPProfile) -> tuple:
        return (
            profile.profile_name.strip(),
            profile.host.strip(),
            int(profile.port),
            profile.username.strip(),
            encrypt_value(profile.password),
            profile.from_name.strip(),
            profile.from_email.strip().lower(),
            profile.reply_to_email.strip().lower(),
            profile.security_mode,
            int(profile.daily_limit),
            int(profile.hourly_limit),
            int(profile.max_connections),
            1 if profile.enabled else 0,
            profile.notes.strip(),
        )

    def _validate_profile(self, profile: SMTPProfile) -> None:
        if not profile.profile_name.strip():
            raise ValueError("Profile name is required.")
        if not profile.host.strip():
            raise ValueError("SMTP host is required.")
        if not is_valid_email(profile.from_email):
            raise ValueError("From email must be a valid email address.")
        if profile.reply_to_email and not is_valid_email(profile.reply_to_email):
            raise ValueError("Reply-to email must be a valid email address.")
        if profile.security_mode not in SECURITY_TYPES:
            raise ValueError("Security type must be None, SSL/TLS, or STARTTLS.")
        if not 1 <= int(profile.port) <= 65535:
            raise ValueError("SMTP port must be between 1 and 65535.")
        for label, value in [
            ("Daily send limit", profile.daily_limit),
            ("Hourly send limit", profile.hourly_limit),
        ]:
            if int(value) < 0:
                raise ValueError(f"{label} cannot be negative.")
        if int(profile.max_connections) < 1:
            raise ValueError("Max connections must be at least 1.")

    def _connect(self, profile: dict):
        mode = profile.get("security_mode") or "STARTTLS"
        host = profile["host"]
        port = int(profile["port"])
        if mode in {"SSL/TLS", "SSL"}:
            client = smtplib.SMTP_SSL(host, port, timeout=20, context=ssl.create_default_context())
        else:
            client = smtplib.SMTP(host, port, timeout=20)
            client.ehlo()
            if mode in {"STARTTLS", "TLS"}:
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
        username = profile.get("username") or ""
        password = profile.get("password") or ""
        if username or password:
            client.login(username, password)
        return client

    def _record_test_result(self, profile_id: int, tested_at: str, status: str, error: str, resolved: dict) -> None:
        db.execute(
            """
            UPDATE smtp_profiles
            SET last_test_at = ?, last_test_status = ?, last_error = ?,
                resolved_ip = ?, resolved_hostname = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                tested_at,
                status,
                error,
                resolved.get("resolved_ip", ""),
                resolved.get("resolved_hostname", ""),
                profile_id,
            ),
        )
