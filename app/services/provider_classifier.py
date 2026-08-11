from __future__ import annotations


MICROSOFT_365 = "MICROSOFT_365"
GOOGLE_WORKSPACE = "GOOGLE_WORKSPACE"
OTHER = "OTHER"
UNKNOWN = "UNKNOWN"


class ProviderClassifier:
    rule_version = "5.9.0"

    def classify_mx(self, mx_records: list[str] | str | None) -> str:
        if not mx_records:
            return UNKNOWN
        if isinstance(mx_records, str):
            records = [mx_records]
        else:
            records = mx_records
        lowered = " ".join(record.lower().rstrip(".") for record in records)
        if any(token in lowered for token in ("protection.outlook.com", "office365.com", "microsoft.com")):
            return MICROSOFT_365
        if any(token in lowered for token in ("google.com", "googlemail.com", "aspmx.l.google")):
            return GOOGLE_WORKSPACE
        return OTHER
