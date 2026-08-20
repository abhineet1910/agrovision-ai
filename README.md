# AgroVision (Flask edition)

AI-powered crop disease detection, fertilizer recommendations, and a farming chat
assistant — migrated from the original React + TypeScript + Vite prototype into a
real, runnable **Python + Flask + SQLAlchemy** application.

This is a migration, not a redesign: the visual design (green/white palette, rounded
cards, dark mode, the animated wheat-field footer, the floating theme toggle) is
preserved from the original app. What changed is the backend — it now has a real
database, real authentication, and real AI calls instead of a hardcoded demo login
and mocked results.

## Features

- **Landing page** — hero, feature cards, animated wheat field (same as original).
- **Real authentication** — register / log in / log out with hashed passwords
  (Werkzeug) and session-based auth (Flask-Login). The original app's "Continue as
  Farmer (Demo)" button (no backend, no password) has been replaced entirely.
- **Crop Doctor** — upload a leaf photo, get an AI diagnosis (disease name, severity,
  confidence, description, treatments, fertilizer plan) via Google Gemini's
  multimodal API. Every scan is saved to the database, tied to the logged-in user.
- **Agri-Chat** — a farming Q&A chatbot, also powered by Gemini, with persisted chat
  history per user.
- **Dashboard** — latest scan summary + a 7-day rainfall chart (Chart.js). The chart
  data is still mock data, same as the original `MOCK_WEATHER` array — see
  "Known limitations" below.
- **Dark mode toggle** — same floating button, spring-easing rotation animation,
  persisted via `localStorage`.
- Honest placeholders for `Calendar`, `Weather`, `Profile`, and `Admin` — these were
  either stubs ("Coming Soon") or entirely unbuilt in the original `View` enum, and
  are kept that way rather than invented from scratch.

## Tech stack

- Python 3.11+, Flask 3, Jinja2, Tailwind (via CDN, same config as the original)
- Flask-SQLAlchemy, Flask-Migrate (Alembic), SQLite (dev) / Postgres-ready
- Flask-Login for session auth, Werkzeug for password hashing
- Google Gemini (`google-generativeai`) for image diagnosis + chat
- Chart.js for the dashboard chart (replaces `recharts`, which is React-only)
- pytest for tests

## Architecture

```
agrovision-flask/
├── app/
│   ├── __init__.py        # create_app() application factory
│   ├── extensions.py      # db, login_manager, migrate singletons
│   ├── errors.py          # centralized error handlers (400/401/403/404/413/429/500)
│   ├── models/             # User, DiagnosisScan, ChatSession, ChatMessage
│   ├── routes/             # main, auth, dashboard, api blueprints
│   ├── services/
│   │   └── llm_service.py  # ALL Gemini calls go through here — routes never touch the SDK directly
│   ├── templates/          # Jinja2 templates (Tailwind, same design tokens as original)
│   └── static/js/          # theme toggle, crop doctor upload flow, chat flow
├── migrations/              # created by `flask db init`
├── tests/                   # pytest: auth, models, API (LLM calls mocked)
├── instance/                 # SQLite db lives here by default
├── config.py
├── run.py
├── requirements.txt
└── .env.example
```

Why this structure: it's a small-to-medium app, so Blueprints + a thin `services/`
layer is enough — no need for a full DDD/hexagonal layout.

## Installation

```bash
git clone <your-repo-url>
cd agrovision-flask
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# then edit .env — at minimum set SECRET_KEY and LLM_API_KEY
```

## PyCharm setup

