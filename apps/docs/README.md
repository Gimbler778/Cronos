# Cronos — College Timetable Optimizer

Cronos is a local-first college timetable optimizer using a Genetic Algorithm (GA), a soft-computing technique.

## Stack
- Frontend: Next.js App Router and TypeScript
- Charts: API-backed custom metric bars and resource distributions
- Backend: Python, FastAPI, Pydantic
- Optimization: custom Genetic Algorithm
- Database: PostgreSQL/Neon when `DATABASE_URL` is configured, SQLite fallback for local development
- Tests: 30 pytest backend tests; 3 Vitest frontend tests; production build validation
- Packaging/deployment: Vercel multi-service deployment at https://cronos-sc.vercel.app

## Goals
Generate a weekly timetable that avoids faculty, room, and section clashes; respects availability, room type/capacity, session counts, and lab blocks; improves preferences and workload balance; and supports timetable views, metrics, and CSV export.

## MVP
Academic data validation, guided record entry plus JSON editing, configurable GA generation,
resource collection endpoints, schedule filtering, run metrics, persisted local state,
API-backed analytics, a plain-language Smart Scheduling overview with clear action feedback,
accessible loading/error/empty states, optional PostgreSQL/Neon storage, and CSV export.
The deployed MVP is available at https://cronos-sc.vercel.app. Vercel hosts the frontend
and FastAPI API together, with `DATABASE_URL` pointing to hosted PostgreSQL; SQLite is
local-development only.
No paid APIs or GPU required.

During local development, the browser frontend calls the FastAPI server at
`http://127.0.0.1:8000`; the API allows both local frontend origins. Production uses the
same-origin Vercel rewrite unless `NEXT_PUBLIC_API_BASE_URL` is set.

## Repository
See `PRD.md`, `ARCHITECTURE.md`, `ALGORITHM_DESIGN.md`, `DATA_MODEL_AND_API.md`, `AGENTS.md`, `INSTRUCTIONS.md`, `TEST_PLAN.md`, `REPORT.md`, `ROADMAP.md`, `UI_DESIGN.md`, and `ppt.md`.

Important: record actual implementation and measured results. Do not claim features or benchmarks that have not been tested.
