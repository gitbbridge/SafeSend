from dataclasses import dataclass


@dataclass(slots=True)
class Contact:
    list_id: int
    email: str
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    custom1: str = ""
    custom2: str = ""
    source_list: str = ""
    cluster_key: str = ""
    verification_status: str = "Unknown"
    id: int | None = None
