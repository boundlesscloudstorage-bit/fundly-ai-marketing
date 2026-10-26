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
- `POST /api/content/generate` — creates a deterministic template-based example; no AI model or external service is called.
- `GET /api/drafts` — lists saved drafts held in memory.
- `POST /api/drafts` — saves an edited example as a draft.
- `PATCH /api/drafts/{draft_id}` — edits caption/hashtags or marks a draft approved.

The Next.js dashboard loads these endpoints directly from the API. Dashboard metrics, campaigns, scheduled posts, and drafts remain demonstration data returned by the API; no AI or social integration is connected.

The content studio supports X, LinkedIn, Instagram, and Facebook draft formats. Generated text is a deterministic template example, not output from a real AI model. You can edit the caption and hashtags, save drafts, edit them later, or mark them approved. Approval does not publish anything. Saved drafts use in-memory storage and are cleared whenever the FastAPI process restarts. Generation rejects prompts containing common guaranteed-return and unsupported investment claims.

### Try content generation

With the API running, use PowerShell to request an offline demo draft:

```powershell
$body = @{
  topic = "building a monthly budget"
  platform = "linkedin"
  objective = "education"
  tone = "friendly"
  keywords = "planning, everyday money"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/content/generate -ContentType "application/json" -Body $body
```

Open the dashboard and use the Content Studio to generate, edit, and save drafts. The Saved Drafts section supports further edits and approval status changes.

## Development checks

From `web/`, run `npm run lint` and `npm run build`. From `api/`, run `python -m compileall app` and `python -m unittest discover -s tests`.

## Project layout

```text
web/       Next.js App Router dashboard (TypeScript, Tailwind CSS)
api/       FastAPI application with validated mock response models
```

No secrets, paid services, external integrations, production database, or deployment configuration are included.
