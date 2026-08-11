SMTP_TIPS = [
    "SMTP warm-up works best when volume grows gradually and failures stay low.",
    "STARTTLS on port 587 is the safest default for many modern SMTP providers.",
    "A successful SMTP login test does not guarantee good inbox placement.",
    "Use one SMTP connection until your provider and reputation can support more.",
    "Provider throttling is often a signal to slow down before failures increase.",
    "A dedicated reply-to address helps users respond without hurting operations.",
    "Consistent from names help recipients recognize your mail.",
    "New domains should avoid sudden spikes in daily volume.",
    "SMTP errors should be reviewed before increasing limits.",
    "Authentication and reputation checks work together; neither replaces the other.",
]

VERIFICATION_TIPS = [
    "Verification reduces invalid recipients before they become bounces.",
    "Risky contacts should be treated conservatively until reports prove they are safe.",
    "Unknown verification status is not the same as deliverable.",
    "Verify newly imported lists before adding them to a campaign.",
    "Repeated bounces can damage domain and IP reputation.",
    "Verification data becomes stale as people change jobs or abandon inboxes.",
    "Suppressed invalid emails protect future campaigns from repeated mistakes.",
    "Deliverable contacts can still complain if targeting is poor.",
    "Verification is list hygiene, not permission proof.",
    "Review verification summaries before building a queue.",
]

WARMUP_TIPS = [
    "Warm-up is about trust over time, not simply sending more mail.",
    "Small consistent sends are safer than occasional bursts.",
    "Increase volume only after several healthy reporting periods.",
    "A new mailbox should not immediately use the same limits as an established one.",
    "Quiet hours make sending patterns feel more natural.",
    "Destination providers prefer predictable, low-complaint traffic.",
    "A sudden jump from zero to high volume is a common reputation risk.",
    "Warm-up should pause if failures or complaints rise.",
    "Different domains and SMTP accounts may warm up at different speeds.",
    "Conservative defaults protect future sending capacity.",
]

MX_TIPS = [
    "MX records identify where a recipient domain receives mail.",
    "Grouping by destination infrastructure can reduce provider-specific bursts.",
    "Many domains share the same mailbox provider behind different domain names.",
    "Provider-level throttling can affect many recipient domains at once.",
    "Recipient infrastructure review helps explain unusual delivery patterns.",
    "MX clustering can reveal whether one provider dominates a list.",
    "Destination diversity is healthier than sending a whole list to one provider at once.",
    "Large clusters should be paced more carefully.",
    "Infrastructure analysis is most useful before queue creation.",
    "MX data supports strategy; it does not replace permission and relevance.",
]

DELIVERABILITY_TIPS = [
    "Deliverability improves when recipients expect and want your email.",
    "Clear subject lines reduce complaints and confusion.",
    "A compliant footer builds trust and supports opt-out expectations.",
    "Suppressions are reputation protection, not just compliance paperwork.",
    "High open rates cannot compensate for poor list quality forever.",
    "Consistent identity helps mailbox providers understand your traffic.",
    "Low failure rates are a signal that pacing and list quality are working.",
    "Spammy formatting can hurt trust even with verified contacts.",
    "A simple readable email often performs better than an overdesigned one.",
    "Reports should guide the next campaign, not just summarize the last one.",
]

QUEUE_TIPS = [
    "Queue review is the last chance to catch risky recipients before sending.",
    "Suppressed contacts should never be intentionally queued.",
    "Risky and unknown recipients should be included only with a clear reason.",
    "Queue size should match SMTP limits and business hours.",
    "A smaller queue is easier to monitor during warm-up.",
    "Paused queues are safer than forcing sends through failures.",
    "Queue order can affect how traffic hits destination providers.",
    "Review campaign readiness before building the queue.",
    "Queue failures often point to configuration or pacing issues.",
    "A queue is an operational plan, not just a recipient list.",
]

REPUTATION_TIPS = [
    "Blacklist checks are signals, not final judgments.",
    "A clean blacklist result does not guarantee inbox placement.",
    "If an IP is listed, pause and investigate before increasing volume.",
    "Reputation problems often come from repeated small mistakes.",
    "Provider blocks can happen before public blacklist listings appear.",
    "Reputation improves through consistent, wanted, low-failure sending.",
    "One poor sender can affect a shared SMTP environment.",
    "Monitor reputation after configuration changes.",
    "Healthy sending requires both technical setup and good recipient targeting.",
    "Conservative sending is cheaper than reputation recovery.",
]

COMPLIANCE_TIPS = [
    "Suppression requests should be treated as permanent unless policy says otherwise.",
    "A clear unsubscribe path reduces complaints.",
    "Do not re-import suppressed contacts as active recipients.",
    "Internal notes help explain why a contact or list was suppressed.",
    "Permission quality matters as much as email validity.",
    "Exported lists should preserve suppression awareness.",
    "Avoid sending to contacts with unclear source or consent.",
    "Compliance settings protect brand trust as well as legal posture.",
    "Keep suppression workflows simple so they are hard to bypass accidentally.",
    "When in doubt, do not send until the contact status is clear.",
]

REPORTING_TIPS = [
    "Reports are most valuable when reviewed before the next send.",
    "Failure trends are often more useful than single failures.",
    "Compare reports by SMTP profile to identify weak infrastructure.",
    "High failure rates should trigger slower pacing.",
    "Review suppressed counts after every meaningful import.",
    "Unknown outcomes deserve follow-up before scaling volume.",
    "Daily summaries help spot problems earlier than monthly reviews.",
    "A stable campaign process should produce predictable reports.",
    "Logs help explain what happened when UI status is not enough.",
    "Use reports to improve defaults, not just to prove activity.",
]

TIPS = SMTP_TIPS + VERIFICATION_TIPS + WARMUP_TIPS + MX_TIPS + DELIVERABILITY_TIPS + QUEUE_TIPS + REPUTATION_TIPS + COMPLIANCE_TIPS + REPORTING_TIPS + [
    "Learning Mode can be turned off when your team no longer needs detailed explanations.",
    "SafeSend favors conservative defaults because reputation is difficult to repair.",
    "Change one major setting at a time so reports remain easy to interpret.",
    "Document unusual settings in notes so future users understand the reason.",
    "A commercial sending workflow should be repeatable, explainable, and cautious.",
    "Healthy systems make risky choices visible before they become incidents.",
    "Configuration guidance is most useful before saving, not after something fails.",
    "If a setting feels unclear, use the Help Center before increasing volume.",
    "SafeSend is designed to teach the why behind each operational setting.",
    "The safest sending plan is the one your reports can support.",
]


def did_you_know(index: int = 0) -> str:
    return TIPS[index % len(TIPS)]

