# fundly-ai-marketing

Fundly AI Marketing Agent is a local-first marketing dashboard prototype. Fundly is the first sample brand; the mock models include a brand identifier so the platform can grow to support more brands.

> **Local prototype:** Dashboard campaign and calendar counts use the configured local database, while engagement and reach estimates remain fictional sample data. Content generation calls the configured Gemini API from the backend. Draft approval is an internal status only; no social network is connected and nothing can be published.

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
if (!(Test-Path .venv\Scripts\Activate.ps1)) { py -3 -m venv .venv }
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If PowerShell blocks virtual environment activation, allow it for the current terminal with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then run the activation command again. The API is at [http://localhost:8000](http://localhost:8000); interactive API docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

Dashboard campaign and calendar counts use persistent database storage. Engagement and reach estimates remain mock data. Campaigns and drafts use persistent database storage. Content generation uses the configured Gemini API; no template fallback is used when configuration is missing:

- `GET /health`
- `GET /api/dashboard/overview`
- `GET /api/campaigns`
- `POST /api/campaigns` — creates a planning entry in the persistent demo campaign list (201 response).
- `GET /api/campaigns/{campaign_id}` — retrieves one campaign planning entry.
- `PATCH /api/campaigns/{campaign_id}` — edits campaign name, channel, objective, or target date.
- `GET /api/content`
- `GET /api/calendar` — lists persistent local scheduled entries.
- `POST /api/calendar` — schedules an approved draft locally; it never publishes to a social network.
- `PATCH /api/calendar/{entry_id}` — reschedules a local calendar entry.
- `DELETE /api/calendar/{entry_id}` — removes a local calendar entry without deleting its draft.
- `POST /api/content/generate` — requests and validates a structured marketing draft from Gemini. Returns a clear configuration error if `GEMINI_API_KEY` is missing.
- `GET /api/drafts` — lists persistent saved drafts.
- `POST /api/drafts` — saves reviewed content as a draft (201 response).
- `PATCH /api/drafts/{draft_id}` — edits caption/hashtags or marks a draft approved.

The Next.js dashboard loads these endpoints directly from the API. Campaign and calendar counts reflect locally persisted records; engagement and reach remain demonstration estimates. AI generation is performed server-side, and the API key is never sent to the browser. No social integration is connected.

The **New campaign** form creates a local planning entry with a name, channel, objective, and target date. Campaigns are stored in the configured database and remain available after an API restart or across workers. Use the Edit action on a campaign to update its planning details. The initial migration adds three clearly marked demo campaigns; campaign management does not create ads, schedule posts, or publish content. The active-campaign and scheduled-content cards recalculate from persisted records; engagement and reach remain sample estimates.

The content studio supports X, LinkedIn, Instagram, and Facebook draft formats. It sends the topic, platform, objective, tone, and optional notes to Gemini and validates the structured response against the existing content schema and financial-claim checks. Those heuristic checks reject common guaranteed-return wording and numerical performance claims; they cannot verify that financial statements are factually true. Review and edit the generated copy before explicitly saving it; saved drafts use the configured database. You can edit drafts later, mark them approved, and schedule approved drafts in the local planning calendar. Existing entries can be rescheduled or removed without deleting their drafts. Each draft can have at most one local calendar entry. Approval and scheduling do not publish anything. Editing changed caption or hashtag content on an approved draft resets it to draft; no-op edits preserve approval. Provider credentials are server-side only. The optional Gemini free tier may use submitted content to improve Google's products; avoid including sensitive or personal information. Provider limits and any charges are controlled by your Google AI Studio project.

Gemini settings are read from process environment variables first and then from the backend's absolute-path `api/.env`, independent of the server's working directory or import order. To enable real AI generation, add the key to the ignored `api/.env` file (create it from `.env.example` if needed), then restart the API:

```dotenv
GEMINI_API_KEY=your_key_from_google_ai_studio
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_USE_PROXY=false
```

Get a key from [Google AI Studio](https://aistudio.google.com/app/apikey). The example model is configurable with `GEMINI_MODEL`. Gemini uses direct HTTPS by default; if your network requires the configured system proxy, set `GEMINI_USE_PROXY=true` and ensure the proxy variables are available to the backend process. Missing keys and invalid model identifiers return configuration errors; provider authentication, unavailable-model, quota, timeout, and request errors have separate sanitized responses. Without `GEMINI_API_KEY`, generation does not produce template content. Automated tests mock provider responses and do not call Gemini or consume API credits.

### Persistent draft database

The API uses SQLAlchemy with PostgreSQL through psycopg. For a simple local setup, it defaults to a SQLite database at `api/fundly.db`; set `DATABASE_URL` to use PostgreSQL instead. Database configuration is read from the process environment and `api/.env`; a process environment variable takes precedence. Copy the safe example if you want a local configuration file:

```powershell
cd C:\Users\PC\fundly-ai-marketing\api
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

The example uses local SQLite. To connect to hosted PostgreSQL such as Supabase, set `DATABASE_URL` in the ignored `api/.env` file to the provider's PostgreSQL URL using the psycopg driver, for example `postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require`. Treat this as a format example; use the URL from your own provider dashboard. Never commit `.env`, paste credentials into source code, or share the URL in logs or support messages. Supabase is optional and no Supabase project is configured or required for tests. Run the connection check and any later Alembic command from the same PowerShell window; confirm that no unintended process-level `DATABASE_URL` is overriding the value in `.env`.

From `api/`, check connectivity before considering a migration:

```powershell
cd C:\Users\PC\fundly-ai-marketing\api
python -m app.check_database
```

The check runs only `SELECT 1`. It reports success or a sanitized error and never prints the database URL, host, username, or password. Before any migration, independently verify that the configured project, host, and database are the intended target in your provider dashboard. Then inspect the current migration revision:

```powershell
alembic current
```

Only after confirming the target and its current schema state, apply the versioned migration:

```powershell
alembic upgrade head
```

The versioned migrations create only the new `drafts`, `campaigns`, and `calendar_entries` tables and their indexes; they do not replace or modify other tables. The campaigns and calendar migrations insert only their documented demo rows into newly created tables. The latest calendar migration links future scheduled entries to drafts and prevents duplicate scheduling for one draft. If the target already has an unversioned table or its state is unclear, stop and review it before upgrading. To inspect migration history, run `alembic history`. The corresponding downgrade removes only these project tables and therefore deletes their stored records; back up data before intentionally downgrading. Migrations never run automatically when the API imports or starts. After a successful migration, start the API with `uvicorn app.main:app --reload`.

### Try content generation

With `GEMINI_API_KEY` configured and the API running, use PowerShell to request a draft:

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

From `web/`, run `npm run lint` and `npm run build`. From `api/`, install `requirements.txt` in the existing virtual environment, then run `python -m compileall app` and `python -m unittest discover -s tests`. Routine tests use a fresh isolated in-memory SQLite database and do not need PostgreSQL or Supabase credentials. PostgreSQL integration tests are skipped unless both `RUN_POSTGRES_INTEGRATION=1` and `TEST_DATABASE_URL` are explicitly set. The database name must start with `test_` or end in `_test`, except the dedicated Neon database named `neondb` is allowed when the host ends in `.neon.tech`. Tests create and remove only a uniquely named schema. Use a dedicated disposable test database, never production data. Do not run a migration as part of routine tests.

## Project layout

```text
web/       Next.js App Router dashboard (TypeScript, Tailwind CSS)
api/       FastAPI application, SQLAlchemy campaign/draft persistence, and Alembic migrations
```

No secrets, social publishing integration, production database, or deployment configuration are included. Gemini is optional and can incur charges if used with a paid Google AI Studio project.
