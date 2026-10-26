from __future__ import annotations

import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass

from apps.api.domain import Assignment, Candidate, Dataset, Faculty, Room, RunResult, Section, Session, TimeSlot


class ScheduleContext:
    def __init__(self, data: Dataset, sessions: list[Session]):
        self.data = data
        self.sessions = sessions
        self.slots = {slot.id: slot for slot in data.time_slots}
        self.rooms = {room.id: room for room in data.rooms}
        self.faculty = {item.id: item for item in data.faculty}
        self.sections = {item.id: item for item in data.sections}
        self.session_map = {item.id: item for item in sessions}
        self.by_day_period = {(slot.day, slot.period): slot for slot in data.time_slots}

        self.occupied_slots: dict[tuple[str, int, bool], list[TimeSlot]] = {}
        for slot in data.time_slots:
            for duration in {sess.duration for sess in sessions} | {1}:
                for consecutive in (True, False):
                    if not consecutive:
                        self.occupied_slots[(slot.id, duration, consecutive)] = [slot]
                    else:
                        self.occupied_slots[(slot.id, duration, consecutive)] = [
                            self.by_day_period[(slot.day, slot.period + offset)]
                            for offset in range(duration)
                            if (slot.day, slot.period + offset) in self.by_day_period
                        ]

        self.valid_rooms_by_session: dict[str, list[Room]] = {}
        self.valid_slots_by_session: dict[str, list[TimeSlot]] = {}
        for session in sessions:
            sec = self.sections.get(session.section_id)
            sec_size = sec.size if sec else 0
            matching_rooms = [
                r for r in data.rooms
                if r.room_type == session.room_type and r.capacity >= sec_size
            ]
            self.valid_rooms_by_session[session.id] = matching_rooms or list(data.rooms)

            matching_slots = [
                slot for slot in data.time_slots
                if (not session.consecutive_required or len(self.occupied_slots.get((slot.id, session.duration, True), [])) == session.duration)
            ]
            self.valid_slots_by_session[session.id] = matching_slots or list(data.time_slots)


def expand_sessions(data: Dataset) -> list[Session]:
    courses = {item.id: item for item in data.courses}
    result: list[Session] = []
    for requirement in data.teaching_requirements:
        course = courses.get(requirement.course_id)
        if course is None:
            raise ValueError(f"Teaching requirement '{requirement.id}' references missing course '{requirement.course_id}'.")
        duration = requirement.duration or course.duration
        room_type = requirement.room_type or course.required_room_type
        for occurrence in range(requirement.required_sessions):
            result.append(Session(
                id=f"{requirement.id}:{occurrence + 1}",
                requirement_id=requirement.id,
                occurrence=occurrence + 1,
                course_id=requirement.course_id,
                section_id=requirement.section_id,
                faculty_id=requirement.faculty_id,
                duration=duration,
                room_type=room_type,
                consecutive_required=course.consecutive_slots_required,
            ))
    return result


def _slot_ids(data: Dataset) -> dict[str, object]:
    return {slot.id: slot for slot in data.time_slots}


def _occupied_slots(data: Dataset, slot_id: str, duration: int, consecutive: bool = True, context: ScheduleContext | None = None) -> list[object]:
    if context is not None:
        return context.occupied_slots.get((slot_id, duration, consecutive), [])
    slots = _slot_ids(data)
    start = slots.get(slot_id)
    if start is None:
        return []
    by_day_period = {(slot.day, slot.period): slot for slot in data.time_slots}
    if not consecutive:
        return [start]
    return [
        by_day_period[(start.day, start.period + offset)]
        for offset in range(duration)
        if (start.day, start.period + offset) in by_day_period
    ]


