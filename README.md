# text.repo
# DevPulse AI

DevPulse AI is a FastAPI web app that analyzes a GitHub user's public profile and shows the results in a polished dashboard.

## Features

- Web form with an input box for a GitHub username.
- FastAPI backend for fetching and analyzing GitHub data.
- Dashboard displays:
  - developer score (0-100)
  - estimated total commits
  - contribution streak
  - top languages
  - AI-style suggestions
- Dark mode toggle with saved theme preference.
- Improved UI styling with modern colors, gradients, and subtle animations.
- Uses GitHub REST API with optional `GITHUB_TOKEN` support.

## Project Structure

- `main.py` - FastAPI application and HTML dashboard rendering.
- `github_api.py` - GitHub REST API client helpers.
- `analyzer.py` - Aggregates metrics, calculates the score, and builds suggestions.
- `utils.py` - Utility helpers for scoring and formatting.
- `requirements.txt` - Python dependencies.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the App

```bash
uvicorn main:app --reload
```

Then open `http://127.0.0.1:8000` in your browser.

### Optional Authentication

GitHub rate limits unauthenticated requests aggressively. For more reliable results, set a personal access token:

```bash
export GITHUB_TOKEN=your_token_here
uvicorn main:app --reload
```

## UI Notes

- The theme toggle switches between dark and light mode.
- Theme preference is saved in the browser with `localStorage`.
- Cards, buttons, and panels include lightweight animations and hover states.
- Reduced motion preferences are respected through CSS.

## Notes on Metrics

- **Total commits** are estimated by counting authored commits across the user's visible, non-fork repositories.
- **Most used languages** are based on each repository's GitHub language byte counts.
- **Contribution streak** is derived from recent public activity events returned by GitHub.
- **Score** blends commits, repositories, followers, streak, and language diversity into a 0-100 value.
- **AI suggestions** use local rule-based logic only; no external AI API is required.

## Example Flow

1. Enter a GitHub username in the dashboard search box.
2. Submit the form.
3. Toggle between dark and light mode if desired.
4. Review the score, streak, language summary, insights, and suggestions cards.
