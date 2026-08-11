from app.help.help_topics import HELP_TOPICS
from app.help.page_intros import PAGE_INTROS
from app.help.recommendations import RECOMMENDATIONS
from app.help.tips import TIPS


def search_help(query: str) -> list[tuple[str, str]]:
    needle = (query or "").strip().lower()
    results: list[tuple[str, str]] = []
    if not needle:
        return [(title, body) for title, body in HELP_TOPICS.items()]
    for title, body in HELP_TOPICS.items():
        if needle in title.lower() or needle in body.lower():
            results.append((title, body))
    for page, body in PAGE_INTROS.items():
        if needle in page.lower() or needle in body.lower():
            results.append((f"Page: {page}", body))
    for rec in RECOMMENDATIONS.values():
        haystack = " ".join([rec.label, rec.description, rec.why_it_matters, rec.best_practice]).lower()
        if needle in haystack:
            results.append((f"Setting: {rec.label}", rec.best_practice))
    for tip in TIPS:
        if needle in tip.lower():
            results.append(("Tip", tip))
    return results[:50]

