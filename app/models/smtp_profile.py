from dataclasses import dataclass


@dataclass(slots=True)
class SMTPProfile:
    profile_name: str
    host: str
    port: int
    username: str
    password: str
    from_name: str
    from_email: str
    reply_to_email: str
    security_mode: str
    daily_limit: int
    hourly_limit: int
    max_connections: int = 1
    enabled: bool = True
    notes: str = ""
    id: int | None = None
    error_counter: int = 0
    sent_today: int = 0
    failed_today: int = 0
    last_test_at: str | None = None
    last_test_status: str = "Not tested"
    last_error: str = ""
    resolved_ip: str = ""
    resolved_hostname: str = ""
    last_successful_send_at: str | None = None
    last_used_at: str | None = None
