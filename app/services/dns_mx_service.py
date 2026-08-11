from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.database import db
from app.services.provider_classifier import ProviderClassifier, UNKNOWN


@dataclass(slots=True)
class MXLookupResult:
    domain: str
    mx_records: list[str]
    provider_cluster: str
    mx_status: str
    lookup_source: str
    error_message: str = ""
    cache_hit: bool = False
    paid_lookup: bool = False


class DomainMXService:
    ttl_days = 30

    def __init__(self, resolver: object | None = None, classifier: ProviderClassifier | None = None) -> None:
        self.resolver = resolver
        self.classifier = classifier or ProviderClassifier()

    def normalize_domain(self, domain: str) -> str:
        return (domain or "").strip().lower().rstrip(".")

    def domain_from_email(self, email: str) -> str:
        parts = (email or "").strip().lower().rsplit("@", 1)
        return parts[1] if len(parts) == 2 else ""

    def resolve_domain(self, domain: str, campaign_id: int | None = None, force_refresh: bool = False) -> MXLookupResult:
        normalized = self.normalize_domain(domain)
        if not normalized:
            return MXLookupResult("", [], UNKNOWN, "INVALID_DOMAIN", "input")
        cached = None if force_refresh else self._cached(normalized)
        if cached:
            result = MXLookupResult(
                domain=normalized,
                mx_records=json.loads(cached["mx_records"] or "[]"),
                provider_cluster=cached["provider_cluster"] or UNKNOWN,
                mx_status=cached["mx_status"] or "UNKNOWN",
                lookup_source=cached["lookup_source"] or "cache",
                cache_hit=True,
            )
            self._audit(result, campaign_id)
            return result
        result = self._direct_lookup(normalized)
        self._store(result)
        self._audit(result, campaign_id)
        return result

    def _cached(self, domain: str):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return db.fetch_one(
            """
            SELECT * FROM domain_mx_cache
            WHERE domain = ? AND expires_at IS NOT NULL AND expires_at > ?
            """,
            (domain, now),
        )

    def _direct_lookup(self, domain: str) -> MXLookupResult:
        if self.resolver:
            return self.resolver.resolve_domain(domain)
        try:
            try:
                import dns.resolver  # type: ignore

                answers = dns.resolver.resolve(domain, "MX", lifetime=8)
                records = sorted(
                    [str(answer.exchange).rstrip(".") for answer in answers],
                    key=lambda item: item.lower(),
                )
                if records == ["."]:
                    return MXLookupResult(domain, [], UNKNOWN, "NULL_MX", "dns")
                return MXLookupResult(domain, records, self.classifier.classify_mx(records), "MX", "dns")
            except ImportError:
                return self._implicit_lookup(domain)
            except Exception as exc:
                name = exc.__class__.__name__.lower()
                if any(token in name for token in ("timeout", "servfail", "nonameservers")):
                    return MXLookupResult(domain, [], UNKNOWN, "TRANSIENT_FAILURE", "dns", str(exc))
                return self._implicit_lookup(domain)
        except Exception as exc:
            return MXLookupResult(domain, [], UNKNOWN, "TRANSIENT_FAILURE", "dns", str(exc))

    def _implicit_lookup(self, domain: str) -> MXLookupResult:
        try:
            socket.getaddrinfo(domain, None)
            return MXLookupResult(domain, [], UNKNOWN, "IMPLICIT_MX", "socket")
        except OSError as exc:
            return MXLookupResult(domain, [], UNKNOWN, "NO_ROUTE", "socket", str(exc))

    def _store(self, result: MXLookupResult) -> None:
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(days=self.ttl_days)).isoformat(timespec="seconds")
        db.execute(
            """
            INSERT INTO domain_mx_cache (
                domain, mx_records, provider_cluster, mx_status, lookup_source, looked_up_at, expires_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                mx_records = excluded.mx_records,
                provider_cluster = excluded.provider_cluster,
                mx_status = excluded.mx_status,
                lookup_source = excluded.lookup_source,
                looked_up_at = excluded.looked_up_at,
                expires_at = excluded.expires_at,
                updated_at = excluded.updated_at
            """,
            (
                result.domain,
                json.dumps(result.mx_records),
                result.provider_cluster,
                result.mx_status,
                result.lookup_source,
                now.isoformat(timespec="seconds"),
                expires,
                now.isoformat(timespec="seconds"),
            ),
        )

    def _audit(self, result: MXLookupResult, campaign_id: int | None = None) -> None:
        db.execute(
            """
            INSERT INTO mx_audit_log (
                domain, lookup_source, paid_lookup, cache_hit, mx_status, provider_cluster, error_message, campaign_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.domain,
                result.lookup_source,
                1 if result.paid_lookup else 0,
                1 if result.cache_hit else 0,
                result.mx_status,
                result.provider_cluster,
                result.error_message,
                campaign_id,
            ),
        )
