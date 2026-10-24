# Test Plan

## Objectives
Verify validation, constraint checking, GA correctness, API contracts, UI behavior, and measured quality against a baseline.

## Hard-constraint tests
- Detect overlapping sessions for the same faculty member.
- Detect overlapping room assignments.
- Detect overlapping sessions for the same section.
- Reject room capacity/type mismatch.
- Detect faculty/room/section unavailability.
- Detect missing or duplicate required sessions.
- Detect invalid days/periods.
- Detect broken consecutive lab blocks.
- Confirm valid schedules have zero hard violations.
- Confirm non-overlapping sessions may reuse the same room.
- Confirm duplicate day/period slots are rejected.
- Confirm run schedules use their input snapshot after data changes.

## GA tests
- Seeded run is reproducible where expected.
- Crossover preserves required session identity/count after repair.
- Mutation preserves data structure integrity.
- Repair has bounded attempts.
- Elitism preserves the best candidate.
- Hard violations always outrank soft penalty in comparison.
- Generation limit is respected.
- Feasible and best-effort results have distinct statuses.

## API tests
Test valid/invalid requests, missing resources, parameter bounds, run status/metrics, CRUD, analytics, CSV headers, health endpoint, and run snapshot isolation. Current automated API coverage passes.

## Frontend tests
The current automated suite covers schedule filtering. The implemented UI also provides
guided record validation, configurable controls, loading/error/empty states, section/faculty/
room filters, API-backed metric/resource displays, CSV export, keyboard focus styles, and
reduced-motion CSS behavior. Browser-level tests remain optional follow-up coverage.

## Evaluation
On a fixed dataset record entity counts, GA parameters, seed, runtime, hard violations, soft penalty, feasible-run rate across multiple seeds, and baseline metrics. The reproducible evaluator is `apps/evaluate.py`; it writes `apps/evaluation-results.json`. Do not invent targets or results after the fact.

## Exit criteria
Critical constraint tests pass; no known session loss/duplication in GA operators; API tests
pass; UI displays a generated schedule and validation summary; limitations are documented;
deployment-specific work is explicitly deferred.
