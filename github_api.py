from __future__ import annotations

import os
import time
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

BASE_URL = "https://api.github.com"
EVENT_WINDOW_DAYS = 90


class GitHubAPIError(RuntimeError):
    pass


class GitHubAPI:
    def __init__(self, token: str | None = None, timeout: int = 15) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "DevPulse-AI",
            }
        )

        auth_token = token or os.getenv("GITHUB_TOKEN")
        if auth_token:
            self.session.headers["Authorization"] = f"Bearer {auth_token}"

        self.timeout = timeout

    def _handle_rate_limit(self, response):
        if response.status_code == 403:
            if "rate limit" in response.text.lower():
                reset_time = response.headers.get("X-RateLimit-Reset")
                if reset_time:
                    wait = int(reset_time) - int(time.time())
                    wait = max(wait, 1)
                    raise GitHubAPIError(f"Rate limit exceeded. Try again in {wait} seconds.")
                raise GitHubAPIError("Rate limit exceeded. Please add GITHUB_TOKEN.")

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        for _ in range(2):  # retry once
            response = self.session.get(f"{BASE_URL}{path}", params=params, timeout=self.timeout)

            if response.status_code == 200:
                return response.json()

            self._handle_rate_limit(response)

            if response.status_code >= 500:
                time.sleep(1)
                continue

            try:
                payload = response.json()
                message = payload.get("message", response.text)
            except ValueError:
                message = response.text

            raise GitHubAPIError(f"{response.status_code} {message}")

        raise GitHubAPIError("Request failed after retry")

    def get_user(self, username: str) -> dict[str, Any]:
        return self._request(f"/users/{username}")

    def get_user_repos(self, username: str) -> list[dict[str, Any]]:
        repos = []
        page = 1

        while True:
            batch = self._request(
                f"/users/{username}/repos",
                params={"per_page": 100, "page": page},
            )

            if not batch:
                break

            repos.extend(batch)

            if len(batch) < 100:
                break

            page += 1

        return repos

    def get_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        return self._request(f"/repos/{owner}/{repo}/languages")

    def get_user_events(self, username: str, max_pages: int = 10):
        events = []
        cutoff = datetime.now(timezone.utc) - timedelta(days=EVENT_WINDOW_DAYS)

        for page in range(1, max_pages + 1):
            batch = self._request(
                f"/users/{username}/events/public",
                params={"per_page": 100, "page": page},
            )

            if not batch:
                break

            for event in batch:
                created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
                if created_at < cutoff:
                    return events
                events.append(event)

        return events

    def iter_repo_commit_counts(self, username: str, repos):
        for repo in repos:
            owner = repo["owner"]["login"]
            name = repo["name"]

            try:
                response = self.session.get(
                    f"{BASE_URL}/repos/{owner}/{name}/commits",
                    params={"author": username, "per_page": 1},
                    timeout=self.timeout,
                )

                if response.status_code == 409:
                    yield 0
                    continue

                self._handle_rate_limit(response)

                if response.status_code >= 400:
                    yield 0
                    continue

                link_header = response.headers.get("Link", "")
                if 'rel="last"' in link_header:
                    yield self._extract_last_page(link_header)
                else:
                    yield len(response.json())

            except Exception:
                yield 0  # fail safe

    @staticmethod
    def _extract_last_page(link_header: str) -> int:
        for part in link_header.split(","):
            if 'rel="last"' in part:
                section = part.split(";")[0].strip().strip("<>")
                if "page=" in section:
                    return int(section.rsplit("page=", 1)[-1].split("&")[0])
        return 0


def normalize_activity_count(event: dict[str, Any]) -> int:
    event_type = event.get("type")
    payload = event.get("payload", {})

    if event_type == "PushEvent":
        return max(1, len(payload.get("commits", [])))
    if event_type in {"PullRequestEvent", "IssuesEvent", "IssueCommentEvent", "PullRequestReviewEvent"}:
        return 2
    if event_type in {"CreateEvent", "DeleteEvent", "ReleaseEvent", "ForkEvent", "WatchEvent"}:
        return 1
    return 0
