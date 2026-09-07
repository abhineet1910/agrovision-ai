# AgroVision

An AI-powered crop health assistant for farmers: upload a photo of a crop leaf and get an instant disease diagnosis with a treatment and fertilizer plan, plus a farming Q&A chat assistant — both powered by Google Gemini's multimodal API.


## Features

- **Real authentication** — register / log in / log out with hashed passwords (Werkzeug) and session-based auth (Flask-Login)
- **Crop Doctor** — upload a leaf photo and get an AI diagnosis (disease name, severity, confidence, description, treatments, fertilizer plan) via Gemini's multimodal image analysis. Every scan is saved to the database, tied to the logged-in user
- **Agri-Chat** — a farming Q&A chatbot, also powered by Gemini, with persisted per-user chat history
- **Dashboard** — latest scan summary plus a 7-day rainfall chart (Chart.js). The rainfall data is mock data, clearly labeled as such in the UI
- **Dark mode toggle** — floating button with a spring-easing rotation animation, persisted via `localStorage`
- **Placeholder pages** for Calendar, Weather, Profile, and Admin, clearly marked "Coming Soon" rather than left broken

## AI / LLM

**Provider: Google Gemini** (`google-generativeai` SDK), because:
- It has a genuine free tier.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask 3, Jinja2 |
| Database | Flask-SQLAlchemy, Flask-Migrate (Alembic), SQLite (dev) / Postgres-ready |
| Auth | Flask-Login (session auth), Werkzeug (password hashing) |
| AI | Google Gemini (`google-generativeai`) — multimodal image diagnosis + text chat |
| Frontend | Jinja2 templates, Tailwind CSS (CDN), vanilla JS for upload/chat interactivity |
| Charts | Chart.js |
| Testing | pytest |

**On the AI:** disease diagnosis is done by sending the uploaded leaf image directly to Gemini's multimodal API and parsing its structured response (disease name, severity, confidence, treatments) — not a separately trained computer-vision classifier. Gemini was chosen because it has a genuine free tier and supports both multimodal image analysis (needed for Crop Doctor) and text chat (needed for Agri-Chat) from a single provider.

## Architecture

```
agrovision-ai/
├── app/
│   ├── __init__.py         # create_app() application factory
│   ├── extensions.py       # db, login_manager, migrate singletons
│   ├── errors.py           # centralized error handlers (400/401/403/404/413/429/500)
│   ├── models/              # User, DiagnosisScan, ChatSession, ChatMessage
│   ├── routes/               # main, auth, dashboard, api blueprints
│   ├── services/
│   │   └── llm_service.py   # all Gemini calls go through here — routes never touch the SDK directly
│   ├── templates/            # Jinja2 templates (Tailwind)
│   └── static/js/            # theme toggle, crop doctor upload flow, chat flow
├── migrations/                # created by `flask db init`
├── tests/                     # pytest: auth, models, API (LLM calls mocked)
├── instance/                  # SQLite db lives here by default
├── config.py
├── run.py
├── requirements.txt
└── .env.example
```

## Setup & Running Locally

1. **Clone and install**
   ```bash
   git clone https://github.com/<your-username>/agrovision-ai.git
   cd agrovision-ai
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Set at minimum `SECRET_KEY` and `LLM_API_KEY` (see table below).

3. **Set up the database**
   ```bash
   flask --app run.py db init       # first time only
   flask --app run.py db migrate -m "Initial tables"
   flask --app run.py db upgrade
   ```

4. **Run**
   ```bash
   python run.py
   ```
   Visit `http://localhost:3000`.

### Environment variables (`.env`)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing key — set a long random string |
| `FLASK_DEBUG` | `1` for local dev, `0` in production |
| `DATABASE_URL` | SQLAlchemy DB URI — defaults to local SQLite; set a `postgresql://...` URL in production |
| `LLM_PROVIDER` | Currently only `gemini` is implemented |
| `LLM_API_KEY` | Your Gemini API key — get a free one at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `LLM_MODEL` | Defaults to `gemini-1.5-flash` (fast, free-tier friendly, multimodal) |
| `MAX_UPLOAD_MB` | Max crop-photo upload size, defaults to 5MB |

## Authentication Flow

```
Register (name, email, password) → password hashed with Werkzeug
  → Log in → session cookie set
    → Dashboard / Crop Doctor / Chat (all @login_required)
      → every scan and chat message is tied to the logged-in user's ID
  → Log out → session cleared
```
## Testing

```bash
pytest
```

Covers:
- Auth: register, login (valid/invalid), logout, protected-route redirect
- Models: password hashing, `DiagnosisScan.to_dict()` shape, cascade deletes
- API: `/api/scan` and `/api/chat` (Gemini calls are mocked, so tests don't need a
  real API key or network access)

## Known Limitations

- **Dashboard rainfall chart is mock data**, clearly labeled in the UI. Swapping it for live data (e.g. the free [Open-Meteo](https://open-meteo.com/) API) is a self-contained change in `app/routes/dashboard.py`.
- **Calendar, Weather, Profile, and Admin are placeholder pages** — marked "Coming Soon" rather than left broken or removed.
- **Free-tier rate limits**: Gemini's free tier has request-per-minute/day limits. If hit, the diagnosis/chat calls raise a handled error and the frontend shows a friendly "temporarily unavailable" message rather than crashing.

`.env`, `instance/`, `*.db`, and `.venv/` are already in `.gitignore` — no secrets or local database files will be committed.
