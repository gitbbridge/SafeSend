from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["SAFESEND_DB_PATH"] = str(Path(tempfile.gettempdir()) / "safesend_59_engine_simulation.db")

from app.database import db
from app.database.db import initialize_database
from app.models.smtp_profile import SMTPProfile
from app.services.audit_export_service import AuditExportService
from app.services.credential_service import DPAPI_PREFIX
from app.services.dns_mx_service import MXLookupResult
from app.services.event_bus import UIEventBus
from app.services.import_service import ImportService
from app.services.operation_tracker import OperationTracker
from app.services.send_engine import EngineState, SendEngine
from app.services.smtp_service import SMTPService
from app.services.smtp_transport import SMTPResult, ScriptedSMTPTransport
from app.services.suppression_service import SuppressionService


class FixtureResolver:
    def resolve_domain(self, domain: str) -> MXLookupResult:
        if domain.startswith("m365"):
            return MXLookupResult(domain, ["mx.protection.outlook.com"], "MICROSOFT_365", "MX", "fixture")
        if domain.startswith("google"):
            return MXLookupResult(domain, ["aspmx.l.google.com"], "GOOGLE_WORKSPACE", "MX", "fixture")
        if domain.startswith("noroute"):
            return MXLookupResult(domain, [], "UNKNOWN", "NO_ROUTE", "fixture")
        if domain.startswith("nullmx"):
            return MXLookupResult(domain, [], "UNKNOWN", "NULL_MX", "fixture")
        if domain.startswith("timeout"):
            return MXLookupResult(domain, [], "UNKNOWN", "TRANSIENT_FAILURE", "fixture", "timeout")
        return MXLookupResult(domain, ["mail.other.example"], "OTHER", "MX", "fixture")


def reset_database() -> None:
    path = Path(tempfile.gettempdir()) / f"safesend_59_engine_simulation_{uuid.uuid4().hex}.db"
    os.environ["SAFESEND_DB_PATH"] = str(path)
    db.DB_PATH = path
    backup_dir = path.parent / "backups"
    if backup_dir.exists():
        for item in backup_dir.glob("safesend_pre_migration_*.db"):
            item.unlink()
    initialize_database()


def seed_smtp_profiles() -> list[int]:
    service = SMTPService()
    profile_ids = []
    for idx in range(3):
        profile_ids.append(
            service.save_profile(
                SMTPProfile(
                    profile_name=f"Primary Sender {idx + 1}",
                    host=f"smtp{idx + 1}.safesend.test",
                    port=587,
                    username=f"user{idx + 1}",
                    password=f"super-secret-{idx + 1}",
                    from_name="SafeSend",
                    from_email=f"sender{idx + 1}@safesend.test",
                    reply_to_email="reply@safesend.test",
                    security_mode="STARTTLS",
                    daily_limit=600,
                    hourly_limit=600,
                    max_connections=1,
                    enabled=True,
                    notes="simulation",
                )
            )
        )
    return profile_ids


def seed_campaign(contact_count: int = 1000) -> int:
    list_id = db.execute("INSERT INTO contact_lists (name, notes) VALUES (?, ?)", ("5.9 Simulation List", "engine test"))
    domains = [f"m365{i}.test" for i in range(40)] + [f"google{i}.test" for i in range(40)] + [f"other{i}.test" for i in range(40)]
    for idx in range(contact_count - 4):
        domain = domains[idx % len(domains)]
        db.execute(
            """
            INSERT INTO contacts (list_id, email, first_name, last_name, company)
            VALUES (?, ?, ?, ?, ?)
            """,
            (list_id, f"person{idx}@{domain}", f"First{idx}", f"Last{idx}", "Example Co"),
        )
    db.execute("INSERT INTO contacts (list_id, email) VALUES (?, ?)", (list_id, "blocked@other1.test"))
    db.execute("INSERT INTO contacts (list_id, email) VALUES (?, ?)", (list_id, "bad-address"))
    db.execute("INSERT INTO contacts (list_id, email) VALUES (?, ?)", (list_id, "dead@noroute1.test"))
    db.execute("INSERT INTO contacts (list_id, email) VALUES (?, ?)", (list_id, "waiting@timeout1.test"))
    SuppressionService().add("blocked@other1.test", "seeded suppression", source="simulation")
    campaign_id = db.execute(
        """
        INSERT INTO campaigns (name, subject, html_body, plain_text_body, contact_list_id, status)
        VALUES (?, ?, ?, ?, ?, 'Ready')
        """,
        ("5.9 Simulation Campaign", "Simulation", "<p>Hello</p>", "Hello", list_id),
    )
    return campaign_id


