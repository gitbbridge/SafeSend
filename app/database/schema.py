SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS smtp_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_name TEXT NOT NULL,
        host TEXT NOT NULL,
        port INTEGER NOT NULL DEFAULT 587,
        username TEXT,
        password TEXT,
        from_name TEXT,
        from_email TEXT NOT NULL,
        reply_to_email TEXT,
        security_mode TEXT NOT NULL DEFAULT 'STARTTLS',
        daily_limit INTEGER NOT NULL DEFAULT 500,
        hourly_limit INTEGER NOT NULL DEFAULT 100,
        max_connections INTEGER NOT NULL DEFAULT 1,
        enabled INTEGER NOT NULL DEFAULT 1,
        notes TEXT,
        error_counter INTEGER NOT NULL DEFAULT 0,
        sent_today INTEGER NOT NULL DEFAULT 0,
        failed_today INTEGER NOT NULL DEFAULT 0,
        last_test_at TEXT,
        last_test_status TEXT NOT NULL DEFAULT 'Not tested',
        last_error TEXT,
        resolved_ip TEXT,
        resolved_hostname TEXT,
        last_successful_send_at TEXT,
        last_used_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS contact_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        source_file TEXT,
        total_contacts INTEGER NOT NULL DEFAULT 0,
        duplicate_count INTEGER NOT NULL DEFAULT 0,
        archived INTEGER NOT NULL DEFAULT 0,
        notes TEXT,
        last_imported_at TEXT,
        last_verified_at TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER NOT NULL,
        email TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        company TEXT,
        phone TEXT,
        address TEXT,
        city TEXT,
        state TEXT,
        zip TEXT,
        country TEXT,
        custom1 TEXT,
        custom2 TEXT,
        custom3 TEXT,
        source_list TEXT,
        cluster_key TEXT,
        cluster_group TEXT,
        cluster_size INTEGER NOT NULL DEFAULT 0,
        is_clustered INTEGER NOT NULL DEFAULT 0,
        is_suppressed INTEGER NOT NULL DEFAULT 0,
        verification_status TEXT NOT NULL DEFAULT 'Unknown',
        verification_category TEXT,
        send_priority INTEGER NOT NULL DEFAULT 0,
        last_sent_at TEXT,
        last_verified_at TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (list_id) REFERENCES contact_lists(id) ON DELETE CASCADE,
        UNIQUE(list_id, email)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        tags TEXT,
        internal_notes TEXT,
        subject TEXT NOT NULL,
        html_body TEXT,
        plain_text_body TEXT,
        contact_list_id INTEGER,
        template_id INTEGER,
        smtp_profile_id INTEGER,
        smtp_pool TEXT,
        attachments TEXT,
        footer_text TEXT,
        status TEXT NOT NULL DEFAULT 'Draft',
        archived INTEGER NOT NULL DEFAULT 0,
        scheduled_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contact_list_id) REFERENCES contact_lists(id),
        FOREIGN KEY (template_id) REFERENCES templates(id),
        FOREIGN KEY (smtp_profile_id) REFERENCES smtp_profiles(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campaign_recipients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        contact_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS send_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER,
        contact_id INTEGER,
        smtp_profile_id INTEGER,
        recipient_email TEXT NOT NULL,
        recipient_name TEXT,
        cluster_group TEXT,
        verification_status TEXT,
        status TEXT NOT NULL DEFAULT 'Pending',
        scheduled_at TEXT,
        sent_at TEXT,
        error_message TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
        FOREIGN KEY (smtp_profile_id) REFERENCES smtp_profiles(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS send_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER,
        queue_item_id INTEGER,
        smtp_profile_id INTEGER,
        recipient_email TEXT,
        status TEXT NOT NULL,
        message TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS suppression_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        reason TEXT,
        scope TEXT NOT NULL DEFAULT 'Global',
        campaign_id INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS verification_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        category TEXT,
        raw_response TEXT,
        verified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cluster_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER,
        cluster_key TEXT NOT NULL,
        cluster_group TEXT NOT NULL,
        cluster_size INTEGER NOT NULL,
        risk_notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (list_id) REFERENCES contact_lists(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS smtp_blacklist_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        smtp_profile_id INTEGER NOT NULL,
        zone TEXT NOT NULL,
        query TEXT NOT NULL,
        listed INTEGER NOT NULL DEFAULT 0,
        response TEXT,
        error_message TEXT,
        checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (smtp_profile_id) REFERENCES smtp_profiles(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        subject TEXT,
        preheader TEXT,
        from_name TEXT,
        from_email TEXT,
        reply_to_email TEXT,
        html_body TEXT,
        plain_text_body TEXT,
        category TEXT NOT NULL DEFAULT 'General',
        status TEXT NOT NULL DEFAULT 'Draft',
        tags TEXT,
        favorite INTEGER NOT NULL DEFAULT 0,
        archived INTEGER NOT NULL DEFAULT 0,
        times_used INTEGER NOT NULL DEFAULT 0,
        last_used_at TEXT,
        created_by TEXT NOT NULL DEFAULT 'Local User',
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS template_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        version_number INTEGER NOT NULL,
        name TEXT,
        subject TEXT,
        preheader TEXT,
        html_body TEXT,
        plain_text_body TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS signatures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        html_body TEXT,
        plain_text_body TEXT,
        is_default INTEGER NOT NULL DEFAULT 0,
        archived INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER,
        subject TEXT NOT NULL,
        label TEXT,
        is_preferred INTEGER NOT NULL DEFAULT 0,
        ab_group TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER,
        name TEXT,
        subject TEXT,
        preheader TEXT,
        from_name TEXT,
        from_email TEXT,
        reply_to_email TEXT,
        html_body TEXT,
        plain_text_body TEXT,
        source_mode INTEGER NOT NULL DEFAULT 0,
        saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campaign_lists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        contact_list_id INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (contact_list_id) REFERENCES contact_lists(id) ON DELETE CASCADE,
        UNIQUE(campaign_id, contact_list_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campaign_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL UNIQUE,
        template_id INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campaign_rules (
        campaign_id INTEGER PRIMARY KEY,
        send_rate TEXT,
        delay_between_emails TEXT,
        max_per_hour TEXT,
        max_per_day TEXT,
        business_hours TEXT,
        quiet_hours TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campaign_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        note TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campaign_filters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        filter_name TEXT,
        filter_value TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS campaign_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        file_path TEXT,
        display_name TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
    )
    """,
]


SMTP_PROFILE_MIGRATIONS = [
    ("max_connections", "INTEGER NOT NULL DEFAULT 1"),
    ("notes", "TEXT"),
    ("failed_today", "INTEGER NOT NULL DEFAULT 0"),
    ("last_test_at", "TEXT"),
    ("last_test_status", "TEXT NOT NULL DEFAULT 'Not tested'"),
    ("last_error", "TEXT"),
    ("resolved_ip", "TEXT"),
    ("resolved_hostname", "TEXT"),
    ("last_successful_send_at", "TEXT"),
]


CONTACT_LIST_MIGRATIONS = [
    ("duplicate_count", "INTEGER NOT NULL DEFAULT 0"),
    ("archived", "INTEGER NOT NULL DEFAULT 0"),
    ("notes", "TEXT"),
    ("last_imported_at", "TEXT"),
    ("last_verified_at", "TEXT"),
    ("updated_at", "TEXT"),
]


CONTACT_MIGRATIONS = [
    ("phone", "TEXT"),
    ("address", "TEXT"),
    ("city", "TEXT"),
    ("state", "TEXT"),
    ("zip", "TEXT"),
    ("country", "TEXT"),
    ("custom3", "TEXT"),
    ("is_suppressed", "INTEGER NOT NULL DEFAULT 0"),
    ("last_sent_at", "TEXT"),
    ("last_verified_at", "TEXT"),
    ("updated_at", "TEXT"),
]


CAMPAIGN_MIGRATIONS = [
    ("description", "TEXT"),
    ("tags", "TEXT"),
    ("internal_notes", "TEXT"),
    ("template_id", "INTEGER"),
    ("smtp_profile_id", "INTEGER"),
    ("archived", "INTEGER NOT NULL DEFAULT 0"),
]


SUPPRESSION_MIGRATIONS = [
    ("normalized_email", "TEXT"),
    ("source", "TEXT NOT NULL DEFAULT 'manual'"),
    ("message_id", "TEXT"),
    ("updated_at", "TEXT"),
    ("active", "INTEGER NOT NULL DEFAULT 1"),
]


TEMPLATE_MIGRATIONS = [
    ("category", "TEXT NOT NULL DEFAULT 'General'"),
    ("status", "TEXT NOT NULL DEFAULT 'Draft'"),
    ("tags", "TEXT"),
    ("last_used_at", "TEXT"),
    ("created_by", "TEXT NOT NULL DEFAULT 'Local User'"),
]


DEFAULT_SETTINGS = {
    "emailable_api_key": "",
    "cluster_threshold": "5",
    "cluster_strategy": "interleaved",
    "weighted_cluster_percentage": "20",
    "delay_seconds": "30",
    "random_delay_min": "10",
    "random_delay_max": "45",
    "max_emails_per_hour": "100",
    "max_emails_per_day": "500",
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00",
    "required_footer": "You are receiving this email because you opted in. Reply unsubscribe to opt out.",
    "email_validation_ttl_days": "30",
}


MILESTONE_5_9_SCHEMA_VERSION = 590


MILESTONE_5_9_MIGRATION = [
    """
    CREATE TABLE IF NOT EXISTS sending_domains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL UNIQUE,
        display_name TEXT,
        enabled INTEGER NOT NULL DEFAULT 1,
        verified INTEGER NOT NULL DEFAULT 0,
        warmup_status TEXT NOT NULL DEFAULT 'NOT_CONFIGURED',
        reputation_status TEXT NOT NULL DEFAULT 'UNKNOWN',
        daily_limit INTEGER,
        hourly_limit INTEGER,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS send_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        recipient_id INTEGER,
        email TEXT NOT NULL,
        normalized_email TEXT NOT NULL,
        recipient_domain TEXT,
        provider_cluster TEXT NOT NULL DEFAULT 'UNKNOWN',
        personalization_data TEXT,
        smtp_account_id INTEGER,
        sending_domain_id INTEGER,
        message_id TEXT,
        attempt_number INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'QUEUED',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        scheduled_at TEXT,
        started_at TEXT,
        completed_at TEXT,
        last_error TEXT,
        classification_rule_version TEXT NOT NULL DEFAULT '5.9.0',
        UNIQUE(campaign_id, normalized_email),
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (recipient_id) REFERENCES contacts(id) ON DELETE SET NULL,
        FOREIGN KEY (smtp_account_id) REFERENCES smtp_profiles(id) ON DELETE SET NULL,
        FOREIGN KEY (sending_domain_id) REFERENCES sending_domains(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS message_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL,
        send_job_id INTEGER,
        message_id TEXT NOT NULL UNIQUE,
        recipient_email TEXT NOT NULL,
        smtp_account_id INTEGER,
        sending_domain_id INTEGER,
        generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        sent_at TEXT,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
        FOREIGN KEY (send_job_id) REFERENCES send_jobs(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS validation_pool (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        normalized_email TEXT NOT NULL UNIQUE,
        validation_status TEXT NOT NULL DEFAULT 'UNKNOWN',
        validation_result TEXT,
        reason TEXT,
        score REAL,
        deliverable INTEGER,
        accept_all INTEGER,
        disposable INTEGER,
        role_address INTEGER,
        free_provider INTEGER,
        mx_found INTEGER,
        mx_records TEXT,
        provider_cluster TEXT NOT NULL DEFAULT 'UNKNOWN',
        validated_at TEXT,
        expires_at TEXT,
        validation_source TEXT,
        raw_provider_data TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS validation_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        normalized_email TEXT NOT NULL,
        validation_source TEXT NOT NULL,
        paid_lookup INTEGER NOT NULL DEFAULT 0,
        cache_hit INTEGER NOT NULL DEFAULT 0,
        result_status TEXT,
        reason TEXT,
        campaign_id INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS domain_mx_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL UNIQUE,
        mx_records TEXT,
        provider_cluster TEXT NOT NULL DEFAULT 'UNKNOWN',
        mx_status TEXT NOT NULL DEFAULT 'UNKNOWN',
        lookup_source TEXT,
        looked_up_at TEXT,
        expires_at TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mx_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT NOT NULL,
        lookup_source TEXT NOT NULL,
        paid_lookup INTEGER NOT NULL DEFAULT 0,
        cache_hit INTEGER NOT NULL DEFAULT 0,
        mx_status TEXT NOT NULL,
        provider_cluster TEXT NOT NULL DEFAULT 'UNKNOWN',
        error_message TEXT,
        campaign_id INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS smtp_account_state (
        smtp_profile_id INTEGER PRIMARY KEY,
        state TEXT NOT NULL DEFAULT 'AVAILABLE',
        sent_today INTEGER NOT NULL DEFAULT 0,
        sent_this_hour INTEGER NOT NULL DEFAULT 0,
        failed_today INTEGER NOT NULL DEFAULT 0,
        min_interval_seconds INTEGER NOT NULL DEFAULT 0,
        last_send_at TEXT,
        cooldown_until TEXT,
        auth_health TEXT NOT NULL DEFAULT 'UNKNOWN',
        last_error TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (smtp_profile_id) REFERENCES smtp_profiles(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS provider_rate_limits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_cluster TEXT NOT NULL,
        hourly_limit INTEGER,
        daily_limit INTEGER,
        min_interval_seconds INTEGER NOT NULL DEFAULT 0,
        enabled INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(provider_cluster)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_send_jobs_campaign_status_scheduled
    ON send_jobs (campaign_id, status, scheduled_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_send_jobs_provider_status
    ON send_jobs (provider_cluster, status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_validation_pool_expires
    ON validation_pool (normalized_email, expires_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_domain_mx_cache_expires
    ON domain_mx_cache (domain, expires_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_suppression_normalized_active
    ON suppression_list (normalized_email, active)
    """,
]


SCHEMA_MIGRATIONS = [
    (MILESTONE_5_9_SCHEMA_VERSION, "milestone_5_9_sending_engine_foundation", MILESTONE_5_9_MIGRATION),
]
