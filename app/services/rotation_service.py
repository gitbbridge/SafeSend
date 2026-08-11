import random


class RotationService:
    def choose_profile(self, profiles: list[dict], mode: str = "round_robin", index: int = 0) -> dict | None:
        usable = [
            profile
            for profile in profiles
            if profile.get("enabled")
            and int(profile.get("sent_today") or 0) < int(profile.get("daily_limit") or 0)
        ]
        if not usable:
            return None
        if mode == "random":
            return random.choice(usable)
        if mode == "limit_then_next":
            return usable[0]
        if mode == "weighted":
            weights = [max(1, int(profile.get("daily_limit") or 1)) for profile in usable]
            return random.choices(usable, weights=weights, k=1)[0]
        return usable[index % len(usable)]
