from dataclasses import dataclass


@dataclass(frozen=True)
class Recommendation:
    setting_key: str
    label: str
    recommended_default: str
    recommended_range: str
    description: str
    what_it_controls: str
    why_it_matters: str
    increase_benefits: str
    decrease_benefits: str
    risks: str
    best_practice: str
    related_settings: tuple[str, ...] = ()


RECOMMENDATIONS = {
    "delay_seconds": Recommendation(
        "delay_seconds",
        "Delay between emails",
        "30 seconds",
        "15 to 120 seconds",
        "Time SafeSend should wait between individual sends when a sending engine is active.",
        "Controls pacing between recipients.",
        "Human-like pacing reduces provider throttling and reputation spikes.",
        "A higher delay lowers pressure on SMTP servers and destination providers.",
        "A lower delay finishes queues faster when reputation and infrastructure are mature.",
        "Very low delays can look automated, trigger rate limits, and increase failures.",
        "Start at 30 seconds, then adjust slowly after reports show stable delivery.",
        ("random_delay_min", "random_delay_max", "max_emails_per_hour"),
    ),
    "random_delay_min": Recommendation(
        "random_delay_min",
        "Random delay min",
        "10 seconds",
        "5 to 60 seconds",
        "Lower bound for random pacing variation.",
        "Controls the shortest extra pause SafeSend can add between sends.",
        "Variation avoids mechanical timing patterns.",
        "Increasing the minimum makes sending gentler and more irregular.",
        "Decreasing it improves speed but reduces randomness.",
        "Too low a value can make traffic appear overly uniform.",
        "Use a small but meaningful minimum and keep it below the max delay.",
        ("random_delay_max", "delay_seconds"),
    ),
    "random_delay_max": Recommendation(
        "random_delay_max",
        "Random delay max",
        "45 seconds",
        "20 to 180 seconds",
        "Upper bound for random pacing variation.",
        "Controls the longest extra pause SafeSend can add between sends.",
        "Randomness helps reputation by preventing predictable bursts.",
        "Increasing it makes sending safer for new infrastructure.",
        "Decreasing it makes sending more predictable and faster.",
        "Too high can make queues take much longer than planned.",
        "Keep this above the minimum and review queue estimates before sending.",
        ("random_delay_min", "delay_seconds", "max_emails_per_hour"),
    ),
    "max_emails_per_hour": Recommendation(
        "max_emails_per_hour",
        "Max emails per hour",
        "100",
        "25 to 250 for new infrastructure",
        "Maximum number of messages allowed per hour.",
        "Controls hourly throughput.",
        "Hourly caps prevent sudden spikes that harm SMTP and domain reputation.",
        "Increasing can improve throughput after reputation is proven.",
        "Decreasing protects new, cold, or recovering sender infrastructure.",
        "High hourly limits can cause throttling, bounces, and blacklist risk.",
        "Use lower limits during warm-up and raise only after reports stay healthy.",
        ("delay_seconds", "max_emails_per_day", "max_connections"),
    ),
    "max_emails_per_day": Recommendation(
        "max_emails_per_day",
        "Max emails per day",
        "500",
        "100 to 1000 for warmed infrastructure",
        "Maximum number of messages allowed per day.",
        "Controls daily volume exposure.",
        "Daily caps keep sending growth gradual and reputation-friendly.",
        "Increasing raises campaign capacity.",
        "Decreasing reduces risk on new domains, new IPs, or recently repaired reputation.",
        "Aggressive daily volume can damage sender reputation quickly.",
        "Scale daily volume gradually and monitor failures before increasing.",
        ("max_emails_per_hour", "daily_limit", "verification_status"),
    ),
    "daily_limit": Recommendation(
        "daily_limit",
        "Daily send limit",
        "500",
        "100 to 1000",
        "Maximum daily send allowance for this SMTP profile.",
        "Controls how much one SMTP profile can contribute each day.",
        "Per-profile limits prevent one account from carrying too much risk.",
        "Increasing improves capacity for trusted senders.",
        "Decreasing protects fragile accounts and new sender identities.",
        "Too high can trigger provider limits or reputation penalties.",
        "Match the value to provider limits and sender warm-up age.",
        ("hourly_limit", "max_connections", "enabled"),
    ),
    "hourly_limit": Recommendation(
        "hourly_limit",
        "Hourly send limit",
        "100",
        "25 to 250",
        "Maximum hourly send allowance for this SMTP profile.",
        "Controls hourly pressure on a single SMTP profile.",
        "Hourly pacing prevents bursts and provider throttling.",
        "Increasing can improve throughput when reports are stable.",
        "Decreasing makes sending safer during warm-up or after failures.",
        "High limits may cause connection refusals, throttling, or spam filtering.",
        "Keep hourly limits conservative and below provider thresholds.",
        ("daily_limit", "delay_seconds", "max_connections"),
    ),
    "max_connections": Recommendation(
        "max_connections",
        "Max connections",
        "1",
        "1 to 3",
        "Number of simultaneous SMTP connections SafeSend may use for this profile.",
        "Controls connection concurrency.",
        "Lower concurrency is safer for reputation and provider trust.",
        "Increasing may improve throughput after infrastructure is proven.",
        "Decreasing reduces provider load and connection errors.",
        "Too many connections can look abusive and trigger temporary blocks.",
        "Use one connection by default; increase only with a known provider limit.",
        ("hourly_limit", "daily_limit", "security_mode"),
    ),
    "security_mode": Recommendation(
        "security_mode",
        "Security",
        "STARTTLS",
        "STARTTLS or SSL/TLS",
        "Encryption mode for SMTP login and transport.",
        "Controls how SafeSend secures the SMTP session.",
        "Encrypted transport protects credentials and improves provider compatibility.",
        "Stronger security improves trust and confidentiality.",
        "Lowering security is rarely beneficial except for legacy internal servers.",
        "No encryption can expose credentials and fail modern provider requirements.",
        "Use STARTTLS on port 587 or SSL/TLS on port 465 unless your provider states otherwise.",
        ("SMTP port", "Username", "Password"),
    ),
    "enabled": Recommendation(
        "enabled",
        "Enabled",
        "Enabled only after testing",
        "Enabled or disabled",
        "Whether SafeSend may use this configuration.",
        "Controls availability of a profile or feature.",
        "Disabled items cannot be accidentally used.",
        "Enabling makes the profile available to workflows.",
        "Disabling protects against untested or risky infrastructure.",
        "Leaving untested profiles enabled can cause failed sends later.",
        "Enable only after connection and reputation checks look healthy.",
        ("last_test_status", "daily_limit", "hourly_limit"),
    ),
    "verification_enabled": Recommendation(
        "verification_enabled",
        "Verification",
        "Enabled",
        "Enabled",
        "Whether contacts should be checked before future sending.",
        "Controls list hygiene and bounce risk.",
        "Verification reduces invalid, risky, and unknown recipients.",
        "Increasing verification coverage improves reputation protection.",
        "Reducing verification may save API usage but increases delivery risk.",
        "Skipping verification can increase bounces and suppressions.",
        "Verify imported contacts before any meaningful send volume.",
        ("Emailable API key", "suppression", "verification_status"),
    ),
}


