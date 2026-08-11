from dataclasses import dataclass


@dataclass(slots=True)
class Campaign:
    name: str
    subject: str
    html_body: str = ""
    plain_text_body: str = ""
    contact_list_id: int | None = None
    smtp_pool: str = ""
    attachments: str = ""
    footer_text: str = ""
    status: str = "Draft"
    scheduled_at: str = ""
    id: int | None = None
