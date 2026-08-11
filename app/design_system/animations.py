from dataclasses import dataclass


@dataclass(frozen=True)
class AnimationSpec:
    hover_ms: int = 120
    press_ms: int = 80
    tooltip_delay_ms: int = 250
    loading_pulse_ms: int = 900


ANIMATION = AnimationSpec()

