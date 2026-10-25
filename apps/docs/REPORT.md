# Cronos — Soft Computing Project Report

> Status: deployed MVP implementation report. Operational hardening, authentication, and
> large-scale validation remain deferred.

## Title
**Cronos: College Timetable Optimization Using a Genetic Algorithm**

## Abstract
Cronos is a timetable optimization application designed to reduce manual scheduling effort. It represents teaching requirements, faculty, rooms, sections, and time slots, then uses a Genetic Algorithm to search for schedules satisfying hard constraints while improving soft preferences. A web interface presents schedules and optimization metrics.

## 1. Introduction
College scheduling requires coordination of faculty, rooms, courses, sections, and time periods. Manual preparation can create clashes and inefficient gaps. This project explores evolutionary computation for this combinatorial optimization task.

## 2. Problem statement
Generate a weekly college timetable from structured academic data while minimizing resource conflicts and improving schedule quality.

## 3. Objectives
Model academic data; define hard/soft constraints; implement a GA; build timetable and analytics UI; compare against a baseline; document limitations.

## 4. Scope
Included: data validation, GA, timetable views, analytics, CSV export, durable persistence
(local SQLite and hosted PostgreSQL), deployment, and evaluation.
Excluded from MVP: production authentication, paid APIs, GPU workloads, institutional integrations, and guaranteed global optimality.

## 5. Technology
Next.js, TypeScript, Python, FastAPI, Pydantic, custom Genetic Algorithm, SQLite fallback, PostgreSQL/Neon via psycopg with JSONB state, Alembic migrations, and a Vercel multi-service deployment.

## 6. Methodology
1. Model scheduling requirements.
2. Validate input.
3. Encode each session as an assignment.
4. Initialize population.
5. Evaluate hard violations and soft penalties.
6. Select, crossover, mutate, repair, and preserve elites.
7. Stop at configured limits.
8. Independently validate the best schedule.
9. Compare against baseline.

## 7. Constraints
Hard: faculty/room/section clashes, availability, room type/capacity, session counts, valid slots, consecutive labs.
Soft: preferences, section gaps, balanced daily load, consecutive periods, distribution of repeated sessions.

## 8. Architecture
The browser uses the Next.js dashboard in `apps/web`. It calls the versioned FastAPI
application in `apps/api`, which validates Pydantic datasets, runs the scheduler, stores
run snapshots through the local SQLite/PostgreSQL-compatible adapter, and exposes schedule,
metrics, analytics, and CSV endpoints. The UI includes guided record additions, an advanced
JSON editor, configurable GA controls, schedule filters, API-backed analytics, and a
plain-language Smart Scheduling overview with clear action feedback.
The MVP is deployed at https://cronos-sc.vercel.app with PostgreSQL-backed state.
Authentication, background jobs, and normalized migration rollout remain later-phase work.

## 9. Project journey
| Milestone | Work completed | Evidence/results | Next steps |
|---|---|---|---|
| Definition | Academic entities, hard/soft constraints, sample dataset | `apps/api/domain.py`, sample endpoint | Confirm institutional data requirements |
| Data model | Pydantic dataset and durable storage adapter | SQLite fallback; optional PostgreSQL; Alembic migration applies locally | Normalize repositories further |
| Constraint checker | Capacity/type, availability, overlap, slot-block and session-count checks | Backend suite passes 30 tests | Add more malformed-slot fixtures |
| Baseline | Seeded randomized candidate and greedy baseline | `apps/evaluate.py`; backend tests | Tune larger datasets |
| GA | Selection, crossover, mutation, elitism, bounded repair | Required session identity and reproducibility tests pass | Tune larger datasets |
| API | Validation, CRUD, runs, analytics, schedule, CSV, persistence semantics, local CORS | 30 backend tests pass | Add auth/rate limits only if required |
| UI | Guided record additions, JSON editor, generation controls, filtered schedule, analytics, and async states | Next.js production build and Vitest suite pass | Add browser-level tests if needed |
| Evaluation | Five-seed comparison on documented sample | Baseline feasible 5/5; greedy-seeded GA feasible 5/5 | Test larger, harder datasets |

