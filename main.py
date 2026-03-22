from __future__ import annotations

from html import escape
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from analyzer import analyze_user_profile
from github_api import GitHubAPIError

app = FastAPI(title="DevPulse AI", version="1.0.0")


CSS = """
:root {
    color-scheme: dark;
    --bg: #07111f;
    --bg-secondary: #0d1a2e;
    --hero-glow: rgba(94, 168, 255, 0.28);
    --panel: rgba(14, 24, 40, 0.84);
    --panel-solid: #101b2f;
    --panel-alt: rgba(28, 41, 67, 0.8);
    --text: #e8f0ff;
    --muted: #9db0d0;
    --accent: #73b7ff;
    --accent-2: #7ef0c7;
    --accent-3: #b88cff;
    --border: rgba(255, 255, 255, 0.1);
    --shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
    --danger-bg: rgba(255, 123, 123, 0.14);
    --danger-border: rgba(255, 123, 123, 0.28);
    --danger-text: #ffd6d6;
}
body[data-theme="light"] {
    color-scheme: light;
    --bg: #eef4ff;
    --bg-secondary: #dfeaff;
    --hero-glow: rgba(99, 179, 255, 0.2);
    --panel: rgba(255, 255, 255, 0.88);
    --panel-solid: #ffffff;
    --panel-alt: rgba(237, 244, 255, 0.95);
    --text: #132238;
    --muted: #5a6c89;
    --accent: #2563eb;
    --accent-2: #0f9f79;
    --accent-3: #7c3aed;
    --border: rgba(19, 34, 56, 0.08);
    --shadow: 0 20px 60px rgba(37, 99, 235, 0.12);
    --danger-bg: rgba(255, 123, 123, 0.12);
    --danger-border: rgba(255, 123, 123, 0.22);
    --danger-text: #8c1d1d;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
    margin: 0;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background:
        radial-gradient(circle at top left, var(--hero-glow), transparent 34%),
        radial-gradient(circle at top right, rgba(126, 240, 199, 0.18), transparent 30%),
        linear-gradient(180deg, var(--bg-secondary), var(--bg));
    color: var(--text);
    min-height: 100vh;
    transition: background 0.45s ease, color 0.35s ease;
}
.container {
    width: min(1120px, calc(100% - 32px));
    margin: 0 auto;
    padding: 40px 0 64px;
}
.hero {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, rgba(115, 183, 255, 0.15), rgba(184, 140, 255, 0.08));
    border: 1px solid var(--border);
    border-radius: 28px;
    padding: 32px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(18px);
    animation: floatIn 0.7s ease;
}
.hero::after {
    content: "";
    position: absolute;
    inset: auto -60px -80px auto;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(126, 240, 199, 0.28), transparent 60%);
    pointer-events: none;
}
.hero-top {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    flex-wrap: wrap;
}
.hero h1 { margin: 0 0 12px; font-size: clamp(2.1rem, 4vw, 3.6rem); }
.hero p { margin: 0; color: var(--muted); max-width: 700px; line-height: 1.7; }
.theme-toggle {
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.06);
    color: var(--text);
    border-radius: 999px;
    padding: 12px 16px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    font-weight: 700;
    transition: transform 0.25s ease, background 0.25s ease, border-color 0.25s ease;
}
.theme-toggle:hover { transform: translateY(-1px); }
.theme-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    box-shadow: 0 0 18px rgba(115, 183, 255, 0.7);
}
.search-form {
    display: flex;
    gap: 12px;
    margin-top: 24px;
    flex-wrap: wrap;
}
.input {
    flex: 1 1 280px;
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--border);
    border-radius: 18px;
    color: var(--text);
    padding: 16px 18px;
    font-size: 1rem;
    outline: none;
    transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease;
}
.input:focus {
    border-color: rgba(115, 183, 255, 0.6);
    box-shadow: 0 0 0 4px rgba(115, 183, 255, 0.14);
    transform: translateY(-1px);
}
.button {
    border: 0;
    border-radius: 18px;
    padding: 16px 22px;
    background: linear-gradient(135deg, var(--accent), var(--accent-3));
    color: white;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.22s ease, box-shadow 0.22s ease, filter 0.22s ease;
    box-shadow: 0 16px 30px rgba(37, 99, 235, 0.28);
}
.button:hover {
    transform: translateY(-2px) scale(1.01);
    filter: saturate(1.08);
}
.grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 18px;
    margin-top: 28px;
}
.card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 22px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(18px);
    animation: riseUp 0.55s ease both;
}
.card:nth-child(2) { animation-delay: 0.08s; }
.card:nth-child(3) { animation-delay: 0.14s; }
.card:nth-child(4) { animation-delay: 0.2s; }
.score-card { grid-column: span 4; }
.summary-card { grid-column: span 8; }
.panel-card { grid-column: span 6; }
.kicker { color: var(--muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.16em; }
.score { font-size: clamp(2.8rem, 6vw, 4.8rem); font-weight: 800; margin: 12px 0 6px; line-height: 1; }
.score.good { color: var(--accent-2); }
.score.mid { color: #ffcf6d; }
.score.low { color: #ff9898; }
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px;
    margin-top: 16px;
}
.metric {
    background: var(--panel-alt);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 16px;
    transition: transform 0.22s ease, border-color 0.22s ease;
}
.metric:hover {
    transform: translateY(-2px);
    border-color: rgba(115, 183, 255, 0.32);
}
.metric label { display:block; color: var(--muted); font-size: 0.88rem; margin-bottom: 8px; }
.metric strong { font-size: 1.15rem; }
.list { list-style: none; padding: 0; margin: 16px 0 0; }
.list li {
    margin-bottom: 12px;
    padding: 14px 16px;
    border-radius: 16px;
    background: var(--panel-alt);
    border: 1px solid var(--border);
    line-height: 1.55;
    transition: transform 0.22s ease, background 0.22s ease;
}
.list li:hover { transform: translateX(4px); }
.error {
    margin-top: 24px;
    background: var(--danger-bg);
    color: var(--danger-text);
    border: 1px solid var(--danger-border);
    border-radius: 18px;
    padding: 16px 18px;
}
.footer { color: var(--muted); margin-top: 22px; font-size: 0.95rem; line-height: 1.6; }
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 20px;
}
.chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 999px;
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--border);
    color: var(--muted);
    font-size: 0.92rem;
}
.chip strong { color: var(--text); }
@keyframes floatIn {
    from { opacity: 0; transform: translateY(20px) scale(0.98); }
    to { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes riseUp {
    from { opacity: 0; transform: translateY(22px); }
    to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 900px) {
    .score-card, .summary-card, .panel-card { grid-column: span 12; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation: none !important;
        transition: none !important;
        scroll-behavior: auto !important;
    }
}
"""

