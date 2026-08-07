# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Spendly — a personal expense tracker built with Flask + server-rendered Jinja2 templates (no frontend framework, no JS build step). The codebase is a step-based course scaffold: several routes and the entire database layer are intentionally left as placeholders for later steps (see `app.py` comments — "Step 1", "Step 3", "Step 4", "Step 7", "Step 8", "Step 9").

## Commands

**Install dependencies** — this machine has two separate Python installs (system `python3` vs. a `pip` on PATH pointing at miniconda). Always install and run with the same interpreter to avoid `ModuleNotFoundError`:
```
python3 -m pip install -r requirements.txt
```

**Run the dev server**:
```
python3 app.py
```
Starts Flask in debug mode (auto-reload on file changes) on a fixed port: `http://127.0.0.1:5001` (not Flask's default 5000).

**Tests**: `pytest` and `pytest-flask` are declared in `requirements.txt`, but no test files exist yet. Once added, run with `python3 -m pytest`.

## Architecture

- **`app.py`** — single-file Flask app; every route is defined here directly (no blueprints). Implemented: `/` (landing), `/register`, `/login`, `/terms`, `/privacy` — all simple GETs that render a template. Intentionally unimplemented placeholders (return a plain string, not a template): `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`.
- **`database/db.py`** — placeholder for the SQLite data layer. Meant to expose `get_db()` (connection with `row_factory` + foreign keys enabled), `init_db()` (create tables), and `seed_db()` (sample data), per its inline comment — none of this is implemented yet. The runtime DB file (`expense_tracker.db`) is gitignored.
- **`templates/base.html`** — shared layout every page extends via `{% extends "base.html" %}`. Exposes blocks `title`, `head`, `content`, `scripts`. Contains the nav and footer; page templates normally only fill `content`.
- **`static/css/style.css`** — the single stylesheet for the whole app, linked once from `base.html`. There is no per-page CSS file (e.g. no `landing.css`) — everything lives here, organized under commented section headers (Hero, Mock card, Legal pages, Footer, Modal, Responsive, ...). Add new page/section styles here, scoped with distinct class names so sections stay independently editable.
- **`static/js/main.js`** — empty placeholder. Page-specific behavior (e.g. the landing page's "See how it works" video modal) is written inline via a `{% block scripts %}` in that page's own template rather than added to `main.js`.
- **`register.html` / `login.html`** forms POST directly to hardcoded `action="/register"` / `action="/login"` rather than `url_for(...)`; the corresponding POST handlers don't exist yet in `app.py`, only the GET routes that render the empty forms.

## Conventions

- Internal links in templates use `url_for('<endpoint>')`, not hardcoded paths — except the two hardcoded form actions noted above.
- Commit messages follow `<area>: <lowercase summary>`, e.g. `landing: add terms and privacy links to footer`.
