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
if (!(Test-Path .venv\Scripts\Activate.ps1)) { py -3 -m venv .venv }
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If PowerShell blocks virtual environment activation, allow it for the current terminal with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then run the activation command again. The API is at [http://localhost:8000](http://localhost:8000); interactive API docs are at [http://localhost:8000/docs](http://localhost:8000/docs).

Dashboard metrics, campaigns, and scheduled content are in-memory mock data. Drafts use persistent database storage:

- `GET /health`
- `GET /api/dashboard/overview`
- `GET /api/campaigns`
- `GET /api/content`
- `POST /api/content/generate` — creates a deterministic template-based example; no AI model or external service is called.
- `GET /api/drafts` — lists persistent saved drafts.
- `POST /api/drafts` — saves an edited example as a draft (201 response).
- `PATCH /api/drafts/{draft_id}` — edits caption/hashtags or marks a draft approved.

The Next.js dashboard loads these endpoints directly from the API. Dashboard metrics, campaigns, scheduled posts, and drafts remain demonstration data returned by the API; no AI or social integration is connected.

The content studio supports X, LinkedIn, Instagram, and Facebook draft formats. Generated text is a deterministic template example, not output from a real AI model. You can edit the caption and hashtags, save drafts, edit them later, or mark them approved. Approval does not publish anything. Editing changed caption or hashtag content on an approved draft resets it to draft; no-op edits preserve approval. Drafts are stored in the configured database. The earlier Phase 3 in-memory drafts did not survive API restarts, so there is no historical dataset to migrate. Generation rejects prompts containing common guaranteed-return and unsupported investment claims.

### Persistent draft database

The API uses SQLAlchemy with PostgreSQL through psycopg. For a simple local setup, it defaults to a SQLite database at `api/fundly.db`; set `DATABASE_URL` to use PostgreSQL instead. Database configuration is read from the process environment and `api/.env` (copy the safe example if you want a local configuration file):

```powershell
cd C:\Users\PC\fundly-ai-marketing\api
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

The example uses local SQLite. To connect to PostgreSQL, set `DATABASE_URL` in the ignored `api/.env` file to a PostgreSQL URL using the psycopg driver, for example `postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require`. Never commit `.env` or put database credentials in source code. Supabase may be used as a PostgreSQL host later; this project does not configure a Supabase project or require one for tests.

Apply the versioned schema migration explicitly before starting the API:

```powershell
cd C:\Users\PC\fundly-ai-marketing\api
alembic upgrade head
uvicorn app.main:app --reload
```

The migration creates only the new `drafts` table and its indexes; it does not replace or modify other tables. To inspect migration history, run `alembic history`. The corresponding downgrade is `alembic downgrade base`; it removes the table created by this migration and therefore deletes its drafts. Back up any drafts before intentionally downgrading. Migrations never run automatically when the API imports or starts.

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

From `web/`, run `npm run lint` and `npm run build`. From `api/`, install `requirements.txt` in the existing virtual environment, apply `alembic upgrade head`, then run `python -m compileall app` and `python -m unittest discover -s tests`. Routine tests use a fresh isolated in-memory SQLite database and do not need PostgreSQL or Supabase credentials. PostgreSQL integration tests are skipped unless both `RUN_POSTGRES_INTEGRATION=1` and `TEST_DATABASE_URL` are explicitly set. The configured database name must start with `test_` or end in `_test`; tests create and remove only a uniquely named schema. Use a dedicated disposable test database, never production data.

## Project layout

```text
web/       Next.js App Router dashboard (TypeScript, Tailwind CSS)
api/       FastAPI application, SQLAlchemy draft persistence, and Alembic migrations
```

No secrets, paid services, external integrations, production database, or deployment configuration are included.
