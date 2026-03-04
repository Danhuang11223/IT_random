# IT Random

Random Activity Flow is a Django + Vue web application for generating low-friction daily activity suggestions based on a user's available time, budget, energy level, and social preference.

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

### 3. Run the Django API

```bash
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

The API will be available under `http://127.0.0.1:8000/api/`.

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

## Deployment Notes

This repository now includes starter deployment files for Render:

- [render.yaml](/Users/danhuang/Desktop/Random/render.yaml)
- [Procfile](/Users/danhuang/Desktop/Random/Procfile)
- [build.sh](/Users/danhuang/Desktop/Random/build.sh)
- [requirements.txt](/Users/danhuang/Desktop/Random/requirements.txt)

The suggested setup is:

1. Deploy the Django API as a Python web service.
2. Deploy the Vue app as a static site.
3. Set `VITE_API_BASE_URL` in the front-end deployment to the public API URL, ending with `/api`.

Example:

```text
VITE_API_BASE_URL=https://your-backend-service.onrender.com/api
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
