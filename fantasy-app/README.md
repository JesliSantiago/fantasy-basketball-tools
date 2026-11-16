# Fantasy App

A web app built on the `fantasy-tools` notebooks.

- **backend/**: FastAPI. Imports `fantasy-tools/src/fantasy_core.py` directly and shares its `data/` cache and `draft_picks.json`, so the notebooks and the app stay in sync.
- **frontend/**: React + TypeScript + Vite. In dev, `/api/*` is proxied to the backend.

## Quick start

From the repo root, in two terminals (Command Prompt; Windows PowerShell 5.1 doesn't support `&&`):

```bat
cd fantasy-app/backend  && .venv\Scripts\activate && uvicorn app.main:app --reload
cd fantasy-app/frontend && npm install && npm run dev     # after installing Node.js
```

Then open http://localhost:5173. This assumes the backend's `.venv` already exists; for a fresh setup see below.

## Run it

Backend (from `fantasy-app/backend`):

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload    # http://127.0.0.1:8000/docs
```

Frontend (from `fantasy-app/frontend`, needs [Node.js](https://nodejs.org) 18+):

```bash
npm install
npm run dev                      # http://localhost:5173
```

Tests: `pytest` from `fantasy-app/backend`.

## API

| Endpoint | What it returns |
| --- | --- |
| `GET /api/health` | Status, data folder, default season |
| `GET /api/rankings?season=2025-26&punt=FG_PCT&limit=200` | 9-cat z-score rankings (`fantasy_core.player_values`) |
| `GET /api/draft` | Picks from `draft_picks.json` |

## Config (environment variables)

`FANTASY_SEASON`, `FANTASY_NUM_TEAMS`, `FANTASY_ROSTER_SIZE`, `FANTASY_TOOLS_DIR`, `FANTASY_DATA_DIR`, `CORS_ORIGINS`. See `backend/app/config.py`.

## Next steps

- Draft: pick entry (`POST /api/draft/picks`), undo, best available with weights and position filters
- Roster: injury report, recent form, replacements and recommendations from `roster_updates.ipynb`
- Category profile charts (currently matplotlib in the notebooks)
