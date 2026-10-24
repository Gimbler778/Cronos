# Cronos — Soft Computing Project Report

> Status: MVP implementation report. Production deployment and operational hardening are intentionally deferred.

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
Included: data validation, GA, timetable views, analytics, CSV export, local persistence, evaluation.
Excluded from MVP: production authentication, paid APIs, GPU workloads, institutional integrations, and guaranteed global optimality.

## 5. Technology
Next.js, TypeScript, Python, FastAPI, Pydantic, custom Genetic Algorithm, SQLite fallback, optional PostgreSQL/Neon via psycopg, and Alembic migrations.

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
plain-language overview with Smart Scheduling and Ready/Running status indicators.
Production database rollout, authentication, background jobs, and hosted deployment are later-phase work.

## 9. Project journey
| Milestone | Work completed | Evidence/results | Next steps |
|---|---|---|---|
| Definition | Academic entities, hard/soft constraints, sample dataset | `apps/api/domain.py`, sample endpoint | Confirm institutional data requirements |
| Data model | Pydantic dataset and durable storage adapter | SQLite fallback; optional PostgreSQL; Alembic migration applies locally | Normalize repositories further |
| Constraint checker | Capacity/type, availability, overlap, slot-block and session-count checks | Backend suite passes 15 tests | Add more malformed-slot fixtures |
| Baseline | Seeded randomized candidate and greedy baseline | `apps/evaluate.py`; backend tests | Tune larger datasets |
| GA | Selection, crossover, mutation, elitism, bounded repair | Required session identity and reproducibility tests pass | Tune larger datasets |
| API | Validation, CRUD, runs, analytics, schedule, CSV | 15 backend tests pass | Add auth/rate limits only if required |
| UI | Guided record additions, JSON editor, generation controls, filtered schedule, analytics, and async states | Next.js production build and Vitest suite pass | Add browser-level tests if needed |
| Evaluation | Five-seed comparison on documented sample | Both methods feasible 5/5; GA mean soft penalty 1.2; baseline 1.0 | Repeat on larger real dataset |

## 10. Experimental setup
Hardware/OS: Windows development environment
Dataset size: 1 faculty, 2 rooms, 1 section, 1 course, 3 time slots, 1 teaching requirement
Population/generations: 40 / 100
Mutation/crossover: 0.15 / 0.8
Seeds: 1, 7, 42, 99, 123
Baseline: One randomized candidate per seed, evaluated with the same constraint checker

## 11. Results
| Metric | Baseline | GA |
|---|---:|---:|
| Hard violations | mean 0.0 | mean 0.0 |
| Soft penalty | mean 1.0 | mean 1.2 |
| Runtime | mean 0 ms | mean 1 ms |
| Feasible runs / total | 5 / 5 | 5 / 5 |

The sample is intentionally small, so these results demonstrate reproducibility and
constraint satisfaction rather than general performance or superiority. On this sample,
the randomized baseline happened to achieve a lower soft penalty; the GA should not be
described as better from this experiment alone.

## 12. Testing
The backend suite has 15 passing tests covering seeded reproducibility, required-session
preservation, hard constraints, API flow, CRUD, analytics, export, invalid references,
baseline bounds, duplicate slot positions, and run snapshot isolation. The frontend suite
has 3 passing schedule-filter tests. The Next.js production build passes. The evaluator
also completes successfully and writes `evaluation-results.json`.

## 13. Challenges and solutions
The project keeps algorithm terminology such as GA in technical controls and documentation,
but uses plain-language Smart Scheduling and Ready/Running status copy in the primary
overview to reduce user confusion. The UI/API boundary is covered by explicit loading,
error, empty, validation, and run-status states. The scheduler also preserves required
session identity through crossover, mutation, and repair, with hard violations ranked
ahead of soft penalties during candidate comparison.

## 14. Limitations
A GA does not guarantee global optimality. Quality depends on encoding, parameters, data, and weights. Some datasets may be infeasible. Soft weights encode design choices.

## 15. Future work
Manual editing with re-validation, background jobs, spreadsheet import, PDF export, authentication, improved diagnostics, algorithm comparison, and optional deployment.

## 16. Conclusion
Cronos delivers a tested local-first timetable MVP with explicit hard-constraint validation,
seeded genetic optimization, baseline comparison, persisted run snapshots, a configurable
web workflow, analytics, filtering, and CSV export. The evidence supports correct behavior
on the documented sample, not global optimality or production readiness. Deployment,
authentication, background execution, operational monitoring, and larger-dataset validation
are reserved for the next phase.

## References
References used during implementation include the FastAPI, Pydantic, Next.js, React,
TypeScript, pytest, and Vitest official documentation. Add formal academic references
required by the course submission format before final submission.
