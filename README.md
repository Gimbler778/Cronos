# Cronos

Cronos is a local-first college timetable optimizer built around a reproducible
Genetic Algorithm. It validates academic data, generates schedules, reports hard
constraint violations and soft penalties, and exports completed schedules to CSV.

## MVP features

- FastAPI backend with Pydantic validation
- Genetic Algorithm with seeded runs, repair, elitism, and baseline comparison
- Faculty, room, section, course, time-slot, and teaching-requirement management
- Hard-constraint validation for clashes, availability, room capacity/type, session counts, and lab blocks
- Configurable soft-constraint weights and optimization parameters
- Next.js dashboard with guided data entry, JSON editing, schedule filters, analytics, and CSV export
- SQLite local persistence with optional PostgreSQL-compatible storage

## Run locally

From the repository root:

```powershell
npm install
npm run dev
```

This starts:

- API: `http://127.0.0.1:8000`
- Web app: `http://localhost:3000`

For separate setup instructions, see [apps/README.md](apps/README.md) and
[apps/docs/INSTRUCTIONS.md](apps/docs/INSTRUCTIONS.md).

## Validate the project

```powershell
npm run test:api
npm --prefix apps/web test -- --run
npm run build:web
npm run evaluate
```

## Documentation

- [Product requirements](apps/docs/PRD.md)
- [Architecture](apps/docs/ARCHITECTURE.md)
- [Algorithm design](apps/docs/ALGORITHM_DESIGN.md)
- [Data model and API](apps/docs/DATA_MODEL_AND_API.md)
- [Test plan](apps/docs/TEST_PLAN.md)
- [Project report](apps/docs/REPORT.md)
- [Roadmap](apps/docs/ROADMAP.md)

## Deployment status

This repository currently targets the local MVP. Production deployment,
authentication, background jobs, rate limiting, migration rollout, monitoring,
and release operations are reserved for a later phase.
