from dataclasses import dataclass

from app.help.recommendations import get_recommendation


@dataclass(frozen=True)
class FieldHelp:
    setting_name: str
    recommended_default: str
    recommended_range: str
    description: str
    what_it_controls: str
    why_it_matters: str
    increase_benefits: str
    decrease_benefits: str
    risks: str
    best_practice: str
    related_settings: tuple[str, ...]

    def tooltip_text(self) -> str:
        related = ", ".join(self.related_settings) if self.related_settings else "None"
        return "\n".join(
            [
                self.setting_name,
                f"Recommended default: {self.recommended_default}",
                f"Recommended range: {self.recommended_range}",
                f"Description: {self.description}",
                f"Controls: {self.what_it_controls}",
                f"Why it matters: {self.why_it_matters}",
                f"Increase benefits: {self.increase_benefits}",
                f"Decrease benefits: {self.decrease_benefits}",
                f"Risks: {self.risks}",
                f"Best practice: {self.best_practice}",
                f"Related settings: {related}",
            ]
        )


FIELD_HELP = {}


def get_field_help(label_or_key: str) -> FieldHelp:
    rec = get_recommendation(label_or_key)
    return FieldHelp(
        rec.label,
        rec.recommended_default,
        rec.recommended_range,
        rec.description,
        rec.what_it_controls,
        rec.why_it_matters,
        rec.increase_benefits,
        rec.decrease_benefits,
        rec.risks,
        rec.best_practice,
        rec.related_settings,
    )