1. **Open** → select the `agrovision-flask` folder.
2. **File → Settings → Project → Python Interpreter → Add Interpreter → Add Local
   Interpreter → Virtualenv Environment** → point it at the `.venv` you created
   above (or let PyCharm create one and run `pip install -r requirements.txt` in
   PyCharm's terminal).
3. Right-click `run.py` → **Run 'run'** (or create a Run Configuration: Script path
   `run.py`, working directory = project root).
4. Optionally add a **Flask** run configuration instead (Target: `run.py`) if you
   prefer PyCharm's Flask-specific debug tooling.

## Environment variables (`.env`)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing key — set a long random string. |
| `FLASK_DEBUG` | `1` for local dev (auto-reload, verbose errors), `0` in production. |
| `DATABASE_URL` | SQLAlchemy DB URI. Defaults to local SQLite; set a `postgresql://...` URL in production. |
| `LLM_PROVIDER` | Currently only `gemini` is implemented. |
| `LLM_API_KEY` | Your Gemini API key (see below). |
| `LLM_MODEL` | Defaults to `gemini-1.5-flash` (fast, free-tier friendly, multimodal). |
| `MAX_UPLOAD_MB` | Max crop-photo upload size, defaults to 5MB. |

## Database

```bash
flask --app run.py db init       # first time only
flask --app run.py db migrate -m "Initial tables"
flask --app run.py db upgrade
```

This creates `instance/app.db` (SQLite) with the `users`, `diagnosis_scans`,
`chat_sessions`, and `chat_messages` tables. Swap `DATABASE_URL` in `.env` to a
Postgres URL and re-run `db upgrade` to move to production.

## Authentication

Real Flask-Login session auth:

```
Register (name, email, password) → password hashed with Werkzeug
  → Log in → session cookie set
    → Dashboard / Crop Doctor / Chat (all @login_required)
      → every scan and chat message is tied to the logged-in user's ID
        → a user can never see another user's scans/chats by guessing an ID
  → Log out → session cleared
```

There is no "demo login" left in this version — the original app's fake login was
intentionally replaced, since persisting AI results per-user requires real accounts.

## AI / LLM

**Provider: Google Gemini** (`google-generativeai` SDK), because:
- It's what the original app (`@google/genai`) was already built around.
- It has a genuine free tier.
- It's one of the few free-tier options that supports **both** text chat and
  multimodal image analysis — both of which this app needs (Crop Doctor requires
  vision, Agri-Chat is text-only).

Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
and set it as `LLM_API_KEY` in `.env`.

**All Gemini calls live in `app/services/llm_service.py`** — routes call
`analyze_crop_image()` and `chat_reply()` and never touch the SDK directly. If you
want to switch providers later (e.g. Groq or OpenRouter for chat-only), implement
the same two function signatures in that module and update `LLM_PROVIDER`. Note:
most free-tier chat-only models don't support vision, so Crop Doctor specifically
needs a multimodal-capable model.

**Free-tier caveat:** Gemini's free tier has rate limits (requests per minute/day).
If you hit them, `analyze_crop_image`/`chat_reply` raise `LLMError`, which the API
routes catch and turn into a friendly `502` response — the frontend shows
"Analysis failed" / "AI Chat is temporarily unavailable" rather than crashing.

## Running

```bash
python run.py
```

Visit `http://localhost:3000`.

## Testing

```bash
pytest
```

Covers:
- Auth: register, login (valid/invalid), logout, protected-route redirect
- Models: password hashing, `DiagnosisScan.to_dict()` shape, cascade deletes
- API: `/api/scan` and `/api/chat` (Gemini calls are mocked, so tests don't need a
  real API key or network access)

## Known limitations (honest differences from the original)

- **Dashboard rainfall chart is still mock data**, same as the original app's
  `MOCK_WEATHER` array. It's clearly labeled in the UI. Swapping it for live data
  (e.g. the free, keyless [Open-Meteo](https://open-meteo.com/) API) is a
  self-contained change in `app/routes/dashboard.py`.
- **`Calendar`, `Weather`, `Profile`, `Admin`** are placeholder pages. They existed
  in the original `View` enum but had no real screens built (Calendar was a
  "Coming Soon" stub; the other three had no code at all) — this migration keeps
  that honesty rather than inventing new features.
- **Chart library changed**: `recharts` is React-only, so the dashboard chart uses
  Chart.js instead. Visual style (green line, rounded tooltip, no gridlines) was
  matched as closely as possible.
- **Frontend framework changed**: the original was a React SPA; this version is
  server-rendered Jinja2 + vanilla JS for the interactive bits (image upload, chat).
  The Tailwind design tokens, colors, spacing, animations, and component layout were
  carried over directly from `index.html`/`App.tsx` — visually it should look and
  feel the same, but it's no longer a single-page React app under the hood.
- **Camera/microphone/geolocation permissions**: the original `metadata.json`
  declared these, but only the camera (via file input, not `getUserMedia`) was
  actually used in the source code. This migration preserves that same level of
  usage — no new voice or location features were added.

## Pushing to GitHub

```bash
git init
git add .
git commit -m "Initial commit: AgroVision Flask migration"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

`.env`, `instance/`, `*.db`, and `.venv/` are already in `.gitignore` — no secrets
or local database files will be committed.
