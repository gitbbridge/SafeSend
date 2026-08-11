import re
from dataclasses import dataclass


SPAM_WORDS = {
    "free",
    "guarantee",
    "urgent",
    "act now",
    "limited time",
    "risk-free",
    "winner",
    "cash",
    "bonus",
    "buy now",
    "click here",
    "congratulations",
    "lowest price",
}

MERGE_RE = re.compile(r"{{\s*([A-Za-z0-9_]+)\s*}}")
URL_RE = re.compile(r"https?://[^\s\"'<>]+")


@dataclass(slots=True)
class SpamAnalysis:
    score: int
    warnings: list[str]
    suggestions: list[str]


class SpamAnalysisService:
    def analyze(self, subject: str, html_body: str, preheader: str = "") -> SpamAnalysis:
        warnings: list[str] = []
        suggestions: list[str] = []
        score = 0
        text = f"{subject} {preheader} {self._strip_tags(html_body)}"
        lowered = text.lower()

        if not subject.strip():
            score += 20
            warnings.append("Missing subject line.")
        if len(subject) > 78:
            score += 8
            suggestions.append("Subject is long; keep it under 78 characters for most inboxes.")
        if subject and subject.upper() == subject and any(ch.isalpha() for ch in subject):
            score += 10
            warnings.append("Subject uses all caps.")
        exclamations = text.count("!")
        if exclamations > 3:
            score += min(20, exclamations * 2)
            warnings.append("Too many exclamation marks.")
        for word in sorted(SPAM_WORDS):
            if word in lowered:
                score += 5
                suggestions.append(f"Review spam trigger phrase: {word}.")
        if "unsubscribe" not in lowered and "{{unsubscribe" not in lowered:
            score += 12
            warnings.append("Missing unsubscribe placeholder or language.")
        broken_tags = [tag for tag in re.findall(r"{{[^}]*$|^[^{]*}}", html_body)]
        allowed = {"FirstName", "LastName", "Company", "Email", "State", "City", "Custom1", "Custom2", "Custom3", "Unsubscribe"}
        for tag in MERGE_RE.findall(html_body + subject + preheader):
            if tag not in allowed:
                score += 4
                warnings.append(f"Unknown merge field: {{{{{tag}}}}}.")
        if broken_tags:
            score += 10
            warnings.append("Possible broken merge field syntax.")
        images = len(re.findall(r"<img\b", html_body, flags=re.IGNORECASE))
        words = len(text.split())
        if images and words < images * 20:
            score += 10
            suggestions.append("Image-to-text ratio may be high.")
        for url in URL_RE.findall(html_body):
            if "." not in url.split("//", 1)[1]:
                score += 6
                warnings.append(f"Link may be malformed: {url}.")
        if not warnings and not suggestions:
            suggestions.append("Looks good. Keep testing with your real audience and compliance footer.")
        return SpamAnalysis(min(score, 100), warnings, suggestions)

    def _strip_tags(self, html: str) -> str:
        return re.sub(r"<[^>]+>", " ", html or "")
