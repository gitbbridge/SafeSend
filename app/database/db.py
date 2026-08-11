import sqlite3
import os
import shutil
from pathlib import Path
from typing import Any, Iterable
from datetime import datetime, timezone

from app.database.schema import (
    CONTACT_LIST_MIGRATIONS,
    CONTACT_MIGRATIONS,
    CAMPAIGN_MIGRATIONS,
    DEFAULT_SETTINGS,
    SCHEMA_STATEMENTS,
    SCHEMA_MIGRATIONS,
    SMTP_PROFILE_MIGRATIONS,
    SUPPRESSION_MIGRATIONS,
    TEMPLATE_MIGRATIONS,
)
from app.utils.paths import DATA_DIR

DB_PATH = Path(os.environ.get("SAFESEND_DB_PATH", DATA_DIR / "safesend.db"))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    _backup_before_pending_migrations()
    with get_connection() as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        _ensure_columns(conn, "smtp_profiles", SMTP_PROFILE_MIGRATIONS)
        _ensure_columns(conn, "contact_lists", CONTACT_LIST_MIGRATIONS)
        _ensure_columns(conn, "contacts", CONTACT_MIGRATIONS)
        _ensure_columns(conn, "campaigns", CAMPAIGN_MIGRATIONS)
        _ensure_columns(conn, "suppression_list", SUPPRESSION_MIGRATIONS)
        _ensure_columns(conn, "templates", TEMPLATE_MIGRATIONS)
        _normalize_smtp_security(conn)
        _normalize_suppression_rows(conn)
        _ensure_schema_migrations(conn)
        _run_schema_migrations(conn)
        _refresh_contact_list_counts(conn)
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        conn.commit()


def _backup_before_pending_migrations() -> Path | None:
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        return None
    if not _has_pending_schema_migrations():
        return None
    backup_dir = DB_PATH.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"safesend_pre_migration_{stamp}.db"
    shutil.copy2(DB_PATH, backup_path)
    return backup_path


def _has_pending_schema_migrations() -> bool:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            has_table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
            ).fetchone()
            applied = set()
            if has_table:
                applied = {int(row[0]) for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
            for version, _name, statements in SCHEMA_MIGRATIONS:
                if version not in applied:
                    for statement in statements:
                        if "CREATE TABLE IF NOT EXISTS send_jobs" in statement:
                            exists = conn.execute(
                                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'send_jobs'"
                            ).fetchone()
                            if not exists:
                                return True
                    return True
    except sqlite3.DatabaseError:
        return True
    return False


def _ensure_schema_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _run_schema_migrations(conn: sqlite3.Connection) -> None:
    applied = {int(row["version"]) for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}
    for version, name, statements in SCHEMA_MIGRATIONS:
        if version in applied:
            continue
        for statement in statements:
            conn.execute(statement)
        conn.execute("INSERT INTO schema_migrations (version, name) VALUES (?, ?)", (version, name))
    _seed_provider_rate_limits(conn)


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: list[tuple[str, str]]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, definition in columns:
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def _normalize_smtp_security(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE smtp_profiles SET security_mode = 'SSL/TLS' WHERE security_mode = 'SSL'")
    conn.execute("UPDATE smtp_profiles SET security_mode = 'STARTTLS' WHERE security_mode = 'TLS'")


def _normalize_suppression_rows(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        UPDATE suppression_list
        SET normalized_email = lower(trim(email))
        WHERE normalized_email IS NULL OR normalized_email = ''
        """
    )
    conn.execute(
        """
        UPDATE suppression_list
        SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
        """
    )


def _seed_provider_rate_limits(conn: sqlite3.Connection) -> None:
    for provider in ("MICROSOFT_365", "GOOGLE_WORKSPACE", "OTHER", "UNKNOWN"):
        conn.execute(
            """
            INSERT OR IGNORE INTO provider_rate_limits (
                provider_cluster, hourly_limit, daily_limit, min_interval_seconds, enabled
            ) VALUES (?, NULL, NULL, 0, 1)
            """,
            (provider,),
        )


def _refresh_contact_list_counts(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        UPDATE contact_lists
        SET total_contacts = (
            SELECT COUNT(*) FROM contacts WHERE contacts.list_id = contact_lists.id
        )
        """
    )


def fetch_all(query: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(query, tuple(params)).fetchall()


def fetch_one(query: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(query, tuple(params)).fetchone()


def execute(query: str, params: Iterable[Any] = ()) -> int:
    with get_connection() as conn:
        cur = conn.execute(query, tuple(params))
        conn.commit()
        return int(cur.lastrowid or 0)


def execute_many(query: str, rows: Iterable[Iterable[Any]]) -> None:
    with get_connection() as conn:
        conn.executemany(query, rows)
        conn.commit()


def dashboard_counts() -> dict[str, int]:
    tables = {
        "smtp_profiles": "smtp_profiles",
        "contact_lists": "contact_lists",
        "contacts": "contacts",
        "campaigns": "campaigns",
        "queued": "send_queue WHERE status = 'Pending'",
        "sent": "send_queue WHERE status = 'Sent'",
        "failed": "send_queue WHERE status = 'Failed'",
        "suppressed": "suppression_list",
    }
    counts: dict[str, int] = {}
    with get_connection() as conn:
        for key, table_expr in tables.items():
            counts[key] = int(conn.execute(f"SELECT COUNT(*) FROM {table_expr}").fetchone()[0])
    return counts