def validate_candidate(data: Dataset, sessions: list[Session], candidate: Candidate, context: ScheduleContext | None = None) -> Candidate:
    if context is None:
        context = ScheduleContext(data, sessions)
    slots = context.slots
    rooms = context.rooms
    faculty = context.faculty
    sections = context.sections
    session_map = context.session_map
    occupied_cache = context.occupied_slots

    violations: list[dict[str, str]] = []

    if len(candidate.assignments) != len(sessions):
        seen = Counter(item.session_id for item in candidate.assignments)
        for session in sessions:
            if seen[session.id] != 1:
                code = "MISSING_SESSION" if seen[session.id] == 0 else "DUPLICATE_SESSION"
                violations.append({"code": code, "entity_id": session.requirement_id})
    else:
        cand_ids = [item.session_id for item in candidate.assignments]
        if len(set(cand_ids)) != len(sessions):
            seen = Counter(cand_ids)
            for session in sessions:
                if seen[session.id] != 1:
                    code = "MISSING_SESSION" if seen[session.id] == 0 else "DUPLICATE_SESSION"
                    violations.append({"code": code, "entity_id": session.requirement_id})

    groups: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)
    for assignment in candidate.assignments:
        session = session_map.get(assignment.session_id)
        slot = slots.get(assignment.slot_id)
        room = rooms.get(assignment.room_id)
        if session is None or slot is None:
            violations.append({"code": "INVALID_SLOT", "entity_id": assignment.session_id})
            continue
        if room is None:
            violations.append({"code": "INVALID_ROOM", "entity_id": assignment.session_id})
            continue
        sec = sections.get(session.section_id)
        fac = faculty.get(session.faculty_id)
        if sec is None or fac is None:
            violations.append({"code": "INVALID_REFERENCE", "entity_id": session.requirement_id})
            continue
        if room.capacity < sec.size:
            violations.append({"code": "ROOM_CAPACITY", "entity_id": session.requirement_id})
        if room.room_type != session.room_type:
            violations.append({"code": "ROOM_TYPE", "entity_id": session.requirement_id})
        occupied = occupied_cache.get((assignment.slot_id, session.duration, session.consecutive_required), [])
        if session.consecutive_required and len(occupied) != session.duration:
            violations.append({"code": "BROKEN_CONSECUTIVE_BLOCK", "entity_id": session.requirement_id})
        for occupied_slot in occupied:
            if occupied_slot.id in room.unavailable_slots:
                violations.append({"code": "ROOM_UNAVAILABLE", "entity_id": room.id})
            if occupied_slot.id in fac.unavailable_slots:
                violations.append({"code": "FACULTY_UNAVAILABLE", "entity_id": session.faculty_id})
            if occupied_slot.id in sec.unavailable_slots:
                violations.append({"code": "SECTION_UNAVAILABLE", "entity_id": session.section_id})
            key = (occupied_slot.day, occupied_slot.period)
            groups[("faculty", session.faculty_id)].append(key)
            groups[("section", session.section_id)].append(key)
            groups[("room", assignment.room_id)].append(key)

    for (kind, entity), values in groups.items():
        if len(values) > len(set(values)):
            duplicates = [val for val, count in Counter(values).items() if count > 1]
            for val in duplicates:
                violations.append({"code": f"{kind.upper()}_OVERLAP", "entity_id": entity, "slot": f"{val[0]}:{val[1]}"})

    candidate.violations = violations
    candidate.hard_violations = len(violations)
    return candidate


def soft_penalty(data: Dataset, sessions: list[Session], candidate: Candidate, weights: dict[str, float], context: ScheduleContext | None = None) -> float:
    if context is None:
        context = ScheduleContext(data, sessions)
    slots = context.slots
    session_map = context.session_map
    faculty_by_id = context.faculty
    occupied_cache = context.occupied_slots

    penalty = 0.0
    section_periods: dict[tuple[str, str], list[int]] = defaultdict(list)
    by_faculty_day: dict[tuple[str, str], int] = defaultdict(int)
    by_requirement_day: dict[tuple[str, str], int] = defaultdict(int)
    periods_by_faculty_day: dict[tuple[str, str], list[int]] = defaultdict(list)

    pref_weight = weights.get("faculty_preference", 1)
    for assignment in candidate.assignments:
        session = session_map.get(assignment.session_id)
        slot = slots.get(assignment.slot_id)
        if not session or not slot:
            continue
        fac = faculty_by_id.get(session.faculty_id)
        if fac and fac.preferred_slots and assignment.slot_id not in fac.preferred_slots:
            penalty += pref_weight

        occupied = occupied_cache.get((assignment.slot_id, session.duration, session.consecutive_required), [])
        occ_len = len(occupied)
        by_faculty_day[(session.faculty_id, slot.day)] += occ_len
        by_requirement_day[(session.requirement_id, slot.day)] += 1
        sec_key = (session.section_id, slot.day)
        fac_key = (session.faculty_id, slot.day)
        for occupied_slot in occupied:
            section_periods[sec_key].append(occupied_slot.period)
            periods_by_faculty_day[fac_key].append(occupied_slot.period)

    gap_weight = weights.get("section_gaps", 1)
    if gap_weight > 0:
        for periods in section_periods.values():
            if len(periods) > 1:
                ordered = sorted(set(periods))
                penalty += max(0, ordered[-1] - ordered[0] + 1 - len(ordered)) * gap_weight

    load_weight = weights.get("faculty_daily_load", 1)
    if load_weight > 0:
        for (faculty_id, _day), counts in by_faculty_day.items():
            fac = faculty_by_id.get(faculty_id)
            limit = (fac.daily_load_limit if fac else None) or 3
            if counts > limit:
                penalty += (counts - limit) * load_weight

    consec_weight = weights.get("consecutive_periods", 1)
    if consec_weight > 0:
        for periods in periods_by_faculty_day.values():
            if len(periods) > 3:
                consecutive = 1
                for previous, current in zip(sorted(set(periods)), sorted(set(periods))[1:]):
                    consecutive = consecutive + 1 if current == previous + 1 else 1
                    if consecutive > 3:
                        penalty += consec_weight

    repeat_weight = weights.get("repeat_distribution", 1)
    if repeat_weight > 0:
        for count in by_requirement_day.values():
            if count > 1:
                penalty += (count - 1) * repeat_weight

    candidate.soft_penalty = penalty
    return penalty


