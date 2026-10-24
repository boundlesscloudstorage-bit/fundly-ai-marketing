# fundly-ai-marketing

Fundly AI Marketing Agent is a local-first marketing dashboard prototype. Fundly is the first sample brand; the mock models include a brand identifier so the platform can grow to support more brands.

> **Demo only:** Dashboard metrics, campaigns, scheduled posts, and AI draft examples are fictional sample data. No AI provider or social network is connected, and nothing can be published.

## Requirements

- Windows 11
- Node.js 20.9 or later and npm
- Python 3.10 or later

## Run the dashboard

Open PowerShell in the repository folder:

```powershell
cd C:\Users\PC\fundly-ai-marketing\web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).
The dashboard requests overview metrics, campaigns, and content from the FastAPI service. By default it uses `http://localhost:8000`. To change the API address, copy `.env.example` to `.env.local` in `web/`, set `NEXT_PUBLIC_API_BASE_URL` to the API origin, and restart the dashboard.

## Run the API

Open a second PowerShell window in the repository folder:

```powershell
cd C:\Users\PC\fundly-ai-marketing\api
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If PowerShell blocks virtual environment activation, allow it for the current terminal with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then run the activation command again. The API is at [http://localhost:8000](http://localhost:8000); interactive API docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

The API endpoints return in-memory mock data:

- `GET /health`
- `GET /api/dashboard/overview`
- `GET /api/campaigns`
- `GET /api/content`

The Next.js dashboard loads these endpoints directly from the API. Dashboard metrics, campaigns, scheduled posts, and drafts remain demonstration data returned by the API; no AI or social integration is connected.

## Development checks

From `web/`, run `npm run lint` and `npm run build`. From `api/`, run `python -m compileall app` and `python -m unittest discover -s tests`.

## Project layout

```text
web/       Next.js App Router dashboard (TypeScript, Tailwind CSS)
api/       FastAPI application with validated mock response models
```

No secrets, paid services, external integrations, production database, or deployment configuration are included.