SCRIPT = """
(() => {
    const body = document.body;
    const toggle = document.getElementById('theme-toggle');
    const label = document.getElementById('theme-label');
    const saved = localStorage.getItem('devpulse-theme');
    const preferred = saved || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');

    const applyTheme = (theme) => {
        body.setAttribute('data-theme', theme);
        label.textContent = theme === 'dark' ? 'Dark mode' : 'Light mode';
        localStorage.setItem('devpulse-theme', theme);
    };

    applyTheme(preferred);
    toggle?.addEventListener('click', () => {
        const next = body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        applyTheme(next);
    });
})();
"""


def score_class(score: int) -> str:
    if score < 40:
        return "low"
    if score < 70:
        return "mid"
    return "good"



def render_list(items: list[str]) -> str:
    if not items:
        return "<li>No data available.</li>"
    return "".join(f"<li>{escape(item)}</li>" for item in items)



def render_dashboard(username: str, analysis: dict[str, Any]) -> str:
    summary = analysis["summary"]
    languages = ", ".join(
        f"{name} ({share:.1f}%)" for name, share in summary["top_languages"]
    ) or "No language data"
    safe_username = escape(username)
    score = analysis["score"]
    return f"""
    <section class=\"grid\">
        <article class=\"card score-card\">
            <div class=\"kicker\">Developer Pulse Score</div>
            <div class=\"score {score_class(score)}\">{score}/100</div>
            <p class=\"footer\">A blended signal from commit volume, repository activity, streaks, followers, and language diversity.</p>
            <div class=\"chip-row\">
                <span class=\"chip\">🔥 <strong>{summary['contribution_streak']} day(s)</strong> streak</span>
                <span class=\"chip\">📦 <strong>{summary['public_repos']}</strong> repos</span>
            </div>
        </article>
        <article class=\"card summary-card\">
            <div class=\"kicker\">Dashboard for @{safe_username}</div>
            <div class=\"metric-grid\">
                <div class=\"metric\"><label>Estimated Total Commits</label><strong>{summary['total_commits']}</strong></div>
                <div class=\"metric\"><label>Contribution Streak</label><strong>{summary['contribution_streak']} day(s)</strong></div>
                <div class=\"metric\"><label>Public Repositories</label><strong>{summary['public_repos']}</strong></div>
                <div class=\"metric\"><label>Dominant Language</label><strong>{escape(summary['dominant_language'] or 'N/A')}</strong></div>
                <div class=\"metric\" style=\"grid-column: 1 / -1;\"><label>Top Languages</label><strong>{escape(languages)}</strong></div>
            </div>
        </article>
        <article class=\"card panel-card\">
            <div class=\"kicker\">Insights</div>
            <ul class=\"list\">{render_list(analysis['insights'])}</ul>
        </article>
        <article class=\"card panel-card\">
            <div class=\"kicker\">AI Suggestions</div>
            <ul class=\"list\">{render_list(analysis['suggestions'])}</ul>
        </article>
    </section>
    """