def _random_candidate(
    rng: random.Random,
    data: Dataset,
    sessions: list[Session],
    context: ScheduleContext | None = None,
) -> Candidate:
    """Build a stochastic low-conflict candidate without using the greedy baseline."""
    if context is None:
        context = ScheduleContext(data, sessions)
    candidate = Candidate([])
    for session in sorted(sessions, key=lambda item: (-item.duration, item.id)):
        valid_rooms = context.valid_rooms_by_session.get(session.id, data.rooms)
        valid_slots = context.valid_slots_by_session.get(session.id, data.time_slots)
        placements = [
            Assignment(session.id, slot.id, room.id)
            for slot in valid_slots
            for room in valid_rooms
        ]
        rng.shuffle(placements)
        best_hard = None
        best_placements: list[Assignment] = []
        for placement in placements:
            trial = Candidate(candidate.assignments + [placement])
            validate_candidate(data, sessions, trial, context=context)
            if best_hard is None or trial.hard_violations < best_hard:
                best_hard = trial.hard_violations
                best_placements = [placement]
            elif trial.hard_violations == best_hard:
                best_placements.append(placement)
        if best_placements:
            candidate.assignments.append(rng.choice(best_placements))
    return candidate


def _copy_candidate(candidate: Candidate) -> Candidate:
    return Candidate(
        assignments=[
            Assignment(item.session_id, item.slot_id, item.room_id)
            for item in candidate.assignments
        ],
        hard_violations=candidate.hard_violations,
        soft_penalty=candidate.soft_penalty,
        violations=list(candidate.violations),
    )


def _tournament(rng: random.Random, population: list[Candidate], size: int) -> Candidate:
    return min(rng.sample(population, min(size, len(population))), key=lambda item: item.score())


def _crossover_candidate(
    rng: random.Random,
    sessions: list[Session],
    left: Candidate,
    right: Candidate,
) -> Candidate:
    """Combine parents by session identity rather than chromosome position."""
    left_by_id = {assignment.session_id: assignment for assignment in left.assignments}
    right_by_id = {assignment.session_id: assignment for assignment in right.assignments}
    assignments: list[Assignment] = []
    for session in sessions:
        options = [
            assignment
            for assignment in (left_by_id.get(session.id), right_by_id.get(session.id))
            if assignment is not None
        ]
        if options:
            chosen = rng.choice(options)
            assignments.append(Assignment(chosen.session_id, chosen.slot_id, chosen.room_id))
    return Candidate(assignments)


