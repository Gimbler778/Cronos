# Cronos

Cronos is a local-first college timetable optimizer built around an independently testable genetic algorithm.

## Run both services with one command

From the repository root:

```powershell
npm install
npm run dev
```

This starts the API at `http://127.0.0.1:8000` and the web app at `http://localhost:3000`.
Press `Ctrl+C` to stop both processes.

The Neon connection string belongs in `apps/.env` as `DATABASE_URL`. It is server-only,
ignored by Git, and must never be prefixed with `NEXT_PUBLIC_` or imported by the web app.

## Run the API

From the repository root:

```powershell
python -m pip install -r apps\requirements.txt
python -m uvicorn apps.api.main:app --reload
```

The API is available at `http://127.0.0.1:8000/docs`.

## Run the web app

```powershell
cd apps\web
npm install
npm run dev
```

Open `http://localhost:3000`. The Smart Scheduling dashboard loads the saved dataset,
seeds the documented sample dataset only on first use, previews saved timetables, shows
action feedback, and exports CSV. The deployed app is available at
https://cronos-sc.vercel.app.

On the Overview page, use **Reset to sample data** to replace the saved dataset with the
sample after confirmation. The Data setup page includes **Clear data & timetable**, which
permanently removes the saved records and generated timetables after confirmation. A cleared
workspace stays empty after refresh.

## Validate the project

From the repository root:

```powershell
npm run test:api
npm --prefix apps/web test -- --run
npm run build:web
npm run evaluate
```

The current automated checks include 28 backend tests, 3 frontend tests, a production build,
and the recorded multi-seed evaluation.

## Deploy the complete app to Vercel

The repository includes a Vercel serverless entrypoint at `api\index.py` and a
`vercel.json` that serves both the Next.js app and FastAPI API from one project. Import
the repository into Vercel with the repository root as the project root. Configure:

```text
DATABASE_URL=<Neon pooled PostgreSQL connection string>
CRONOS_WEB_ORIGINS=https://your-project.vercel.app
NEXT_PUBLIC_API_BASE_URL=https://your-project.vercel.app
```

Do not configure `CRONOS_SQLITE_PATH` in Vercel. SQLite remains available for local
development only; Vercel instances are stateless and their filesystem is not durable.
The API reads the dataset and optimization runs from PostgreSQL for every request, so
cold starts and multiple serverless instances do not lose application state.

## Project scope

The current repository targets the deployed MVP. Authentication, background jobs, rate
limiting, migration rollout, monitoring, and release operations are reserved for a later phase.

See the documentation in [apps/docs](apps/docs), including the
[project report](apps/docs/REPORT.md), [roadmap](apps/docs/ROADMAP.md), and
[slide-by-slide presentation plan](apps/docs/ppt.md).
