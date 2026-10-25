# Setup and Run Instructions

These commands describe the current local MVP. The hosted deployment uses the same code
through `vercel.json`; its environment configuration is documented at the end of this file.

## Prerequisites
Python 3.11+, Node.js LTS, npm, Git, a Neon PostgreSQL database (free tier is sufficient), and a modern browser. No GPU is needed.

## Repository
```bash
mkdir Cronos
cd Cronos
git init
mkdir apps
```

## API
```bash
cd apps
python -m venv .venv
```
Activate on Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```
Activate on macOS/Linux:
```bash
source .venv/bin/activate
```
Install dependencies:
```bash
pip install -r requirements.txt
```
From the repository root, once `apps/api/main.py` exists:
```bash
uvicorn apps.api.main:app --reload
```
API docs: `http://127.0.0.1:8000/docs`.

## Database (Neon PostgreSQL)
Create a project in the Neon console and copy its connection string. Create `apps/.env` (never commit it):
```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
```
Use the pooled connection string for application traffic, keep TLS enabled, and create the schema through Alembic migrations once configured:
```bash
alembic upgrade head
```
Neon has a free tier; confirm current limits before relying on it for a demo.

## Web app
From repository root:
```bash
cd apps\web
npx create-next-app@latest . --typescript --tailwind --eslint --app
```
The current UI uses API-backed custom visualizations and CSS motion with reduced-motion support;
no chart or animation dependency is required.
Typical URL: `http://localhost:3000`.

The local frontend automatically uses `http://127.0.0.1:8000` when opened on localhost.
If you need to override that behavior, create `.env.local`:
```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```
Do not put secrets in public environment variables.
The API always allows `http://localhost:3000` and `http://127.0.0.1:3000` locally; deployment
origins can be added through `CRONOS_WEB_ORIGINS`.

## Tests
Backend: `python -m pytest apps\tests -q`
Frontend: `npm --prefix apps\web test -- --run`
Production build: `npm run build:web`
Optional E2E: `npx playwright test`.

## Deployment (Vercel)
Import the repository with the repository root as the project root. Vercel uses the
`frontend` service (`apps/web`) and the `backend` service (`api.index:app`) defined in
`vercel.json`. Configure:
```text
DATABASE_URL=<Neon pooled PostgreSQL connection string>
CRONOS_WEB_ORIGINS=https://your-project.vercel.app
NEXT_PUBLIC_API_BASE_URL=https://your-project.vercel.app
```
Do not set `CRONOS_SQLITE_PATH` on Vercel; serverless filesystems are not durable. See the
root `README.md` for the current live URL and deployment details.

## Suggested implementation order
1. Domain models and sample dataset.
2. Constraint checker and tests.
3. Baseline scheduler.
4. GA operators and tests.
5. Persistence and API.
6. Frontend forms and timetable grid.
7. Analytics and CSV export.
8. Experiments and report.

## Troubleshooting
If the web app cannot reach the API, confirm that Uvicorn is running on port 8000, the
frontend is on port 3000, and any custom `NEXT_PUBLIC_API_BASE_URL` is correct. Local CORS
origins are allowed by default; deployment origins must be listed in `CRONOS_WEB_ORIGINS`.
If persistence fails, verify `DATABASE_URL`, TLS settings, and that the Neon project is
active. Reduce GA population/generations during development. For infeasible results, inspect
validation and diagnostics before increasing runtime.

The MVP is implemented and verified locally, and the hosted configuration is deployed.
Authentication, background jobs, normalized production migration rollout, rate limiting,
and monitoring remain later-phase work.