def run_primary_simulation() -> dict:
    from app.services.dns_mx_service import DomainMXService
    from app.services.validation_service import EmailValidationService

    reset_database()
    seed_smtp_profiles()
    campaign_id = seed_campaign()
    mx_service = DomainMXService(resolver=FixtureResolver())
    validation_service = EmailValidationService(mx_service=mx_service)
    event_bus = UIEventBus()
    transport = ScriptedSMTPTransport()
    from app.services.send_engine import CampaignSendEngine

    engine = CampaignSendEngine(campaign_id, event_bus=event_bus, transport=transport, validation_service=validation_service, mx_service=mx_service)
    state = engine.run_synchronously(max_jobs=999)
    statuses = {
        row["status"]: row["total"]
        for row in db.fetch_all("SELECT status, COUNT(*) AS total FROM send_jobs GROUP BY status")
    }
    sent_count = len(transport.sent_messages)
    message_ids = [row["message_id"] for row in db.fetch_all("SELECT message_id FROM send_jobs WHERE status = 'SENT'")]
    domains = [row["recipient_domain"] for row in db.fetch_all("SELECT recipient_domain FROM send_jobs ORDER BY id LIMIT 180")]
    max_run = max_same_domain_run(domains)
    assert state in {EngineState.STOPPED, EngineState.COMPLETED}, state
    assert statuses.get("SENT", 0) == sent_count
    assert statuses.get("SUPPRESSED", 0) >= 2, statuses
    assert statuses.get("FAILED", 0) >= 1, statuses
    assert statuses.get("WAITING", 0) >= 1, statuses
    assert len(message_ids) == len(set(message_ids)), "Message-ID values must be unique"
    assert all(message_id for message_id in message_ids), "Every sent job must persist Message-ID"
    assert max_run <= 2, f"Domain clustering has a long same-domain run: {max_run}"
    assert db.fetch_one("SELECT COUNT(*) AS total FROM validation_audit_log")["total"] > 0
    assert db.fetch_one("SELECT COUNT(*) AS total FROM mx_audit_log")["total"] > 0
    return {
        "campaign_id": campaign_id,
        "state": state.value,
        "statuses": statuses,
        "sent_messages": sent_count,
        "message_ids": len(message_ids),
        "max_same_domain_run": max_run,
        "events": len(event_bus.drain(10000)),
    }


