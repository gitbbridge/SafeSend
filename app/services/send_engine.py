from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from app.database import db
from app.services.dns_mx_service import DomainMXService
from app.services.event_bus import EngineEvent, EngineEventType, UIEventBus
from app.services.message_builder import MessageBuilder
from app.services.operation_tracker import OperationHandle, OperationTracker
from app.services.smtp_pool_manager import SMTPPoolManager
from app.services.smtp_service import SMTPService
from app.services.smtp_transport import SMTPResult, SMTPTransport
from app.services.suppression_service import SuppressionService
from app.services.validation_service import EmailValidationService
from app.utils.validators import is_valid_email, normalize_email


class EngineState(str, Enum):
    IDLE = "IDLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


WAITING_STATUSES = ("QUEUED", "WAITING", "DEFERRED")
ACTIVE_STATUSES = ("QUEUED", "WAITING", "SENDING", "DEFERRED")
SEND_JOB_BATCH_SIZE = 500


class CampaignSendEngine:
    def __init__(
        self,
        campaign_id: int,
        event_bus: UIEventBus | None = None,
        transport: SMTPTransport | None = None,
        validation_service: EmailValidationService | None = None,
        mx_service: DomainMXService | None = None,
        operation_handle: OperationHandle | None = None,
    ) -> None:
        self.campaign_id = campaign_id
        self.event_bus = event_bus or UIEventBus()
        self.mx_service = mx_service or DomainMXService()
        self.validation_service = validation_service or EmailValidationService(mx_service=self.mx_service)
        self.pool_manager = SMTPPoolManager(self.mx_service)
        self.smtp_service = SMTPService()
        self.transport = transport or SMTPTransport()
        self.message_builder = MessageBuilder()
        self.suppression = SuppressionService()
        self.state = EngineState.IDLE
        self.operation_handle = operation_handle
        self._completed_jobs = 0
        self._total_jobs = 0
        self._thread: threading.Thread | None = None
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> bool:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._stop_event.clear()
            self._pause_event.clear()
            self._set_state(EngineState.STARTING)
            self._thread = threading.Thread(
                target=self._run,
                name=f"SafeSendCampaignEngine-{self.campaign_id}",
                daemon=True,
            )
            self._thread.start()
            return True

    def run_synchronously(self, max_jobs: int | None = None) -> EngineState:
        self._stop_event.clear()
        self._pause_event.clear()
        self._set_state(EngineState.STARTING)
        self._run(max_jobs=max_jobs)
        return self.state

    def pause(self) -> None:
        self._pause_event.set()

    def resume(self) -> None:
        self._pause_event.clear()

    def stop(self) -> None:
        self._set_state(EngineState.STOPPING)
        self._stop_event.set()

    def join(self, timeout: float | None = None) -> None:
        if self._thread:
            self._thread.join(timeout)

    def _run(self, max_jobs: int | None = None) -> None:
        sent_or_terminal = 0
        try:
            self._progress("Preparing campaign...")
            self._prepare_send_jobs()
            self._total_jobs = self._remaining_count()
            db.execute("UPDATE campaigns SET status = 'Running', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (self.campaign_id,))
            self._set_state(EngineState.RUNNING)
            while True:
                if self._stop_event.is_set():
                    self._progress("Stopping safely...")
                    self._cancel_remaining()
                    self._set_state(EngineState.STOPPED)
                    return
                if self._pause_event.is_set():
                    self._set_state(EngineState.PAUSED)
                    self._progress("Paused")
                    db.execute("UPDATE campaigns SET status = 'Paused', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (self.campaign_id,))
                    while self._pause_event.is_set() and not self._stop_event.is_set():
                        time.sleep(0.05)
                    if self._stop_event.is_set():
                        continue
                    db.execute("UPDATE campaigns SET status = 'Running', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (self.campaign_id,))
                    self._set_state(EngineState.RUNNING)
                    self._progress("Sending")
                if max_jobs is not None and sent_or_terminal >= max_jobs:
                    self._set_state(EngineState.STOPPED)
                    return
                job = self._next_due_job()
                if not job:
                    if self._remaining_count() == 0:
                        db.execute(
                            "UPDATE campaigns SET status = 'Completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (self.campaign_id,),
                        )
                        self._set_state(EngineState.COMPLETED)
                        return
                    if max_jobs is not None:
                        self._set_state(EngineState.STOPPED)
                        return
                    wait_seconds, label = self._seconds_until_next_due_job()
                    self._progress(label)
                    self._stop_event.wait(wait_seconds)
                    continue
                terminal = self._process_job(job)
                if terminal:
                    sent_or_terminal += 1
                    self._completed_jobs += 1
                    self._progress("Sending", current=self._completed_jobs, total=max(self._total_jobs, self._completed_jobs))
        except Exception as exc:
            db.execute(
                "UPDATE campaigns SET status = 'Error', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (self.campaign_id,),
            )
            self._publish(EngineEventType.ERROR, message=str(exc))
            self._set_state(EngineState.ERROR)
        finally:
            if self.operation_handle:
                self.operation_handle.complete()

    def _prepare_send_jobs(self) -> None:
        campaign = self._campaign()
        if not campaign:
            raise ValueError("Campaign was not found.")
        if not campaign["contact_list_id"]:
            return
        contacts = [dict(row) for row in db.fetch_all("SELECT * FROM contacts WHERE list_id = ?", (campaign["contact_list_id"],))]
        prepared: list[dict[str, Any]] = []
        total_contacts = len(contacts)
        for index, contact in enumerate(contacts, start=1):
            if self._stop_event.is_set():
                return
            if self._operation_cancelled():
                self._stop_event.set()
                return
            if index == 1 or index % 50 == 0 or index == total_contacts:
                self._progress("Preparing campaign recipients", current=index, total=total_contacts)
            email = contact.get("email") or ""
            normalized = normalize_email(email)
            domain = self.mx_service.domain_from_email(normalized)
            if not normalized or not is_valid_email(normalized):
                self.suppression.add(email, "Invalid email format", "Global", self.campaign_id, validate=False, source="engine")
                prepared.append(
                    {
                        "contact": contact,
                        "normalized": normalized or email,
                        "domain": domain,
                        "provider": "UNKNOWN",
                        "status": "SUPPRESSED",
                        "error": "Invalid email format",
                        "scheduled_at": self._now(),
                    }
                )
                continue
            validation = self.validation_service.validate_email(normalized, self.campaign_id)
            status = "QUEUED"
            error = ""
            if self.suppression.is_suppressed(normalized):
                status = "SUPPRESSED"
            elif validation.validation_status == "UNDELIVERABLE" and validation.validation_result == "invalid_format":
                self.suppression.add(normalized, "Invalid email format", "Global", self.campaign_id, validate=False, source="engine")
                status = "SUPPRESSED"
                error = "Invalid email format"
            elif validation.validation_status == "VALIDATION_DEFERRED":
                status = "WAITING"
                error = validation.reason
            scheduled_at = (
                (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(timespec="seconds")
                if status == "WAITING"
                else self._now()
            )
            prepared.append(
                {
                    "contact": contact,
                    "normalized": normalized,
                    "domain": domain,
                    "provider": validation.provider_cluster,
                    "status": status,
                    "error": error,
                    "scheduled_at": scheduled_at,
                }
            )
        total_prepared = len(prepared)
        job_rows = []
        for index, item in enumerate(self._clustered_prepared(prepared), start=1):
            if self._stop_event.is_set():
                return
            if index == 1 or index % 50 == 0 or index == total_prepared:
                self._progress("Writing campaign send jobs", current=index, total=total_prepared)
            job_rows.append(
                self._send_job_values(
                    item["contact"],
                    item["normalized"],
                    item["domain"],
                    item["provider"],
                    item["status"],
                    item["error"],
                    item["scheduled_at"],
                )
            )
        self._insert_job_rows(job_rows)

    def _clustered_prepared(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        groups: dict[tuple[str, str], deque[dict]] = defaultdict(deque)
        for entry in entries:
            groups[(entry["provider"] or "UNKNOWN", entry["domain"] or "")].append(entry)
        ordered: list[dict[str, Any]] = []
        keys = sorted(groups, key=lambda key: (key[0], key[1]))
        while keys:
            next_keys = []
            for key in keys:
                bucket = groups[key]
                if bucket:
                    ordered.append(bucket.popleft())
                if bucket:
                    next_keys.append(key)
            keys = next_keys
        return ordered

    def _insert_or_ignore_job(
        self,
        contact: dict,
        normalized_email: str,
        domain: str,
        provider_cluster: str,
        status: str,
        error: str,
        scheduled_at: str | None = None,
    ) -> None:
        self._insert_job_rows([self._send_job_values(contact, normalized_email, domain, provider_cluster, status, error, scheduled_at)])

    def _send_job_values(
        self,
        contact: dict,
        normalized_email: str,
        domain: str,
        provider_cluster: str,
        status: str,
        error: str,
        scheduled_at: str | None = None,
    ) -> tuple:
        return (
            self.campaign_id,
            contact.get("id"),
            contact.get("email") or normalized_email,
            normalized_email,
            domain,
            provider_cluster or "UNKNOWN",
            json.dumps(self._personalization(contact)),
            status,
            scheduled_at or self._now(),
            error,
        )

    def _insert_job_rows(self, rows: list[tuple]) -> None:
        if not rows:
            return
        query = """
            INSERT OR IGNORE INTO send_jobs (
                campaign_id, recipient_id, email, normalized_email, recipient_domain,
                provider_cluster, personalization_data, status, scheduled_at, last_error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        for index in range(0, len(rows), SEND_JOB_BATCH_SIZE):
            db.execute_many(query, rows[index : index + SEND_JOB_BATCH_SIZE])
            self._publish(
                EngineEventType.JOB_QUEUED,
                message=f"Queued {min(index + SEND_JOB_BATCH_SIZE, len(rows)):,} / {len(rows):,} send jobs",
            )

    def _process_job(self, job: dict) -> bool:
        if self._operation_cancelled():
            self._stop_event.set()
            return False
        gate_error = self._eligibility_error(job)
        if gate_error:
            terminal_status = "SUPPRESSED" if "suppressed" in gate_error.lower() else "FAILED"
            self._update_job(job["id"], terminal_status, completed_at=self._now(), last_error=gate_error)
            self._publish(EngineEventType.JOB_SUPPRESSED if terminal_status == "SUPPRESSED" else EngineEventType.JOB_FAILED, job["id"], gate_error)
            return True
        sending_domain_id = self._sending_domain_for_job(job)
        selected = self.pool_manager.choose_profile(self.campaign_id, sending_domain_id)
        if not selected:
            self._update_job(job["id"], "WAITING", last_error="No eligible SMTP account is currently available.")
            return False
        smtp_profile = self.smtp_service.get_profile(int(selected["id"])) or selected
        if sending_domain_id and not self.pool_manager.profile_matches_domain(smtp_profile, sending_domain_id):
            self._update_job(job["id"], "FAILED", completed_at=self._now(), last_error="SMTP From domain is not approved for this sending domain.")
            return True
        campaign = self._campaign()
        if not campaign:
            self._update_job(job["id"], "FAILED", completed_at=self._now(), last_error="Campaign no longer exists.")
            return True
        message_id = self.message_builder.ensure_message_id(job["id"], self.campaign_id, job["email"], smtp_profile, sending_domain_id)
        self._update_job(
            job["id"],
            "SENDING",
            started_at=self._now(),
            smtp_account_id=smtp_profile["id"],
            sending_domain_id=sending_domain_id,
            message_id=message_id,
        )
        self._publish(EngineEventType.JOB_STARTED, job["id"], f"Sending {job['email']}")
        result = self.transport.send(smtp_profile, self.message_builder.build(campaign, job, smtp_profile, message_id))
        return self._record_transport_result(job, smtp_profile, message_id, result)

    def _record_transport_result(self, job: dict, smtp_profile: dict, message_id: str, result: SMTPResult) -> bool:
        if result.success:
            now = self._now()
            self._update_job(job["id"], "SENT", completed_at=now)
            self.pool_manager.record_success(int(smtp_profile["id"]))
            self.message_builder.mark_sent(message_id)
            self._publish(EngineEventType.JOB_COMPLETED, job["id"], "Message sent", {"message_id": message_id})
            return True
        if result.transient:
            self._update_job(
                job["id"],
                "DEFERRED",
                scheduled_at=(datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(timespec="seconds"),
                last_error=result.response,
            )
            self.pool_manager.record_failure(int(smtp_profile["id"]), result.status, result.response)
            self._publish(EngineEventType.JOB_DEFERRED, job["id"], result.response)
            return False
        self._update_job(job["id"], "FAILED", completed_at=self._now(), last_error=result.response)
        self.pool_manager.record_failure(int(smtp_profile["id"]), result.status, result.response)
        self._publish(EngineEventType.JOB_FAILED, job["id"], result.response)
        return True

    def _eligibility_error(self, job: dict) -> str:
        campaign = self._campaign()
        if not campaign:
            return "Campaign no longer exists."
        if campaign["archived"]:
            return "Campaign is archived."
        if self.suppression.is_suppressed(job["normalized_email"]):
            return "Recipient is suppressed."
        validation = db.fetch_one("SELECT validation_status FROM validation_pool WHERE normalized_email = ?", (job["normalized_email"],))
        if validation and validation["validation_status"] == "UNDELIVERABLE":
            return "Recipient validation is undeliverable."
        duplicate = db.fetch_one(
            """
            SELECT id FROM message_registry
            WHERE campaign_id = ? AND recipient_email = ? AND sent_at IS NOT NULL
            """,
            (self.campaign_id, job["email"]),
        )
        if duplicate:
            return "Duplicate send prevented for this campaign recipient."
        provider_gate = self._provider_gate(job.get("provider_cluster") or "UNKNOWN")
        if provider_gate:
            return provider_gate
        return ""

    def _provider_gate(self, provider_cluster: str) -> str:
        row = db.fetch_one("SELECT * FROM provider_rate_limits WHERE provider_cluster = ?", (provider_cluster,))
        if not row or not int(row["enabled"] or 0):
            return "Provider cluster is temporarily disabled."
        now = datetime.now(timezone.utc)
        if row["hourly_limit"]:
            cutoff = (now - timedelta(hours=1)).isoformat(timespec="seconds")
            count = db.fetch_one(
                "SELECT COUNT(*) AS total FROM send_jobs WHERE provider_cluster = ? AND status = 'SENT' AND completed_at >= ?",
                (provider_cluster, cutoff),
            )
            if int(count["total"] or 0) >= int(row["hourly_limit"]):
                return f"{provider_cluster} hourly provider limit reached."
        if row["daily_limit"]:
            cutoff = (now - timedelta(days=1)).isoformat(timespec="seconds")
            count = db.fetch_one(
                "SELECT COUNT(*) AS total FROM send_jobs WHERE provider_cluster = ? AND status = 'SENT' AND completed_at >= ?",
                (provider_cluster, cutoff),
            )
            if int(count["total"] or 0) >= int(row["daily_limit"]):
                return f"{provider_cluster} daily provider limit reached."
        return ""

    def _sending_domain_for_job(self, job: dict) -> int | None:
        if job.get("sending_domain_id"):
            return int(job["sending_domain_id"])
        campaign = self._campaign()
        profile = self.smtp_service.get_profile(int(campaign["smtp_profile_id"])) if campaign and campaign["smtp_profile_id"] else None
        if not profile:
            profile = self.pool_manager.choose_profile(self.campaign_id)
        if not profile:
            return None
        domain_id = self.pool_manager.ensure_sending_domain(profile.get("from_email") or "")
        if domain_id:
            db.execute("UPDATE send_jobs SET sending_domain_id = ? WHERE id = ?", (domain_id, job["id"]))
        return domain_id

    def _next_due_job(self) -> dict | None:
        row = db.fetch_one(
            """
            SELECT * FROM send_jobs
            WHERE campaign_id = ?
              AND status IN ('QUEUED', 'WAITING', 'DEFERRED')
              AND (scheduled_at IS NULL OR scheduled_at <= ?)
            ORDER BY scheduled_at, id
            LIMIT 1
            """,
            (self.campaign_id, self._now()),
        )
        return dict(row) if row else None

    def _remaining_count(self) -> int:
        row = db.fetch_one(
            """
            SELECT COUNT(*) AS total FROM send_jobs
            WHERE campaign_id = ? AND status IN ('QUEUED', 'WAITING', 'SENDING', 'DEFERRED')
            """,
            (self.campaign_id,),
        )
        return int(row["total"] or 0) if row else 0

    def _seconds_until_next_due_job(self) -> tuple[float, str]:
        row = db.fetch_one(
            """
            SELECT scheduled_at FROM send_jobs
            WHERE campaign_id = ? AND status IN ('QUEUED', 'WAITING', 'DEFERRED')
            ORDER BY scheduled_at
            LIMIT 1
            """,
            (self.campaign_id,),
        )
        if not row or not row["scheduled_at"]:
            return 5.0, "Waiting for next scheduled send..."
        try:
            scheduled = datetime.fromisoformat(str(row["scheduled_at"]).replace("Z", "+00:00"))
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=timezone.utc)
            seconds = max(0.5, (scheduled - datetime.now(timezone.utc)).total_seconds())
            local_label = scheduled.astimezone().strftime("%I:%M %p").lstrip("0")
            return min(seconds, 60.0), f"Waiting for next scheduled send - {local_label}"
        except ValueError:
            return 5.0, "Waiting for next scheduled send..."

    def _cancel_remaining(self) -> None:
        db.execute(
            """
            UPDATE send_jobs
            SET status = 'CANCELLED', completed_at = CURRENT_TIMESTAMP, last_error = 'Engine stopped by user.'
            WHERE campaign_id = ? AND status IN ('QUEUED', 'WAITING', 'DEFERRED', 'SENDING')
            """,
            (self.campaign_id,),
        )
        db.execute("UPDATE campaigns SET status = 'Stopped', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (self.campaign_id,))

    def _update_job(self, job_id: int, status: str, **fields: Any) -> None:
        assignments = ["status = ?"]
        params: list[Any] = [status]
        for key, value in fields.items():
            assignments.append(f"{key} = ?")
            params.append(value)
        params.append(job_id)
        db.execute(f"UPDATE send_jobs SET {', '.join(assignments)} WHERE id = ?", params)

    def _campaign(self) -> dict | None:
        row = db.fetch_one("SELECT * FROM campaigns WHERE id = ?", (self.campaign_id,))
        return dict(row) if row else None

    def _personalization(self, contact: dict) -> dict[str, Any]:
        return {
            "first_name": contact.get("first_name") or "",
            "last_name": contact.get("last_name") or "",
            "company": contact.get("company") or "",
            "city": contact.get("city") or "",
            "state": contact.get("state") or "",
            "custom1": contact.get("custom1") or "",
            "custom2": contact.get("custom2") or "",
            "custom3": contact.get("custom3") or "",
        }

    def _publish(self, event_type: EngineEventType, send_job_id: int | None = None, message: str = "", payload: dict[str, Any] | None = None) -> None:
        self.event_bus.publish(
            EngineEvent(
                event_type=event_type,
                campaign_id=self.campaign_id,
                send_job_id=send_job_id,
                message=message,
                payload=payload or {},
            )
        )

    def _set_state(self, state: EngineState) -> None:
        self.state = state
        self._publish(EngineEventType.STATE_CHANGED, message=state.value)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _progress(self, detail: str, current: int | None = None, total: int | None = None) -> None:
        if self.operation_handle:
            self.operation_handle.update(detail, current=current, total=total, indeterminate=total is None)

    def _operation_cancelled(self) -> bool:
        return bool(self.operation_handle and self.operation_handle.cancel_requested())


class SendEngine:
    _instances: dict[int, CampaignSendEngine] = {}
    _instances_lock = threading.Lock()

    def __init__(
        self,
        event_bus: UIEventBus | None = None,
        transport: SMTPTransport | None = None,
        validation_service: EmailValidationService | None = None,
        mx_service: DomainMXService | None = None,
        operation_tracker: OperationTracker | None = None,
    ) -> None:
        self.event_bus = event_bus or UIEventBus()
        self.transport = transport
        self.mx_service = mx_service
        self.validation_service = validation_service
        self.operation_tracker = operation_tracker
        self.last_recovered_count = self.recover_interrupted_jobs()

    def start_campaign(self, campaign_id: int) -> bool:
        engine = self._engine_for(campaign_id)
        return engine.start()

    def run_campaign_synchronously(self, campaign_id: int, max_jobs: int | None = None) -> EngineState:
        engine = self._engine_for(campaign_id)
        return engine.run_synchronously(max_jobs=max_jobs)

    def pause_campaign(self, campaign_id: int) -> None:
        db.execute("UPDATE campaigns SET status = 'Paused', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (campaign_id,))
        engine = self._existing(campaign_id)
        if engine:
            engine.pause()

    def resume_campaign(self, campaign_id: int) -> None:
        db.execute("UPDATE campaigns SET status = 'Queued', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (campaign_id,))
        engine = self._existing(campaign_id)
        if engine:
            engine.resume()

    def stop_campaign(self, campaign_id: int) -> None:
        engine = self._existing(campaign_id)
        if engine:
            engine.stop()
        else:
            db.execute(
                """
                UPDATE send_jobs SET status = 'CANCELLED', completed_at = CURRENT_TIMESTAMP, last_error = 'Stopped before engine start.'
                WHERE campaign_id = ? AND status IN ('QUEUED', 'WAITING', 'DEFERRED', 'SENDING')
                """,
                (campaign_id,),
            )
            db.execute("UPDATE campaigns SET status = 'Stopped', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (campaign_id,))

    def cancel_campaign(self, campaign_id: int) -> None:
        self.stop_campaign(campaign_id)
        db.execute("UPDATE campaigns SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (campaign_id,))
        db.execute("UPDATE send_queue SET status = 'Skipped' WHERE campaign_id = ? AND status = 'Pending'", (campaign_id,))

    def shutdown(self, timeout: float = 5.0) -> None:
        deadline = time.time() + timeout
        for engine in list(self._instances.values()):
            engine.stop()
        for engine in list(self._instances.values()):
            remaining = max(0.0, deadline - time.time())
            engine.join(remaining)

    def recover_interrupted_jobs(self) -> int:
        row = db.fetch_one("SELECT COUNT(*) AS total FROM sqlite_master WHERE type = 'table' AND name = 'send_jobs'")
        if not row or int(row["total"] or 0) == 0:
            return 0
        count = db.fetch_one("SELECT COUNT(*) AS total FROM send_jobs WHERE status = 'SENDING'")
        db.execute(
            """
            UPDATE send_jobs
            SET status = 'UNKNOWN', last_error = 'Recovered from interrupted SENDING state.'
            WHERE status = 'SENDING'
            """
        )
        return int(count["total"] or 0) if count else 0

    def _engine_for(self, campaign_id: int) -> CampaignSendEngine:
        with self._instances_lock:
            engine = self._instances.get(campaign_id)
            if engine and engine._thread and engine._thread.is_alive():
                return engine
            handle = None
            if self.operation_tracker:
                handle = self.operation_tracker.begin(
                    "Sending campaign",
                    "Preparing campaign...",
                    total=None,
                    cancellable=True,
                    critical=True,
                )
            engine = CampaignSendEngine(
                campaign_id,
                self.event_bus,
                self.transport,
                validation_service=self.validation_service,
                mx_service=self.mx_service,
                operation_handle=handle,
            )
            self._instances[campaign_id] = engine
            return engine

    def _existing(self, campaign_id: int) -> CampaignSendEngine | None:
        with self._instances_lock:
            return self._instances.get(campaign_id)
