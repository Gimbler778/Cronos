# Algorithm Design — Genetic Algorithm

## Problem representation
Each required course occurrence becomes a schedulable session. A chromosome is a list of assignments:
`(session_id, timeslot_id, room_id)`.
Faculty and section are derived from the session requirement. Model labs as block assignments where possible.

## Initialization
Create a population of candidate schedules, biasing choices toward available faculty, suitable rooms, valid slots, and consecutive lab blocks. Always retain a feasible greedy seed when one can be constructed so random exploration cannot regress to an infeasible best result.

## Hard constraint checker
Count violations for faculty overlap, room overlap, section overlap, unavailability, unsuitable room type/capacity, missing/duplicate sessions, invalid slots, and broken lab blocks. Keep this checker independent from fitness scoring.

## Fitness
Compare candidates lexicographically:
1. Fewer hard-constraint violations is always better.
2. If tied, lower weighted soft penalty is better.

Soft penalties can include preference mismatch, section gaps, uneven daily workload, excessive consecutive periods, and poor distribution of repeated sessions. Display both metrics separately.

## GA operators
- Selection: tournament selection, e.g. tournament size 3.
- Crossover: schedule-aware crossover that preserves required session IDs, followed by repair.
- Mutation: move a session, change its room, swap slots, or move a lab block.
- Repair: bounded reassignment of invalid sessions, prioritizing constrained sessions.
- Elitism: retain a small number of best candidates each generation.

## Initial parameters (tune experimentally)
Population 80; max generations 250; crossover probability 0.8; mutation probability 0.15; tournament size 3; elite count 2; configurable random seed.

## Pseudocode
```text
validate input
population = initialize()
evaluate candidates
for generation in 1..max_generations:
    next = keep_elites(population)
    while next is not full:
        parents = tournament_select(population)
        child = crossover(parents)
        mutate(child)
        child = repair(child)
        evaluate(child)
        append child
    population = next
    record best metrics
    stop if target or budget reached
independently validate best candidate
return schedule, status, metrics, diagnostics
```

## Stopping and status
Stop at target quality, generation limit, runtime limit, or a configured no-improvement limit. Return clear statuses such as `feasible`, `best_effort`, or `failed`.

## Evaluation
Compare against a simple greedy/randomized baseline on identical datasets. Record hard violations, soft penalty, runtime, feasible-run rate across seeds, and generations.

## Limitations
A GA does not prove global optimality. Results depend on representation, operators, data, parameters, and weights. Some input sets may be infeasible.
