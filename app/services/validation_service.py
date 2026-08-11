from __future__ import annotations

import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.database import db
from app.services.dns_mx_service import DomainMXService
from app.services.provider_classifier import UNKNOWN
from app.utils.validators import is_valid_email, normalize_email


DEFAULT_VALIDATION_WORKERS = 4
MAX_VALIDATION_WORKERS = 8


@dataclass(slots=True)
class ValidationResult:
    email: str
    normalized_email: str
    validation_status: str
    validation_result: str = ""
    reason: str = ""
    score: float | None = None
    deliverable: bool | None = None
    accept_all: bool | None = None
    disposable: bool | None = None
    role_address: bool | None = None
    free_provider: bool | None = None
    mx_found: bool | None = None
    mx_records: list[str] | None = None
    provider_cluster: str = UNKNOWN
    validation_source: str = "local"
    raw_provider_data: dict[str, Any] | None = None
    cache_hit: bool = False
    paid_lookup: bool = False


class EmailableClient:
    endpoint = "https://api.emailable.com/v1/verify"

    def verify(self, email: str, api_key: str) -> dict[str, Any]:
        query = urllib.parse.urlencode({"email": email, "api_key": api_key})
        with urllib.request.urlopen(f"{self.endpoint}?{query}", timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))


class EmailValidationService:
    def __init__(self, client: EmailableClient | None = None, mx_service: DomainMXService | None = None) -> None:
        self.client = client or EmailableClient()
        self.mx_service = mx_service or DomainMXService()

    def validate_email(self, email: str, campaign_id: int | None = None, force_refresh: bool = False) -> ValidationResult:
        normalized = normalize_email(email)
        if not normalized or not is_valid_email(normalized):
            result = ValidationResult(email, normalized, "UNDELIVERABLE", "invalid_format", "Invalid email format")
            self._store(result)
            self._audit(result, campaign_id)
            return result
        cached = None if force_refresh else self._cached(normalized)
        if cached:
            result = self._row_to_result(cached)
            result.cache_hit = True
            self._audit(result, campaign_id)
            return result
        api_key = self._setting("emailable_api_key")
        if api_key:
            try:
                raw = self.client.verify(normalized, api_key)
                result = self._standardize_provider_result(email, normalized, raw)
                self._store(result)
                self._audit(result, campaign_id)
                return result
            except Exception as exc:
                result = ValidationResult(
                    email,
                    normalized,
                    "VALIDATION_DEFERRED",
                    "transient_provider_failure",
                    str(exc),
                    validation_source="emailable",
                    paid_lookup=True,
                )
                self._audit(result, campaign_id)
                return result
        mx = self.mx_service.resolve_domain(self.mx_service.domain_from_email(normalized), campaign_id)
        if mx.mx_status == "NO_ROUTE" or mx.mx_status == "NULL_MX":
            status = "UNDELIVERABLE"
            deliverable = False
        elif mx.mx_status == "TRANSIENT_FAILURE":
            status = "VALIDATION_DEFERRED"
            deliverable = None
        else:
            status = "UNKNOWN"
            deliverable = None
        result = ValidationResult(
            email=email,
            normalized_email=normalized,
            validation_status=status,
            validation_result=mx.mx_status,
            reason=mx.error_message,
            deliverable=deliverable,
            mx_found=mx.mx_status in {"MX", "IMPLICIT_MX"},
            mx_records=mx.mx_records,
            provider_cluster=mx.provider_cluster,
            validation_source=mx.lookup_source,
        )
        self._store(result)
        self._audit(result, campaign_id)
        return result

    def provider_for_email(self, email: str, campaign_id: int | None = None) -> str:
        result = self.validate_email(email, campaign_id)
        return result.provider_cluster or UNKNOWN

    def validate_many(
        self,
        emails: list[str],
        campaign_id: int | None = None,
        *,
        max_workers: int = DEFAULT_VALIDATION_WORKERS,
        progress_callback=None,
    ) -> list[ValidationResult]:
        worker_count = max(1, min(int(max_workers or DEFAULT_VALIDATION_WORKERS), MAX_VALIDATION_WORKERS))
        results: list[ValidationResult] = []
        total = len(emails)
        completed = 0
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="SafeSendValidation") as executor:
            futures = [executor.submit(self.validate_email, email, campaign_id) for email in emails]
            for future in as_completed(futures):
                results.append(future.result())
                completed += 1
                if progress_callback and (completed == 1 or completed % 100 == 0 or completed == total):
                    progress_callback(completed, total)
        return results

    def _cached(self, normalized_email: str):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return db.fetch_one(
            """
            SELECT * FROM validation_pool
            WHERE normalized_email = ? AND expires_at IS NOT NULL AND expires_at > ?
            """,
            (normalized_email, now),
        )

    def _store(self, result: ValidationResult) -> None:
        ttl_days = int(self._setting("email_validation_ttl_days") or 30)
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=ttl_days)).isoformat(timespec="seconds")
        db.execute(
            """
            INSERT INTO validation_pool (
                email, normalized_email, validation_status, validation_result, reason, score,
                deliverable, accept_all, disposable, role_address, free_provider, mx_found,
                mx_records, provider_cluster, validated_at, expires_at, validation_source, raw_provider_data, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(normalized_email) DO UPDATE SET
                email = excluded.email,
                validation_status = excluded.validation_status,
                validation_result = excluded.validation_result,
                reason = excluded.reason,
                score = excluded.score,
                deliverable = excluded.deliverable,
                accept_all = excluded.accept_all,
                disposable = excluded.disposable,
                role_address = excluded.role_address,
                free_provider = excluded.free_provider,
                mx_found = excluded.mx_found,
                mx_records = excluded.mx_records,
                provider_cluster = excluded.provider_cluster,
                validated_at = excluded.validated_at,
                expires_at = excluded.expires_at,
                validation_source = excluded.validation_source,
                raw_provider_data = excluded.raw_provider_data,
                updated_at = excluded.updated_at
            """,
            (
                result.email,
                result.normalized_email,
                result.validation_status,
                result.validation_result,
                result.reason,
                result.score,
                self._bool(result.deliverable),
                self._bool(result.accept_all),
                self._bool(result.disposable),
                self._bool(result.role_address),
                self._bool(result.free_provider),
                self._bool(result.mx_found),
                json.dumps(result.mx_records or []),
                result.provider_cluster or UNKNOWN,
                now.isoformat(timespec="seconds"),
                expires,
                result.validation_source,
                json.dumps(result.raw_provider_data or {}),
                now.isoformat(timespec="seconds"),
            ),
        )

    def _audit(self, result: ValidationResult, campaign_id: int | None = None) -> None:
        db.execute(
            """
            INSERT INTO validation_audit_log (
                normalized_email, validation_source, paid_lookup, cache_hit, result_status, reason, campaign_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.normalized_email,
                result.validation_source,
                1 if result.paid_lookup else 0,
                1 if result.cache_hit else 0,
                result.validation_status,
                result.reason,
                campaign_id,
            ),
        )

    def _standardize_provider_result(self, email: str, normalized: str, raw: dict[str, Any]) -> ValidationResult:
        state = str(raw.get("state") or raw.get("status") or "").lower()
        reason = str(raw.get("reason") or raw.get("message") or "")
        if state in {"deliverable", "valid"}:
            status = "DELIVERABLE"
            deliverable = True
        elif state in {"risky", "accept_all", "unknown"}:
            status = "RISKY" if state != "unknown" else "UNKNOWN"
            deliverable = None
        elif state in {"undeliverable", "invalid"}:
            status = "UNDELIVERABLE"
            deliverable = False
        else:
            status = "UNKNOWN"
            deliverable = None
        mx_records = raw.get("mx_records") if isinstance(raw.get("mx_records"), list) else []
        return ValidationResult(
            email=email,
            normalized_email=normalized,
            validation_status=status,
            validation_result=state,
            reason=reason,
            score=float(raw["score"]) if raw.get("score") is not None else None,
            deliverable=deliverable,
            accept_all=self._maybe_bool(raw.get("accept_all")),
            disposable=self._maybe_bool(raw.get("disposable")),
            role_address=self._maybe_bool(raw.get("role")),
            free_provider=self._maybe_bool(raw.get("free")),
            mx_found=self._maybe_bool(raw.get("mx_found")),
            mx_records=mx_records,
            provider_cluster=self.mx_service.classifier.classify_mx(mx_records),
            validation_source="emailable",
            raw_provider_data=raw,
            paid_lookup=True,
        )

    def _row_to_result(self, row) -> ValidationResult:
        return ValidationResult(
            email=row["email"],
            normalized_email=row["normalized_email"],
            validation_status=row["validation_status"],
            validation_result=row["validation_result"] or "",
            reason=row["reason"] or "",
            score=row["score"],
            deliverable=self._row_bool(row["deliverable"]),
            accept_all=self._row_bool(row["accept_all"]),
            disposable=self._row_bool(row["disposable"]),
            role_address=self._row_bool(row["role_address"]),
            free_provider=self._row_bool(row["free_provider"]),
            mx_found=self._row_bool(row["mx_found"]),
            mx_records=json.loads(row["mx_records"] or "[]"),
            provider_cluster=row["provider_cluster"] or UNKNOWN,
            validation_source=row["validation_source"] or "cache",
            raw_provider_data=json.loads(row["raw_provider_data"] or "{}"),
        )

    def _setting(self, key: str) -> str:
        row = db.fetch_one("SELECT value FROM app_settings WHERE key = ?", (key,))
        return str(row["value"] or "") if row else ""

    def _bool(self, value: bool | None) -> int | None:
        if value is None:
            return None
        return 1 if value else 0

    def _maybe_bool(self, value: Any) -> bool | None:
        if value is None:
            return None
        return bool(value)

    def _row_bool(self, value: Any) -> bool | None:
        if value is None:
            return None
        return bool(value)
