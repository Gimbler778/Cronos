# Algorithm Design — Genetic Algorithm

## Problem representation
Each `TeachingRequirement.required_sessions` occurrence becomes a schedulable session.
`Course.sessions_per_week` is retained as catalog metadata and does not override a
requirement. A chromosome is a list of assignments:
`(session_id, timeslot_id, room_id)`.
Faculty and section are derived from the session requirement. Model labs as block assignments where possible.

## Initialization
Create a population of candidate schedules with stochastic low-conflict construction:
each session chooses randomly among placements with the lowest current hard-constraint
count. Retain a feasible greedy seed when requested, but do not depend on it: stochastic
low-conflict initialization and repair must also be able to produce feasible schedules.

## Hard constraint checker
Count violations for faculty overlap, room overlap, section overlap, unavailability, unsuitable room type/capacity, missing/duplicate sessions, invalid slots, and broken lab blocks. Keep this checker independent from fitness scoring.

## Fitness
Compare candidates lexicographically:
1. Fewer hard-constraint violations is always better.
2. If tied, lower weighted soft penalty is better.

Soft penalties can include preference mismatch, section gaps, uneven daily workload, excessive consecutive periods, and poor distribution of repeated sessions. Faculty preferences are evaluated per faculty; a faculty member with no preferences incurs no preference penalty. Duration blocks contribute all occupied periods to load and gap metrics. Display both metrics separately.

## GA operators
- Selection: tournament selection, e.g. tournament size 3.
- Crossover: schedule-aware crossover that preserves required session IDs, followed by repair.
- Mutation: move a session, change its room, swap slots, or move a lab block.
- Mutation targets sessions named by current violations when possible, and includes
  assignment swaps to escape one-session local minima.
- Repair: bounded reassignment of one violation-targeted session, enumerating a small
  randomized placement budget and prioritizing constrained sessions.
- Improvement: apply bounded feasible single-session moves and pair swaps to the
  incumbent, accepting only hard-feasible soft-score improvements.
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
Feasibility is not an automatic stopping condition. Once a feasible candidate is found,
the search continues to optimize its soft penalty until it reaches the optional
`target_soft_penalty`, the generation limit, or the configured
`no_improvement_generations` budget. This prevents the greedy seed from making the GA
behave like an immediate feasibility checker while keeping runs bounded. Return clear
statuses such as `feasible`, `best_effort`, or `failed`.

## Evaluation
Compare against a simple greedy/randomized baseline on identical datasets. Record hard violations, soft penalty, runtime, feasible-run rate across seeds, and generations. Use both the small UI sample and a separate constrained benchmark; include seeded and unseeded GA ablations so the value of the greedy seed is visible.

## Limitations
A GA does not prove global optimality. Results depend on representation, operators, data,
parameters, and weights. Some input sets may be infeasible. A requirement duration is
the number of occupied consecutive periods; when omitted, it inherits the course
duration. `consecutive_slots_required` remains a compatibility flag for the same
block-based model rather than an independent non-consecutive scheduling mode.
