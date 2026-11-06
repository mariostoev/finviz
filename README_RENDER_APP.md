# Finviz AI Trade Radar App

This repository now includes a separate web app alongside the original `finviz` Python package:

- `backend/` - FastAPI API for Finviz snapshots, trade scoring, and optional OpenAI summaries
- `frontend/` - Next.js dashboard for scanning stock ideas
- `render.yaml` - Render Blueprint for deploying both services

## Important Note

Finviz quote data is delayed. The scanner is for research and idea generation only, not live execution advice.

## Local Run

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Optional backend environment variables:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `CORS_ORIGINS`

## Render Deploy

Render can deploy both services from `render.yaml`:

- `finviz-ai-backend`
- `finviz-ai-frontend`

The frontend proxies `/api/*` to the backend over Render's private network using `BACKEND_HOSTPORT`.
