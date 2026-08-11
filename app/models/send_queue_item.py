from dataclasses import dataclass


@dataclass(slots=True)
class SendQueueItem:
    recipient_email: str
    campaign_id: int | None = None
    contact_id: int | None = None
    smtp_profile_id: int | None = None
    recipient_name: str = ""
    cluster_group: str = ""
    verification_status: str = "Unknown"
    status: str = "Pending"
    error_message: str = ""
    id: int | None = None