PAGE_DEFAULTS = {
    "Dashboard": ("max_emails_per_day", "verification_enabled"),
    "Campaigns": ("delay_seconds", "max_emails_per_hour", "verification_enabled"),
    "Compose": ("required_footer", "verification_enabled"),
    "Contacts / Lists": ("verification_enabled",),
    "SMTP Servers": ("daily_limit", "hourly_limit", "max_connections", "security_mode"),
    "Sending Rules": ("delay_seconds", "random_delay_min", "random_delay_max", "max_emails_per_hour", "max_emails_per_day"),
    "Clustering / Reputation Strategy": ("max_emails_per_hour",),
    "Verification": ("verification_enabled",),
    "Sending Queue": ("delay_seconds", "max_emails_per_hour"),
    "Reports / Logs": ("max_emails_per_day",),
    "Suppression List": ("verification_enabled",),
    "Settings": ("verification_enabled",),
}


def normalize_key(label_or_key: str) -> str:
    value = (label_or_key or "").strip().lower().replace("/", " ").replace("-", " ")
    aliases = {
        "delay between emails": "delay_seconds",
        "random delay min": "random_delay_min",
        "random delay max": "random_delay_max",
        "max emails per hour": "max_emails_per_hour",
        "max emails per day": "max_emails_per_day",
        "daily limit": "daily_limit",
        "daily send limit": "daily_limit",
        "hourly limit": "hourly_limit",
        "hourly send limit": "hourly_limit",
        "max connections": "max_connections",
        "security": "security_mode",
        "enabled": "enabled",
        "emailable api key": "verification_enabled",
    }
    return aliases.get(value, value.replace(" ", "_"))


def get_recommendation(label_or_key: str) -> Recommendation:
    key = normalize_key(label_or_key)
    return RECOMMENDATIONS.get(
        key,
        Recommendation(
            key,
            label_or_key,
            "Use the conservative default",
            "Depends on your account and provider",
            "This setting changes how SafeSend behaves.",
            "Controls one part of the current workflow.",
            "Clear configuration reduces mistakes and makes sending more predictable.",
            "Increasing may improve speed or capacity when infrastructure is proven.",
            "Decreasing usually reduces operational risk.",
            "Incorrect values can cause failed work, confusing reports, or deliverability problems.",
            "Change one setting at a time and review results before making another change.",
            (),
        ),
    )


def recommendations_for_page(page: str) -> list[Recommendation]:
    return [get_recommendation(key) for key in PAGE_DEFAULTS.get(page, ("verification_enabled",))]

