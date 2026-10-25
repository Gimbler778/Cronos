# Product Requirements Document

## Summary
Cronos generates college timetables using a Genetic Algorithm. It helps administrators coordinate courses, faculty, sections, rooms, and time slots.

## Users
- Timetable administrator: configures data, constraints, runs optimization, exports schedules.
- Faculty and students: review schedules.
- Evaluator: reviews algorithm design, tests, and measured results.

## Functional requirements
1. Manage courses, faculty, rooms, sections, time slots, and teaching requirements.
2. Validate IDs, capacities, room types, availability, required sessions, and slot references.
3. Configure soft-constraint weights while keeping hard constraints mandatory.
4. Run the GA with configurable parameters and a reproducible random seed.
5. View schedules by section, faculty, or room.
6. Display hard violations, soft penalty, runtime, generations, and fitness progression.
7. Export schedules to CSV.
8. Save input and completed run snapshots in Neon (hosted PostgreSQL).
9. Show diagnostics when no feasible schedule is found.

## Hard constraints
- No overlapping sessions for a faculty member, room, or section.
- Room capacity and type must match the session requirements.
- Faculty/room/section availability must be respected.
- Every required session must appear exactly as required.
- Sessions must fall within configured working days and periods.
- Required lab blocks must use consecutive slots.

## Soft constraints
- Respect faculty preferred slots.
- Minimize gaps in a section's day.
- Balance faculty workload across days.
- Avoid excessive consecutive teaching periods.
- Distribute repeated sessions sensibly.

## Non-functional requirements
Local-first, no GPU or paid API, server-side validation, clear errors, responsive UI, deterministic tests where possible, and recorded GA configuration.

## Acceptance criteria
- Sample dataset can be loaded and validated.
- Constraint checker detects each hard-constraint type.
- GA finds a feasible schedule for a documented feasible sample.
- Infeasible/best-effort outcomes are clearly labeled.
- UI displays schedule and validation summary.
- CSV export and automated tests work.
- Saved data and the latest timetable survive a page refresh; an explicitly cleared
  workspace stays empty.
- Report includes actual environment and measured results.

## Delivery phases
0. Define constraints and dataset.
1. Data model, validation, persistence.
2. Constraint checker, fitness, GA, baseline.
3. API and export.
4. Frontend timetable and analytics.
5. Testing and baseline comparison.
6. Report, screenshots, and demonstration.
7. Deployment and persistence hardening.

## Risks
Infeasible input, slow convergence, misleading single fitness scores, scope creep, UI/API drift, and irreproducible results. Mitigate with input diagnostics, runtime limits, separate hard/soft metrics, a small MVP, shared API schemas, and recorded seeds.

## Out of scope for MVP
Production authentication, multi-tenant hosting, institutional integrations, paid APIs, and guaranteed global optimality.
