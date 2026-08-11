import csv
from pathlib import Path
from typing import Callable


EXPORT_FIELDS = [
    "email",
    "first_name",
    "last_name",
    "company",
    "phone",
    "address",
    "city",
    "state",
    "zip",
    "country",
    "custom1",
    "custom2",
    "custom3",
    "verification_status",
    "suppressed",
    "last_sent_at",
    "last_verified_at",
]


class ExportService:
    def export_contacts(self, contacts: list[dict], path: str, progress_callback: Callable[[int, int], None] | None = None) -> int:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        total = len(contacts)
        with output.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=EXPORT_FIELDS)
            writer.writeheader()
            for index, contact in enumerate(contacts, start=1):
                writer.writerow({field: contact.get(field, "") for field in EXPORT_FIELDS})
                if progress_callback and (index == 1 or index % 100 == 0 or index == total):
                    progress_callback(index, total)
        return len(contacts)
