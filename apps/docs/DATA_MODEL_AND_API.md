# Data Model and API

## Entities
- **Faculty:** id, name, department, unavailable slots, preferred slots, optional daily load limit.
- **Room:** id, name, capacity, room type, unavailable slots.
- **Section:** id, name, size, department, semester.
- **Course:** id, code, name, required room type, duration, sessions per week, consecutive-slot requirement.
- **TeachingRequirement:** id, course, section, faculty, required sessions, duration, room requirements.
- **TimeSlot:** id, day, period index, start time, end time.
- **OptimizationRun:** id, status, timestamps, seed, parameters, input hash, hard violations, soft penalty, runtime, generations, diagnostics.
- **ScheduledSession:** id, run id, teaching requirement, occurrence index, slot/block, room.

## Persistence
The current adapter uses a durable `cronos_state` key/value table. It uses PostgreSQL/Neon when
`DATABASE_URL` is configured and SQLite at `CRONOS_SQLITE_PATH` otherwise. The normalized Alembic
schema exists for local validation; production migration rollout remains a later deployment phase.

## API conventions
Base prefix: `/api/v1`; JSON; Pydantic validation; consistent errors; never imply a schedule is valid without explicit status and constraint results.

## Suggested endpoints
- `GET /health`
- `GET/POST /api/v1/faculty`
- `GET/POST /api/v1/rooms`
- `GET/POST /api/v1/sections`
- `GET/POST /api/v1/courses`
- `GET/POST /api/v1/time-slots`
- `GET/POST /api/v1/teaching-requirements`
- `PUT/DELETE /api/v1/{collection}/{id}`
- `POST /api/v1/validate`
- `POST /api/v1/optimization-runs`
- `GET /api/v1/optimization-runs`
- `GET /api/v1/optimization-runs/{run_id}`
- `GET /api/v1/optimization-runs/{run_id}/schedule`
- `GET /api/v1/optimization-runs/{run_id}/metrics`
- `GET /api/v1/optimization-runs/{run_id}/analytics`
- `POST /api/v1/baseline`
- `POST /api/v1/baseline/greedy`
- `GET /api/v1/optimization-runs/{run_id}/export.csv`

## Example optimization request
```json
{
  "population_size": 80,
  "max_generations": 250,
  "crossover_probability": 0.8,
  "mutation_probability": 0.15,
  "tournament_size": 3,
  "elite_count": 2,
  "random_seed": 42,
  "soft_weights": {
    "faculty_preference": 3,
    "section_gaps": 2,
    "faculty_daily_load": 2
  }
}
```

## Example validation error
```json
{
  "valid": false,
  "errors": [{
    "code": "ROOM_CAPACITY",
    "message": "Assigned room is too small for the section.",
    "entity_id": "requirement-12"
  }],
  "warnings": []
}
```

## Error format
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "One or more fields are invalid.",
    "details": []
  }
}
```

Runs currently execute synchronously for small local datasets. Background jobs, authentication,
rate limits, and production migration operations are reserved for the deployment phase.