def render_page(username: str = "", analysis: dict[str, Any] | None = None, error: str | None = None) -> str:
    dashboard = render_dashboard(username, analysis) if analysis else ""
    error_block = f'<div class="error">{escape(error)}</div>' if error else ""
    value = escape(username)
    return f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>DevPulse AI</title>
        <style>{CSS}</style>
    </head>
    <body data-theme=\"dark\">
        <main class=\"container\">
            <section class=\"hero\">
                <div class=\"hero-top\">
                    <div>
                        <div class=\"kicker\">FastAPI Dashboard</div>
                        <h1>DevPulse AI</h1>
                        <p>Enter a GitHub username to inspect public repository activity, language trends, contribution streaks, developer score, and simple AI-style suggestions in one polished dashboard.</p>
                    </div>
                    <button id=\"theme-toggle\" class=\"theme-toggle\" type=\"button\" aria-label=\"Toggle color theme\">
                        <span class=\"theme-dot\"></span>
                        <span id=\"theme-label\">Dark mode</span>
                    </button>
                </div>
                <form class=\"search-form\" method=\"get\" action=\"/\">
                    <input class=\"input\" type=\"text\" name=\"username\" placeholder=\"e.g. torvalds\" value=\"{value}\" required />
                    <button class=\"button\" type=\"submit\">Analyze Profile</button>
                </form>
                {error_block}
            </section>
            {dashboard}
        </main>
        <script>{SCRIPT}</script>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def index(username: str = Query(default="", max_length=100)) -> HTMLResponse:
    cleaned_username = username.strip()
    if not cleaned_username:
        return HTMLResponse(render_page())

    try:
        analysis = analyze_user_profile(cleaned_username)
    except GitHubAPIError as exc:
        return HTMLResponse(render_page(username=cleaned_username, error=f"GitHub API error: {exc}"), status_code=400)
    except Exception as exc:  # pragma: no cover - defensive web fallback
        return HTMLResponse(render_page(username=cleaned_username, error=f"Unexpected error: {exc}"), status_code=500)

    return HTMLResponse(render_page(username=cleaned_username, analysis=analysis))
