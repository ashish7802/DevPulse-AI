from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from github_api import GitHubAPI, normalize_activity_count
from utils import clamp_score, consecutive_streak, percentage_breakdown


def analyze_user_profile(username: str) -> dict[str, Any]:
    api = GitHubAPI()
    user = api.get_user(username)
    repos = [repo for repo in api.get_user_repos(username) if not repo.get("fork")]

    language_totals: Counter[str] = Counter()
    for repo in repos:
        languages = api.get_repo_languages(repo["owner"]["login"], repo["name"])
        language_totals.update(languages)

    total_commits = sum(api.iter_repo_commit_counts(username, repos))
    events = api.get_user_events(username)

    activity_by_day = defaultdict(int)
    for event in events:
        day = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00")).date()
        activity_by_day[day] += normalize_activity_count(event)

    streak = consecutive_streak(list(activity_by_day))
    language_breakdown = percentage_breakdown(language_totals, limit=5)
    dominant_language = language_breakdown[0][0] if language_breakdown else None

    score = build_score(
        total_commits=total_commits,
        public_repos=user.get("public_repos", 0),
        followers=user.get("followers", 0),
        streak=streak,
        top_language_share=language_breakdown[0][1] if language_breakdown else 0.0,
    )

    insights = [
        f"Analyzed {len(repos)} original public repositories.",
        f"Estimated {total_commits} authored commits across visible repositories.",
        f"Recent public activity streak: {streak} day(s).",
    ]
    if language_breakdown:
        insights.append(
            "Primary language mix: "
            + ", ".join(f"{language} {share:.1f}%" for language, share in language_breakdown[:3])
        )
    else:
        insights.append("No language statistics were available from public repositories.")

    suggestions = build_suggestions(
        public_repos=user.get("public_repos", 0),
        total_commits=total_commits,
        streak=streak,
        language_breakdown=language_breakdown,
        dominant_language=dominant_language,
    )

    return {
        "score": score,
        "summary": {
            "public_repos": user.get("public_repos", 0),
            "total_commits": total_commits,
            "top_languages": language_breakdown,
            "contribution_streak": streak,
            "dominant_language": dominant_language,
        },
        "insights": insights,
        "suggestions": suggestions,
    }



def build_suggestions(
    *,
    public_repos: int,
    total_commits: int,
    streak: int,
    language_breakdown: list[tuple[str, float]],
    dominant_language: str | None,
) -> list[str]:
    suggestions: list[str] = []

    if public_repos < 3:
        suggestions.append("Publish more public projects to showcase consistency and breadth.")

    if total_commits < 50:
        suggestions.append("Increase daily commits to build stronger visible momentum on GitHub.")
    elif total_commits > 250:
        suggestions.append("Great commit volume—keep pairing it with well-documented milestones.")

    if streak < 3:
        suggestions.append("Try contributing on consecutive days to grow your contribution streak.")
    elif streak >= 7:
        suggestions.append("Excellent streak—maintain it with small daily improvements or issue triage.")

    if not language_breakdown:
        suggestions.append("Add code-heavy repositories so GitHub can detect your primary languages.")
    else:
        if dominant_language and language_breakdown[0][1] >= 60:
            suggestions.append(f"Focus more on {dominant_language} projects if you want to deepen that specialty.")
        elif len(language_breakdown) >= 3:
            suggestions.append("Your stack is diverse—highlight a flagship project in your strongest language.")
        else:
            suggestions.append("Explore one additional language or framework to broaden your visible skill set.")

    return suggestions[:4] or ["Keep shipping consistently and document standout work in your repositories."]



def build_score(
    *,
    total_commits: int,
    public_repos: int,
    followers: int,
    streak: int,
    top_language_share: float,
) -> int:
    commit_score = min(total_commits / 10, 40)
    repo_score = min(public_repos * 2.5, 20)
    follower_score = min(followers, 10)
    streak_score = min(streak * 2.5, 20)
    diversity_score = max(0.0, 10 - (top_language_share / 10))
    return clamp_score(round(commit_score + repo_score + follower_score + streak_score + diversity_score))
