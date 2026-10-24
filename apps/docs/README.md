# Cronos — College Timetable Optimizer

Cronos is a local-first college timetable optimizer using a Genetic Algorithm (GA), a soft-computing technique.

## Stack
- Frontend: Next.js App Router and TypeScript
- Charts: API-backed custom metric bars and resource distributions
- Backend: Python, FastAPI, Pydantic
- Optimization: custom Genetic Algorithm
- Database: PostgreSQL/Neon when `DATABASE_URL` is configured, SQLite fallback for local development
- Tests: 15 pytest backend tests; 3 Vitest frontend tests; production build validation
- Packaging/deployment: intentionally deferred to a later phase

## Goals
Generate a weekly timetable that avoids faculty, room, and section clashes; respects availability, room type/capacity, session counts, and lab blocks; improves preferences and workload balance; and supports timetable views, metrics, and CSV export.

## MVP
Academic data validation, guided record entry plus JSON editing, configurable GA generation,
resource collection endpoints, schedule filtering, run metrics, persisted local state,
API-backed analytics, a plain-language Smart Scheduling overview with clear action feedback,
accessible loading/error/empty states, optional PostgreSQL/Neon storage, and CSV export.
Production deployment and operational hardening remain a later phase. For a Vercel
deployment, host `apps\web` as the frontend and deploy the FastAPI API separately with
`DATABASE_URL` pointing to hosted PostgreSQL; SQLite is local-development only.
No paid APIs or GPU required.

## Repository
See `PRD.md`, `ARCHITECTURE.md`, `ALGORITHM_DESIGN.md`, `DATA_MODEL_AND_API.md`, `AGENTS.md`, `INSTRUCTIONS.md`, `TEST_PLAN.md`, `REPORT.md`, `ROADMAP.md`, and `UI_DESIGN.md`.

Important: record actual implementation and measured results. Do not claim features or benchmarks that have not been tested.
