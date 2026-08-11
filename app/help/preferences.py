from app.database import db

LEARNING_MODE_KEY = "learning_mode"
GUIDED_CONFIGURATION_KEY = "guided_configuration"


def learning_mode_enabled(default: bool = True) -> bool:
    row = db.fetch_one("SELECT value FROM app_settings WHERE key = ?", (LEARNING_MODE_KEY,))
    if not row:
        return default
    return str(row["value"]).strip().lower() not in {"0", "false", "off", "no", "disabled"}


def set_learning_mode(enabled: bool) -> None:
    db.execute(
        """
        INSERT INTO app_settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """,
        (LEARNING_MODE_KEY, "1" if enabled else "0"),
    )


def guided_configuration_enabled(default: bool = True) -> bool:
    row = db.fetch_one("SELECT value FROM app_settings WHERE key = ?", (GUIDED_CONFIGURATION_KEY,))
    if not row:
        return default
    return str(row["value"]).strip().lower() not in {"0", "false", "off", "no", "disabled", "hidden"}


def set_guided_configuration(enabled: bool) -> None:
    db.execute(
        """
        INSERT INTO app_settings (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """,
        (GUIDED_CONFIGURATION_KEY, "1" if enabled else "0"),
    )
