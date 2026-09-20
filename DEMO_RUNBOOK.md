# ResilienceAI — School Demo Runbook

Short, verified setup guide for the school demo (updated Aug 2026). The full
README covers the basics; this file records the exact steps that work, on any
recent Linux/Windows machine with Python 3.11+ and Node 20+.

## One-time setup

```bash
# 1. Clone
git clone git@github.com:Mhk-debug/ResilienceAI.git
cd ResilienceAI

# 2. Backend environment (Python 3.11 or newer)
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # pins are Python-3.11 compatible (Aug 2026)
cd ..

# 3. Frontend dependencies
cd frontend
npm install    # approves sharp/unrs-resolver build scripts automatically
cd ..

# 4. Database
#    Option A (recommended for standalone demo): local PostgreSQL
#      sudo apt install postgresql   (or use Homebrew / installer on Windows)
#      create role+db, e.g.:
#        sudo -u postgres psql -c "CREATE ROLE resilience LOGIN PASSWORD 'resilience';"
#        sudo -u postgres psql -c "CREATE DATABASE resilienceai OWNER resilience;"
#    Option B: Neon — put your Neon connection URL in .env instead
#
#    Tables are created automatically on backend boot (no migration step).

# 5. Create .env (project root; already gitignored)
#    Required:
#      DATABASE_URL=postgresql://resilience:resilience@127.0.0.1:5432/resilienceai
#      GEMINI_API_KEY=...            # needed for the AI analysis stage
#    Optional defaults (fine as-is for a demo):
#      SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
#      FRONTEND_URL, NEXT_PUBLIC_API_URL
```

## Run (two terminals)

```bash
# Terminal 1 — backend on http://127.0.0.1:8000
cd backend && source .venv/bin/activate && uvicorn main:app

# Terminal 2 — frontend on http://localhost:3000
cd frontend && npm run dev
```

Open http://localhost:3000 → register an account → New Assessment.

## What needs internet / external services

| Dependency          | If missing at demo time                              |
|---------------------|-------------------------------------------------------|
| Gemini API key      | Assessment **fails at the AI stage** — the only hard requirement. The app otherwise boots fine. |
| USGS quake API      | Degrades: hazard engine runs on fallbacks + warnings  |
| SoilGrids           | Degrades: deterministic fallback soil properties      |
| Nominatim reverse geocode | Degrades: no place name shown (store/UI handle null) |
| Map tiles (Leaflet) | Form still works; map tiles just don't load           |
| RAG (optional)      | Not installed → retriever is None → citations skipped. To enable: `pip install sentence-transformers chromadb` + `python scripts/build_kb_index.py` (needs ~1 GB more of deps) |

## Useful commands

```bash
# Reset DB (wipes all users/assessments) — run while backend is stopped
cd backend && . .venv/bin/activate && python scripts/reset_db.py

# Run backend test suite (53 tests)
cd backend && . .venv/bin/activate && python -m pytest tests/ -q

# Production-style frontend build check
cd frontend && npm run build
```

## Notes

- Backend auth: cookie + JWT (`access_token`, HttpOnly, 30-min expiry).
  Register auto-logs-in; verify-email / change-password / change-email all work
  with SMTP unset (tokens are printed to the backend console instead).
- `.env` is never committed. Keep it out of the repo.