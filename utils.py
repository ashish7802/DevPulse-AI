from __future__ import annotations

from collections import Counter
from datetime import date, timedelta


def clamp_score(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(value, maximum))


def consecutive_streak(days: list[date]) -> int:
    if not days:
        return 0

    unique_days = sorted(set(days), reverse=True)
    streak = 1
    previous = unique_days[0]
    for current in unique_days[1:]:
        if previous - current == timedelta(days=1):
            streak += 1
            previous = current
            continue
        break
    return streak


def percentage_breakdown(language_totals: Counter[str], limit: int = 5) -> list[tuple[str, float]]:
    total = sum(language_totals.values())
    if total == 0:
        return []

    return [
        (language, round((amount / total) * 100, 1))
        for language, amount in language_totals.most_common(limit)
    ]
