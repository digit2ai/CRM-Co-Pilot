# CRM-Co-Pilot

## What this repo actually is

A single-file Flask app (`app.py`, ~1390 lines) for managing software delivery
projects: Projects -> Sprints -> Epics -> User Stories, plus Risks and
reusable Project Templates. It has a prompt-based project generator
(`detect_project_type` + `generate_project_structure`) that turns a plain
text description into a starter sprint/epic/story tree (types: crm,
ecommerce, mobile, web, analytics, ai, general).

This is NOT the large multi-vertical RinglyPro-CRM ecosystem that the
`.claude/skills/ringlypro-architect` skill describes (verticals/, MCP Brain,
102-agent workforce, voice orbs, SIT-per-vertical, etc). That skill file is
present in `.claude/skills/` but most of its runbooks (voice orb, cost/quote,
teaser, proposal, AI Readiness Department) do not apply here because the
supporting infrastructure (verticals/, memory/, other RinglyPro repos) does
not exist in this repo. Treat those runbooks as reference material only,
not as things to invoke against this codebase.

## Stack

- Flask 2.3.3 + Flask-SQLAlchemy 3.0.5 + Flask-Migrate 4.0.5
- DB: `DATABASE_URL` env var if set (Postgres via psycopg2-binary in
  production), else falls back to local `sqlite:///project_manager.db`
- `SECRET_KEY` env var, defaults to a dev placeholder — must be set in
  any real deployment
- Served via gunicorn in production (`gunicorn==21.2.0` in requirements.txt)
- No test suite exists yet (no `tests/`, no SIT files, no CI config found
  in this checkout)

## Key files

- `app.py` — models (Project, Sprint, Epic, UserStory, Risk,
  ProjectTemplate), all routes (HTML views + `/api/...` JSON endpoints),
  the prompt-to-structure generator, and `init_app()` which auto-creates
  tables and seeds sample data on first boot.
- `init_db.py` — seed/sample data used by `init_app()` and by
  `init_production.py` when the `project` table is empty.
- `init_production.py` — production bootstrap: creates tables, seeds only
  if empty. Run this (not `init_db.py` directly) against a fresh prod DB.
- `import_stories.py` — bulk import helper for user stories.
- `templates/`, `static/` — Jinja views and assets for the dashboard,
  project/sprint/user-story detail pages, backlog, and the
  create-from-prompt flow.

## Verified working (2026-09-21)

Booted the app in a clean venv (`pip install -r requirements.txt`), hit it
with Flask's test client:
- App imports cleanly, no missing deps.
- First request against a fresh sqlite DB auto-creates tables and seeds a
  sample CRM project + default templates (see `init_app()` in `app.py`).
- `GET /` -> 200 (dashboard renders).
- `GET /api/templates` -> 200 (JSON API responds).

No functional changes were made in this pass — this was a wake-up health
check only. Added `.gitignore` (previously absent) so `__pycache__/`,
`instance/*.db`, and local venvs stop showing up as untracked files.

## Not done in this pass

- No automated test suite exists. Adding one (pytest + fixtures around the
  Flask test client) is the natural next step before any further feature
  work, so regressions get caught instead of discovered live.
- Did not touch the emoji characters already present in some `print()`
  output in `init_db.py`/`init_production.py`/`app.py` init logging —
  out of scope for a health-check pass; flagging here since the house
  style elsewhere is no-emoji.
- Did not attempt to reach any deployed instance of this app (no
  production URL/credentials available in this environment).
