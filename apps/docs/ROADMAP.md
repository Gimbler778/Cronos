# Roadmap

## Phase 0 — Definition
- [x] Confirm days, periods, lab rules, and constraints.
- [x] Create a small documented sample dataset.
- [x] Freeze data model and API draft for the MVP.

## Phase 1 — Data and validation
- [x] Domain/Pydantic models.
- [x] Configure `DATABASE_URL`/`.env` and add Alembic migrations.
- [x] Add normalized persistence schema and storage adapter.
- [x] Input validation and diagnostics.
- [x] Seed data and validation tests.

## Phase 2 — Scheduler
- [x] Overlap utilities and hard-constraint checker.
- [x] Soft penalty functions.
- [x] Greedy/randomized baseline.
- [x] GA initialization, selection, crossover, mutation, elitism.
- [x] Repair operator.
- [x] Deterministic and infeasible-case tests.

## Phase 3 — API
- [x] Collection create/list and validation endpoints.
- [x] Optimization run endpoints.
- [x] Persist run metadata and schedule.
- [x] CSV export and integration tests.

## Phase 4 — UI
- [x] Next.js and TypeScript.
- [x] Dashboard and guided academic-data record form.
- [x] Schedule preview and filters.
- [x] Optimization controls and diagnostics.
- [x] API-backed analytics with custom accessible visualizations.
- [x] Subtle CSS motion with reduced-motion support.
- [x] Loading/error/empty states.

## Phase 5 — Evaluation
- [x] Compare GA with randomized baseline.
- [x] Run multiple seeds.
- [x] Record runtime, violations, penalty, and feasible-run rate.
- [x] Run backend/frontend tests and production build.
- [x] Update report with measured evidence.

## Phase 6 — Demonstration
- [x] Prepare sample dataset and demo flow.
- [ ] Capture screenshots (manual presentation task).
- [x] Explain encoding, fitness, operators, constraints, results, and limitations.
- [x] Finalize `REPORT.md` with measured results and limitations.
- [ ] Tag final version (repository/release task).

## Reserved for later deployment/release phase
Neon production hardening, normalized migration rollout, Docker Compose, authentication,
background jobs, rate limiting, hosted deployment, release tagging, and operational monitoring.

## Optional product extensions
XLSX/PDF import/export, manual schedule editing, alternative algorithms, and larger real-world datasets.