def _mutate_candidate(
    rng: random.Random,
    data: Dataset,
    sessions: list[Session],
    candidate: Candidate,
    swap_probability: float,
    context: ScheduleContext | None = None,
) -> Candidate:
    assignments = [Assignment(item.session_id, item.slot_id, item.room_id) for item in candidate.assignments]
    if not assignments:
        return Candidate(assignments)
    if context is None:
        context = ScheduleContext(data, sessions)
    session_map = context.session_map
    target_ids = {
        violation.get("entity_id")
        for violation in candidate.violations
        if violation.get("code", "").endswith(("OVERLAP", "UNAVAILABLE", "CAPACITY", "TYPE"))
    }
    targeted = [
        index for index, assignment in enumerate(assignments)
        if assignment.session_id in target_ids
        or (
            session_map.get(assignment.session_id) is not None
            and (
                session_map[assignment.session_id].faculty_id in target_ids
                or session_map[assignment.session_id].section_id in target_ids
                or session_map[assignment.session_id].requirement_id in target_ids
            )
        )
    ]
    index = rng.choice(targeted or list(range(len(assignments))))
    if len(assignments) > 1 and rng.random() < swap_probability:
        other = rng.randrange(len(assignments) - 1)
        if other >= index:
            other += 1
        assignments[index].slot_id, assignments[other].slot_id = assignments[other].slot_id, assignments[index].slot_id
    else:
        current = assignments[index]
        valid_slots = context.valid_slots_by_session.get(current.session_id, data.time_slots)
        valid_rooms = context.valid_rooms_by_session.get(current.session_id, data.rooms)
        assignments[index] = Assignment(
            current.session_id,
            rng.choice(valid_slots).id,
            rng.choice(valid_rooms).id,
        )
    return Candidate(assignments)


def _repair_candidate(
    rng: random.Random,
    data: Dataset,
    sessions: list[Session],
    candidate: Candidate,
    weights: dict[str, float],
    attempts_per_assignment: int = 2,
    context: ScheduleContext | None = None,
) -> Candidate:
    """Repair conflicting assignments by choosing the best enumerated location."""
    if context is None:
        context = ScheduleContext(data, sessions)
    validate_candidate(data, sessions, candidate, context=context)
    soft_penalty(data, sessions, candidate, weights, context=context)
    session_map = context.session_map
    max_passes = 1
    for _ in range(max_passes):
        before = candidate.score()
        targeted_ids = {
            violation.get("entity_id")
            for violation in candidate.violations
            if violation.get("code", "").endswith(
                ("OVERLAP", "UNAVAILABLE", "CAPACITY", "TYPE", "CONSECUTIVE_BLOCK")
            )
        }
        indexes = [
            index
            for index, assignment in enumerate(candidate.assignments)
            if assignment.session_id in targeted_ids
            or (
                (session := session_map.get(assignment.session_id)) is not None
                and (
                    session.faculty_id in targeted_ids
                    or session.section_id in targeted_ids
                    or session.requirement_id in targeted_ids
                    or assignment.room_id in targeted_ids
                )
            )
        ]
        if not indexes:
            indexes = list(range(len(candidate.assignments)))
        rng.shuffle(indexes)
        repair_limit = min(len(indexes), 1)
        for index in indexes[:repair_limit]:
            assignment = candidate.assignments[index]
            best = candidate
            valid_rooms = context.valid_rooms_by_session.get(assignment.session_id, data.rooms)
            valid_slots = context.valid_slots_by_session.get(assignment.session_id, data.time_slots)
            alternatives = [
                (slot, room)
                for slot in valid_slots
                for room in valid_rooms
                if slot.id != assignment.slot_id or room.id != assignment.room_id
            ]
            rng.shuffle(alternatives)
            limit = len(alternatives) if attempts_per_assignment >= 10 else max(8, attempts_per_assignment * 4)
            for slot, room in alternatives[:limit]:
                trial_assignments = [
                    Assignment(item.session_id, item.slot_id, item.room_id)
                    for item in candidate.assignments
                ]
                trial_assignments[index] = Assignment(
                    assignment.session_id, slot.id, room.id
                )
                trial = Candidate(trial_assignments)
                validate_candidate(data, sessions, trial, context=context)
                soft_penalty(data, sessions, trial, weights, context=context)
                if trial.score() < best.score():
                    best = trial
            candidate = best
        if candidate.score() >= before:
            break
    return candidate


