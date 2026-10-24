# AGENTS.md — Coding Instructions

## Source of truth
Follow `PRD.md`, `ARCHITECTURE.md`, `ALGORITHM_DESIGN.md`, and `DATA_MODEL_AND_API.md`.

## General
- Make small, focused changes.
- Do not claim features or benchmarks without evidence.
- Keep scheduling logic independent of FastAPI and React.
- Report hard violations separately from soft penalties.
- Never silently label an infeasible schedule valid.
- Use free/open-source dependencies; no paid APIs.
- Record random seed and GA parameters.
- Validate all user input server-side.
- Add tests for meaningful changes.
- Update docs when contracts or behavior change.

## Backend
Use Python type hints and Pydantic schemas. Route handlers delegate to services. Keep GA operators independently testable. Avoid global mutable state. Bound repair attempts and runtime. Do not leak stack traces as user-facing errors.

## Frontend
Use Next.js App Router and TypeScript. Use semantic React controls and the existing CSS
design system. Use a custom timetable/analytics presentation backed by real API data.
Keep API calls typed and local to the page until a shared client is justified. Avoid `any`.
Support keyboard navigation, visible focus, validation, loading, and error states. Respect
reduced-motion preferences.

## Algorithm correctness
Required sessions must not disappear or duplicate during crossover. Validate after crossover, mutation, and repair. Candidate comparison prioritizes hard violations then soft penalty. Test overlaps, capacity, availability, required counts, and consecutive labs.

## Workflow
1. Read relevant docs.
2. Implement the smallest useful change.
3. Update tests and schemas/types.
4. Run tests and report exact commands/results.
5. Update documentation.
6. Summarize changes and limitations.

## Do not
Do not add authentication, queues, cloud deployment, or external AI integrations without approval. Do not use fabricated metrics. Do not replace the timetable grid with a charting library.
