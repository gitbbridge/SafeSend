import re

EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def normalize_email(email: str) -> str:
    return email.strip().lower()


def require_footer(text: str) -> bool:
    lowered = text.lower()
    return "unsubscribe" in lowered or "opt out" in lowered or "opt-out" in lowered