def _improve_feasible(
    data: Dataset,
    sessions: list[Session],
    candidate: Candidate,
    weights: dict[str, float],
    max_passes: int = 2,
    context: ScheduleContext | None = None,
) -> Candidate:
    """Use bounded feasible moves to improve soft quality after construction."""
    if context is None:
        context = ScheduleContext(data, sessions)
    validate_candidate(data, sessions, candidate, context=context)
    soft_penalty(data, sessions, candidate, weights, context=context)
    if candidate.hard_violations:
        return candidate
    for _ in range(max_passes):
        before = candidate.score()
        incumbent = candidate
        for index, assignment in enumerate(candidate.assignments):
            valid_rooms = context.valid_rooms_by_session.get(assignment.session_id, data.rooms)
            valid_slots = context.valid_slots_by_session.get(assignment.session_id, data.time_slots)
            for slot in valid_slots:
                for room in valid_rooms:
                    if slot.id == assignment.slot_id and room.id == assignment.room_id:
                        continue
                    trial_assignments = [
                        Assignment(item.session_id, item.slot_id, item.room_id)
                        for item in candidate.assignments
                    ]
                    trial_assignments[index] = Assignment(assignment.session_id, slot.id, room.id)
                    trial = Candidate(trial_assignments)
                    validate_candidate(data, sessions, trial, context=context)
                    if trial.hard_violations > 0:
                        continue
                    soft_penalty(data, sessions, trial, weights, context=context)
                    if trial.score() < incumbent.score():
                        incumbent = trial
        for left_index in range(len(candidate.assignments)):
            left = candidate.assignments[left_index]
            left_session = context.session_map.get(left.session_id)
            for right_index in range(left_index + 1, len(candidate.assignments)):
                right = candidate.assignments[right_index]
                right_session = context.session_map.get(right.session_id)
                if left.slot_id == right.slot_id:
                    continue
                if left_session and right_session and left_session.duration != right_session.duration:
                    if left_session.consecutive_required and len(context.occupied_slots.get((right.slot_id, left_session.duration, True), [])) != left_session.duration:
                        continue
                    if right_session.consecutive_required and len(context.occupied_slots.get((left.slot_id, right_session.duration, True), [])) != right_session.duration:
                        continue
                trial_assignments = [
                    Assignment(item.session_id, item.slot_id, item.room_id)
                    for item in candidate.assignments
                ]
                trial_assignments[left_index] = Assignment(left.session_id, right.slot_id, left.room_id)
                trial_assignments[right_index] = Assignment(right.session_id, left.slot_id, right.room_id)
                trial = Candidate(trial_assignments)
                validate_candidate(data, sessions, trial, context=context)
                if trial.hard_violations > 0:
                    continue
                soft_penalty(data, sessions, trial, weights, context=context)
                if trial.score() < incumbent.score():
                    incumbent = trial
        candidate = incumbent
        if candidate.score() == before:
            break
    return candidate


def greedy_baseline(
    data: Dataset,
    soft_weights: dict[str, float] | None = None,
    improve_feasible: bool = True,
    context: ScheduleContext | None = None,
) -> RunResult:
    started = time.perf_counter()
    if not data.time_slots or not data.rooms:
        return RunResult("failed", None, 0, 0, [], ["At least one time slot and room are required."])
    sessions = expand_sessions(data)
    if context is None:
        context = ScheduleContext(data, sessions)
    weights = soft_weights or {}
    candidate = Candidate([])
    for session in sorted(sessions, key=lambda item: (-item.duration, item.id)):
        best: Candidate | None = None
        valid_rooms = context.valid_rooms_by_session.get(session.id, data.rooms)
        valid_slots = context.valid_slots_by_session.get(session.id, data.time_slots)
        for slot in valid_slots:
            for room in valid_rooms:
                trial = Candidate(candidate.assignments + [Assignment(session.id, slot.id, room.id)])
                validate_candidate(data, sessions, trial, context=context)
                soft_penalty(data, sessions, trial, weights, context=context)
                if best is None or trial.score() < best.score():
                    best = trial
        if best is None:
            return RunResult("failed", None, 0, int((time.perf_counter() - started) * 1000), [], ["No candidate assignment could be constructed."])
        candidate = best
    status = "feasible" if candidate.hard_violations == 0 else "best_effort"
    for _ in range(len(sessions)):
        if candidate.hard_violations == 0:
            break
        candidate = _repair_candidate(
            random.Random(_),
            data,
            sessions,
            candidate,
            weights,
            attempts_per_assignment=10,
            context=context,
        )
    if candidate.hard_violations:
        for seed in range(20):
            candidate = _random_candidate(random.Random(seed), data, sessions, context=context)
            validate_candidate(data, sessions, candidate, context=context)
            soft_penalty(data, sessions, candidate, weights, context=context)
            if candidate.hard_violations == 0:
                break
    if improve_feasible:
        candidate = _improve_feasible(data, sessions, candidate, weights, context=context)
    status = "feasible" if candidate.hard_violations == 0 else "best_effort"
    return RunResult(status, candidate, 0, int((time.perf_counter() - started) * 1000), [], [])


