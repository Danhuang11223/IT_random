# IT Random

Random Activity Flow is a Django + Vue web application for generating low-friction daily activity suggestions based on a user's available time, budget, energy level, and social preference.

## Key Features (Current)

- Generator flow: `Generate -> Accept -> History`
- Budget preference tiers: `Free / Low / Medium / High / Any` (instead of raw number entry)
- Save for later: independent saved list (`/saved`) without forcing accept
- Non-repeat recommendations: 7-day cooldown with one-time relaxation notice
- Add to Calendar: `.ics` download and Google Calendar prefilled link
- History tools: status filter + keyword search (`title/comment`) + sorting + pagination
- Accessibility panel: reduce motion, larger text, high contrast (persisted to localStorage)
- Structured recommendation explainability on each generated result
- Admin activity pool management (CRUD + CSV import)
- Delete undo for Saved/History (5-second undo window)

## Stack

- Back end: Django 6 + Django REST Framework
- Front end: Vue 3 + Vue Router + Vite
- Database: SQLite (local development)

## Local Development

### 1. Install Python dependencies

If you are starting from a fresh environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

If the existing local virtual environment is already set up:

```bash
source .venv/bin/activate
```

### 2. Prepare the Django app

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_activities
```

Optional: create an admin account

```bash
.venv/bin/python manage.py createsuperuser
```

### 2.1 Demo reset (one command)

Before a demo or marking session, reset to a clean, seeded state:

```bash
./scripts/demo_reset.sh
```

By default this recreates:

- seeded activity pool
- demo admin user `admin / Admin123456!`

Override via env vars if needed:

```bash
DEMO_ADMIN_USERNAME=teacher DEMO_ADMIN_PASSWORD='StrongPass123!' ./scripts/demo_reset.sh
```

### 3. Run the Django API

```bash
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

The API will be available under `http://127.0.0.1:8000/api/`.

Main API groups:

- Auth: `/api/auth/login/`, `/api/auth/register/`
- Generator: `/api/generate/`, `/api/generate/{request_id}/reroll/`
- Suggestion accept: `/api/suggestions/{suggestion_id}/accept/`
- Logs/history: `/api/logs/`, `/api/logs/{id}/`
- Saved for later: `/api/saved/`, `/api/saved/{id}/`
- Metadata: `/api/metadata/`

### 4. Run the Vue front end

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Test and Build Commands

### Back-end tests

```bash
.venv/bin/python manage.py test daily_random_events
```

### Django configuration check

```bash
.venv/bin/python manage.py check
```

### Front-end production build

```bash
cd frontend
npm run build
```

### E2E (Playwright)

Install dependencies and browser binaries first:

```bash
cd frontend
npm install
npx playwright install
```

Run:

```bash
npm run e2e
```

## CI (GitHub Actions)

Workflow: `.github/workflows/ci.yml`

- Job 1: Django migrations + `manage.py test daily_random_events`
- Job 2: Playwright e2e (`login -> generate -> save -> history search/sort`)

Each push/PR produces automated acceptance evidence.

## Manual Verification Checklist (Feature Expansion)

1. Sign in, generate a suggestion, click `💾 Save`, confirm it appears in `/saved`.
2. From Result/History/Saved, open `Add to Calendar`, test `.ics` download and Google link.
3. In History, combine `status + q + sort + page` and refresh browser; query state should persist.
4. In header `Accessibility`, toggle all 3 settings; refresh and confirm persistence.
5. Generate repeatedly with similar constraints and confirm 7-day non-repeat behaviour and cooldown relaxation message when needed.

## Deployment Notes

This repository now includes starter deployment files for Render:

- [render.yaml](/Users/danhuang/Desktop/Random/render.yaml)
- [Procfile](/Users/danhuang/Desktop/Random/Procfile)
- [build.sh](/Users/danhuang/Desktop/Random/build.sh)
- [requirements.txt](/Users/danhuang/Desktop/Random/requirements.txt)

The suggested setup is:

1. Deploy the Vue app as a static site (`https://it-random.onrender.com`).
2. Deploy the Django API as a Python web service (`https://it-random-api.onrender.com`).
3. Set `VITE_API_BASE_URL` in the front-end deployment to the public API URL, ending with `/api`.

Example:

```text
VITE_API_BASE_URL=https://it-random-api.onrender.com/api
```

### Production hardening defaults

- `DJANGO_DEBUG` defaults to `False` (secure by default)
- CORS is allowlist-based via `DJANGO_CORS_ALLOWED_ORIGINS`
- Copy `.env.example` and set your real secrets/hosts before deploy

Production start command example:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
```

Local development does not need this variable because Vite proxies `/api` to Django.

## Coursework Documentation

Prepared submission support files live in [docs](/Users/danhuang/Desktop/Random/docs):

- [implementation-report.md](/Users/danhuang/Desktop/Random/docs/implementation-report.md)
- [accessibility-evidence.md](/Users/danhuang/Desktop/Random/docs/accessibility-evidence.md)
- [sustainability-report.md](/Users/danhuang/Desktop/Random/docs/sustainability-report.md)
- [ai-use-statement.md](/Users/danhuang/Desktop/Random/docs/ai-use-statement.md)
- [submission-checklist.md](/Users/danhuang/Desktop/Random/docs/submission-checklist.md)

These are written as Markdown source files so they can be edited and exported to PDF for submission.
