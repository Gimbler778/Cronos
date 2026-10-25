# Architecture

## High-level flow
```text
Browser
  -> apps/web Next.js UI (TypeScript)
       -> Guided data entry, dataset editor, schedule filters, and run controls
       -> API-backed metrics and resource analytics
  -> HTTP/JSON
  -> apps/api FastAPI + Pydantic
       -> Application services
       -> Scheduling domain
            -> Constraint checker
            -> Fitness evaluator
            -> Genetic Algorithm
       -> Storage adapter
  -> PostgreSQL/Neon in Vercel, or local SQLite during development
```

## Frontend
Next.js client dashboard with guided record additions, advanced JSON dataset editing,
configurable optimization controls, schedule preview with section/faculty/room filters,
API-backed generation/resource analytics, CSV download, keyboard focus states, and
loading/error/empty states. Animation is CSS-only and disabled under reduced-motion preferences.

## Backend
Validate requests, expose versioned JSON APIs, orchestrate optimization, persist runs and schedules, export CSV, and return diagnostics. Keep domain logic independent of FastAPI.

## Suggested API layout
```text
apps/api/
  main.py
  api/routes/
  schemas/
  models/
  repositories/
  services/
  scheduler/
    chromosome.py
    constraints.py
    fitness.py
    operators.py
    genetic_algorithm.py
    diagnostics.py
apps/tests/
```

## Suggested web layout
```text
apps/web/app/
  page.tsx
  schedule.ts
  globals.css
apps/web/components/
  (future extracted UI components)
```

The current MVP keeps the dashboard views in `apps/web/app/page.tsx`; the sidebar switches
between overview, data setup, timetable, and analytics panels without separate routes.

## Data flow
1. Admin enters/loads data.
2. API validates data and references.
3. User starts an optimization run.
4. GA creates and evolves candidates.
5. Independent constraint checker validates the best candidate.
6. Run and schedule are persisted.
7. UI displays schedule, metrics, and diagnostics.
8. User exports CSV.

## Principles
Separate concerns; distinguish hard violations from soft penalties; record seeds and parameters; fail safely; keep local operation as the default.

## Serverless deployment
The root `api/index.py` exports the FastAPI app for Vercel's Python runtime. API request
handlers load the current dataset and run records from the storage adapter rather than
depending on process memory. Vercel deployments must provide `DATABASE_URL`; SQLite is
retained only for local development. Optimization is intentionally bounded by request
validation for this college-scale demo; larger workloads should move to background jobs.

## Later hardening phase
Background jobs, authentication, per-user workspaces, rate limiting, normalized migration
rollout, release tagging, and monitoring.

## Future product extensions
Manual editing with re-validation, spreadsheet import, PDF export, and alternative optimizer comparison.