## 10. Experimental setup
Hardware/OS: Windows development environment
Dataset size: 3 faculty, 4 rooms, 3 sections, 4 courses, 15 time slots, 6 teaching requirements
Population/generations: 24 / 60; no-improvement budget: 25 generations
Mutation/crossover: 0.15 / 0.8
Seeds: 1, 7, 42, 99, 123
Baseline: Greedy construction (`greedy_baseline`) per seed, evaluated with the same constraint checker

## 11. Results
| Metric | Baseline | GA |
|---|---:|---:|
| Hard violations | mean 0.0 | mean 0.0 |
| Soft penalty | mean 7.0 | mean 7.0 |
| Runtime | mean 45.4 ms | mean 3015.2 ms |
| Feasible runs / total | 5 / 5 | 5 / 5 |

The GA finds a feasible schedule on every recorded seed and matches the baseline's soft
penalty on the small documented sample. Feasibility alone no longer terminates the GA:
it continues until the soft target, generation limit, or no-improvement budget is reached.
The sample still produces parity, so it is not evidence of global optimality.

The benchmark evaluator uses a separate constrained dataset with 5 faculty, 4 rooms,
5 sections, 6 courses, 20 time slots, and 12 teaching requirements. Constructive greedy,
greedy plus feasible local search, seeded GA, unseeded GA, and an unseeded GA without
feasible local search are measured on the same seeds. The greedy-plus-local-search
variant is included to avoid attributing all improvement over constructive greedy to
genetic operators. Results therefore describe the complete hybrid optimizer; they do not
prove that the GA component alone beats an equivalent local-search baseline. In the
recorded run, constructive greedy achieved 31.0 mean soft penalty, greedy plus local
search achieved 27.0, and seeded and unseeded GA achieved 22.4. The unseeded GA without
local search achieved 26.2. All variants were feasible on 5/5 seeds. Runtime figures
are environment-dependent, and the evaluator records the seed list and all variant
metrics in `apps/evaluation-results.json`. These results are not a global-optimality
claim.

## 12. Testing
The backend suite has 30 passing tests covering seeded reproducibility, required-session
preservation, hard constraints, API flow, CRUD, analytics, export filters, invalid
references, duplicate requirement IDs, baseline bounds, duplicate slot positions, run snapshot isolation, and the
clear/reset persistence semantics. The frontend suite has 3 passing schedule-filter tests.
The Next.js production build passes. The evaluator also completes successfully and writes
`evaluation-results.json`.

## 13. Challenges and solutions
The project keeps algorithm terminology such as GA in technical controls and documentation,
but uses plain-language Smart Scheduling and clear action feedback in the primary overview
to reduce user confusion. The UI/API boundary is covered by explicit loading,
error, empty, validation, and run-status states. The scheduler also preserves required
session identity through crossover, mutation, and repair, with hard violations ranked
ahead of soft penalties during candidate comparison. A later persistence fix replaced the
frontend's repeated sample-data reload with a first-run seed, an explicit reset, and a
latest-run restore so saved work survives refreshes.

## 14. Limitations
A GA does not guarantee global optimality. Quality depends on encoding, parameters, data, and weights. Some datasets may be infeasible. Soft weights encode design choices.

## 15. Future work
Manual editing with re-validation, larger benchmark datasets, background jobs, spreadsheet
and PDF import/export, authentication, improved diagnostics, alternative optimizer
comparison, and operational monitoring.

## 16. Conclusion
Cronos delivers a tested, deployed timetable MVP with explicit hard-constraint validation,
hybrid seeded/unseeded genetic optimization with feasible local search, baseline comparison, persisted run snapshots, a configurable
web workflow, analytics, filtering, and CSV export. The recorded sample shows feasibility
parity with the greedy baseline; the evidence does not support global optimality or
institutional-scale readiness. Authentication, background execution, operational
monitoring, and larger-dataset validation are reserved for the next phase.

## References
References used during implementation include the FastAPI, Pydantic, Next.js, React,
TypeScript, pytest, and Vitest official documentation. Add formal academic references
required by the course submission format before final submission.
