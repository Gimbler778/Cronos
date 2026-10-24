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

Open `http://localhost:3000`. The Smart Scheduling dashboard loads the documented sample
dataset, validates it, runs a seeded optimization, previews the schedule, shows Ready/Running
status, and exports CSV.

## Validate the project

From the repository root:

```powershell
npm run test:api
npm --prefix apps/web test -- --run
npm run build:web
npm run evaluate
```

The current automated checks include 15 backend tests, 3 frontend tests, a production build,
and the recorded multi-seed evaluation.

## Project scope

The current repository targets the local MVP. Production deployment, authentication,
background jobs, rate limiting, migration rollout, monitoring, and release operations
are reserved for a later phase.

See the documentation in [apps/docs](apps/docs), including the
[project report](apps/docs/REPORT.md) and [roadmap](apps/docs/ROADMAP.md).
