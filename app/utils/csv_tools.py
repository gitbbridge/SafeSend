import csv
from pathlib import Path

from app.utils.validators import is_valid_email, normalize_email


def read_csv_preview(path: str, limit: int = 25) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for idx, row in enumerate(reader):
            if idx >= limit:
                break
            rows.append({key or "": value or "" for key, value in row.items()})
        return list(reader.fieldnames or []), rows


def detect_email_column(headers: list[str]) -> str:
    for header in headers:
        lowered = header.lower()
        if lowered in {"email", "email_address", "e-mail", "mail"}:
            return header
    for header in headers:
        if "email" in header.lower():
            return header
    return headers[0] if headers else ""


def cleaned_csv_contacts(path: str, email_column: str, field_map: dict[str, str]) -> tuple[list[dict[str, str]], int]:
    seen: set[str] = set()
    skipped = 0
    contacts: list[dict[str, str]] = []
    with Path(path).open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            email = normalize_email(row.get(email_column, ""))
            if not is_valid_email(email) or email in seen:
                skipped += 1
                continue
            seen.add(email)
            contact = {"email": email}
            for target, source in field_map.items():
                contact[target] = (row.get(source, "") if source else "").strip()
            contacts.append(contact)
    return contacts, skipped