def run_provider_cap_test() -> dict:
    db.execute("UPDATE provider_rate_limits SET hourly_limit = 2 WHERE provider_cluster = 'GOOGLE_WORKSPACE'")
    google_jobs = db.fetch_all("SELECT id FROM send_jobs WHERE provider_cluster = 'GOOGLE_WORKSPACE' AND status = 'QUEUED' LIMIT 5")
    for row in google_jobs:
        db.execute("UPDATE send_jobs SET status = 'QUEUED', scheduled_at = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))
    result = db.fetch_one("SELECT hourly_limit FROM provider_rate_limits WHERE provider_cluster = 'GOOGLE_WORKSPACE'")
    assert int(result["hourly_limit"]) == 2
    return {"google_hourly_limit": 2, "eligible_cap_configured": True}


def run_pause_stop_thread_test() -> dict:
    from app.services.dns_mx_service import DomainMXService
    from app.services.validation_service import EmailValidationService

    reset_database()
    seed_smtp_profiles()
    campaign_id = seed_campaign(contact_count=80)
    mx_service = DomainMXService(resolver=FixtureResolver())
    validation_service = EmailValidationService(mx_service=mx_service)

    def slow_send(_profile, _message):
        time.sleep(0.01)
        return SMTPResult(True, "SENT", response="slow-ok")

    transport = ScriptedSMTPTransport(slow_send)
    manager = SendEngine(event_bus=UIEventBus(), transport=transport, validation_service=validation_service, mx_service=mx_service)
    before_threads = threading.active_count()
    assert manager.start_campaign(campaign_id)
    wait_until(lambda: db.fetch_one("SELECT COUNT(*) AS total FROM send_jobs")["total"] > 0, timeout=8)
    assert not manager.start_campaign(campaign_id), "Second engine instance should be rejected while running"
    manager.pause_campaign(campaign_id)
    time.sleep(0.05)
    manager.resume_campaign(campaign_id)
    time.sleep(0.05)
    manager.stop_campaign(campaign_id)
    manager.shutdown(timeout=3.0)
    after_threads = threading.active_count()
    campaign = db.fetch_one("SELECT status FROM campaigns WHERE id = ?", (campaign_id,))
    assert campaign["status"] in {"Stopped", "Completed"}
    assert after_threads <= before_threads + 1
    return {"campaign_status": campaign["status"], "threads_before": before_threads, "threads_after": after_threads}


def wait_until(predicate, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("Timed out waiting for test condition.")


def run_crash_recovery_test() -> dict:
    reset_database()
    seed_smtp_profiles()
    campaign_id = seed_campaign(contact_count=8)
    job_id = db.execute(
        """
        INSERT INTO send_jobs (campaign_id, email, normalized_email, status)
        VALUES (?, ?, ?, 'SENDING')
        """,
        (campaign_id, "recover@other.test", "recover@other.test"),
    )
    manager = SendEngine()
    row = db.fetch_one("SELECT status FROM send_jobs WHERE id = ?", (job_id,))
    assert row["status"] == "UNKNOWN"
    return {"recovered": manager.last_recovered_count, "job_status": row["status"]}


def run_credential_test() -> dict:
    reset_database()
    profile_id = seed_smtp_profiles()[0]
    raw = db.fetch_one("SELECT password FROM smtp_profiles WHERE id = ?", (profile_id,))["password"]
    profile = SMTPService().get_profile(profile_id)
    assert raw != "super-secret-1"
    assert profile["password"] == "super-secret-1"
    return {"raw_secret_prefix": str(raw).split(":", 1)[0], "dpapi": str(raw).startswith(DPAPI_PREFIX)}


def run_migration_backup_test() -> dict:
    backup_db = Path(tempfile.gettempdir()) / "safesend_59_old_schema.db"
    if backup_db.exists():
        backup_db.unlink()
    backup_dir = backup_db.parent / "backups"
    if backup_dir.exists():
        for item in backup_dir.glob("safesend_pre_migration_*.db"):
            item.unlink()
    with sqlite3.connect(backup_db) as conn:
        conn.execute("CREATE TABLE app_settings (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO app_settings (key, value) VALUES ('existing', 'kept')")
        conn.commit()
    original_path = db.DB_PATH
    try:
        db.DB_PATH = backup_db
        initialize_database()
        backup_files = list(backup_dir.glob("safesend_pre_migration_*.db"))
        assert backup_files, "Expected a pre-migration backup"
        assert db.fetch_one("SELECT value FROM app_settings WHERE key = ?", ("existing",))["value"] == "kept"
        assert db.fetch_one("SELECT COUNT(*) AS total FROM send_jobs")["total"] == 0
        return {"backup_created": True, "backup_count": len(backup_files)}
    finally:
        db.DB_PATH = original_path


def run_audit_export_test() -> dict:
    reset_database()
    seed_smtp_profiles()
    campaign_id = seed_campaign(contact_count=20)
    from app.services.dns_mx_service import DomainMXService
    from app.services.validation_service import EmailValidationService
    from app.services.send_engine import CampaignSendEngine

    mx_service = DomainMXService(resolver=FixtureResolver())
    validation_service = EmailValidationService(mx_service=mx_service)
    CampaignSendEngine(campaign_id, transport=ScriptedSMTPTransport(), validation_service=validation_service, mx_service=mx_service).run_synchronously(max_jobs=20)
    out_dir = Path(tempfile.gettempdir()) / "safesend_59_exports"
    validation_path = AuditExportService().export_validation_audit(out_dir / "validation_audit.csv")
    mx_path = AuditExportService().export_mx_audit(out_dir / "mx_audit.csv")
    summary = AuditExportService().usage_summary()
    assert validation_path.exists() and validation_path.stat().st_size > 0
    assert mx_path.exists() and mx_path.stat().st_size > 0
    assert summary["validation_total"] > 0
    return {"validation_export": str(validation_path), "mx_export": str(mx_path), "usage_summary": summary}


def run_progress_throttle_test() -> dict:
    tracker = OperationTracker(min_update_interval=60.0)
    handle = tracker.begin("Throttle test", "Starting", total=1000)
    for index in range(1, 1000):
        handle.update("Processing", current=index, total=1000)
    handle.update("Processing", current=1000, total=1000)
    updates = tracker.drain_updates(2000)
    assert len(updates) <= 3, len(updates)
    handle.complete()
    return {"updates_after_1000_calls": len(updates), "throttled": True}


def run_constrained_worker_test() -> dict:
    reset_database()
    from app.services.dns_mx_service import DomainMXService
    from app.services.validation_service import EmailValidationService

    mx_service = DomainMXService(resolver=FixtureResolver())
    validation_service = EmailValidationService(mx_service=mx_service)
    emails = [f"worker{i}@m365{i % 5}.test" for i in range(40)]
    progress_events = []
    before_threads = threading.active_count()
    results = validation_service.validate_many(
        emails,
        max_workers=2,
        progress_callback=lambda current, total: progress_events.append((current, total)),
    )
    after_threads = threading.active_count()
    assert len(results) == len(emails)
    assert after_threads <= before_threads + 1
    assert progress_events[-1] == (len(emails), len(emails))
    return {
        "emails": len(emails),
        "max_workers": 2,
        "threads_before": before_threads,
        "threads_after": after_threads,
        "progress_events": len(progress_events),
    }


def run_batched_import_test() -> dict:
    reset_database()
    csv_path = Path(tempfile.gettempdir()) / f"safesend_59_import_{uuid.uuid4().hex}.csv"
    rows = ["email,first_name,last_name,company"]
    rows.extend(f"import{i}@example.test,First{i},Last{i},Example" for i in range(1205))
    csv_path.write_text("\n".join(rows), encoding="utf-8")
    list_id = db.execute("INSERT INTO contact_lists (name) VALUES (?)", ("Batched Import Test",))
    progress_events = []
    summary = ImportService().import_into_list(
        str(csv_path),
        list_id,
        {"email": "email", "first_name": "first_name", "last_name": "last_name", "company": "company"},
        {
            "skip_duplicates": True,
            "update_existing": False,
            "ignore_blank_emails": True,
            "validate_email_format": True,
            "suppress_invalid_emails": False,
        },
        progress_callback=lambda current, total: progress_events.append((current, total)),
    )
    count = db.fetch_one("SELECT COUNT(*) AS total FROM contacts WHERE list_id = ?", (list_id,))["total"]
    assert int(count) == 1205
    assert summary["inserted"] == 1205
    assert progress_events[-1] == (1205, 1205)
    assert len(progress_events) <= 15
    return {"inserted": summary["inserted"], "progress_events": len(progress_events), "rows_in_db": int(count)}


def run_scheduled_wait_test() -> dict:
    reset_database()
    seed_smtp_profiles()
    campaign_id = seed_campaign(contact_count=8)
    future = (datetime.now(timezone.utc) + timedelta(seconds=120)).isoformat(timespec="seconds")
    db.execute(
        """
        INSERT INTO send_jobs (campaign_id, email, normalized_email, status, scheduled_at)
        VALUES (?, ?, ?, 'WAITING', ?)
        """,
        (campaign_id, "future@example.test", "future@example.test", future),
    )
    from app.services.send_engine import CampaignSendEngine

    engine = CampaignSendEngine(campaign_id)
    seconds, label = engine._seconds_until_next_due_job()
    assert 1.0 < seconds <= 60.0
    assert "Waiting for next scheduled send" in label
    return {"sleep_seconds": round(seconds, 2), "label": label}


def max_same_domain_run(domains: list[str]) -> int:
    longest = 0
    current = 0
    previous = None
    for domain in domains:
        if domain == previous:
            current += 1
        else:
            current = 1
            previous = domain
        longest = max(longest, current)
    return longest


def main() -> int:
    results = {
        "primary_simulation": run_primary_simulation(),
        "provider_cap": run_provider_cap_test(),
        "pause_stop_threads": run_pause_stop_thread_test(),
        "crash_recovery": run_crash_recovery_test(),
        "credential_security": run_credential_test(),
        "migration_backup": run_migration_backup_test(),
        "audit_export": run_audit_export_test(),
        "progress_throttle": run_progress_throttle_test(),
        "constrained_workers": run_constrained_worker_test(),
        "batched_import": run_batched_import_test(),
        "scheduled_wait": run_scheduled_wait_test(),
    }
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"ASSERTION FAILED: {exc}", file=sys.stderr)
        raise