def optimize(
    data: Dataset,
    population_size: int = 80,
    max_generations: int = 250,
    crossover_probability: float = 0.8,
    mutation_probability: float = 0.15,
    swap_probability: float = 0.35,
    tournament_size: int = 3,
    elite_count: int = 2,
    random_seed: int | None = None,
    soft_weights: dict[str, float] | None = None,
    no_improvement_generations: int = 25,
    target_soft_penalty: float | None = None,
    use_greedy_seed: bool = True,
    improve_feasible: bool = True,
) -> RunResult:
    started = time.perf_counter()
    if not data.time_slots or not data.rooms:
        return RunResult("failed", None, 0, 0, [], ["At least one time slot and room are required."])
    sessions = expand_sessions(data)
    context = ScheduleContext(data, sessions)
    rng = random.Random(random_seed)
    weights = soft_weights or {}
    greedy_seed = greedy_baseline(data, weights, improve_feasible=improve_feasible, context=context).candidate if use_greedy_seed else None
    random_count = population_size - 1 if greedy_seed is not None else population_size
    population = [_random_candidate(rng, data, sessions, context=context) for _ in range(max(1, random_count))]
    if greedy_seed is not None:
        population.append(_copy_candidate(greedy_seed))
    for item in population:
        validate_candidate(data, sessions, item, context=context)
        soft_penalty(data, sessions, item, weights, context=context)
    history: list[dict[str, float | int]] = []
    best = min(population, key=lambda item: item.score())
    if improve_feasible:
        best = _improve_feasible(data, sessions, best, weights, context=context)
    completed = 0
    stagnant_generations = 0
    for generation in range(max_generations + 1):
        population.sort(key=lambda item: item.score())
        previous_score = best.score()
        best = min(best, population[0], key=lambda item: item.score())
        if generation > 0:
            stagnant_generations = stagnant_generations + 1 if best.score() == previous_score else 0
        history.append({"generation": generation, "hard_violations": best.hard_violations, "soft_penalty": best.soft_penalty})
        completed = generation
        reached_target = (
            target_soft_penalty is not None
            and best.hard_violations == 0
            and best.soft_penalty <= target_soft_penalty
        )
        if reached_target or stagnant_generations >= no_improvement_generations:
            break
        next_population = [_copy_candidate(item) for item in population[:max(1, elite_count)]]
        while len(next_population) < len(population):
            left = _tournament(rng, population, tournament_size)
            right = _tournament(rng, population, tournament_size)
            child = (
                _crossover_candidate(rng, sessions, left, right)
                if rng.random() < crossover_probability
                else _copy_candidate(left)
            )
            validate_candidate(data, sessions, child, context=context)
            soft_penalty(data, sessions, child, weights, context=context)
            if rng.random() < mutation_probability:
                child = _mutate_candidate(rng, data, sessions, child, swap_probability, context=context)
            child = _repair_candidate(rng, data, sessions, child, weights, context=context)
            validate_candidate(data, sessions, child, context=context)
            soft_penalty(data, sessions, child, weights, context=context)
            next_population.append(child)
        population = next_population
    if improve_feasible:
        best = _improve_feasible(data, sessions, best, weights, context=context)
    validate_candidate(data, sessions, best, context=context)
    soft_penalty(data, sessions, best, weights, context=context)
    if history:
        history[-1] = {
            "generation": history[-1]["generation"],
            "hard_violations": best.hard_violations,
            "soft_penalty": best.soft_penalty,
        }
    status = "feasible" if best.hard_violations == 0 else "best_effort"
    return RunResult(status, best, completed, int((time.perf_counter() - started) * 1000), history, [] if status == "feasible" else ["No feasible schedule found within the generation limit."])


def randomized_baseline(
    data: Dataset,
    random_seed: int | None = None,
    soft_weights: dict[str, float] | None = None,
) -> RunResult:
    started = time.perf_counter()
    if not data.time_slots or not data.rooms:
        return RunResult("failed", None, 0, 0, [], ["At least one time slot and room are required."])
    sessions = expand_sessions(data)
    context = ScheduleContext(data, sessions)
    candidate = _random_candidate(random.Random(random_seed), data, sessions, context=context)
    validate_candidate(data, sessions, candidate, context=context)
    soft_penalty(data, sessions, candidate, soft_weights or {}, context=context)
    status = "feasible" if candidate.hard_violations == 0 else "best_effort"
    return RunResult(status, candidate, 0, int((time.perf_counter() - started) * 1000), [], [])
