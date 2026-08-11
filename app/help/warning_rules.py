from app.help.recommendations import normalize_key


def _number(value) -> float | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def evaluate_setting(setting_key: str, value) -> list[str]:
    key = normalize_key(setting_key)
    number = _number(value)
    warnings: list[str] = []
    if key in {"delay_seconds", "delay_between_emails"} and number is not None and number < 15:
        warnings.append("Delay is very low. Fast pacing can look automated and may increase throttling or spam filtering.")
    if key in {"max_emails_per_hour", "hourly_limit"} and number is not None and number > 250:
        warnings.append("Hourly volume is aggressive. Increase only after reports show stable delivery and low failure rates.")
    if key in {"max_emails_per_day", "daily_limit"} and number is not None and number > 1000:
        warnings.append("Daily volume is high. New or recovering infrastructure should warm up gradually before this level.")
    if key == "max_connections" and number is not None and number > 3:
        warnings.append("Multiple SMTP connections can trigger provider limits. One connection is safest for most accounts.")
    if key == "verification_enabled" and str(value).strip().lower() in {"0", "false", "disabled", "off", "no"}:
        warnings.append("Verification appears disabled. Unverified contacts increase bounce and reputation risk.")
    if key in {"suppression", "suppression_enabled"} and str(value).strip().lower() in {"0", "false", "disabled", "off", "no"}:
        warnings.append("Suppression appears disabled. Suppression protects compliance and prevents accidental future sends.")
    return warnings


def evaluate_settings(settings: dict) -> list[str]:
    messages: list[str] = []
    for key, value in settings.items():
        messages.extend(evaluate_setting(key, value))
    return messages

