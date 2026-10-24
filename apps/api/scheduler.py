from __future__ import annotations

import random
import time
from collections import Counter, defaultdict

from apps.api.domain import Assignment, Candidate, Dataset, RunResult, Session


def expand_sessions(data: Dataset) -> list[Session]:
    courses = {item.id: item for item in data.courses}
    result: list[Session] = []
    for requirement in data.teaching_requirements:
        course = courses.get(requirement.course_id)
        if course is None:
            continue
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


def validate_candidate(data: Dataset, sessions: list[Session], candidate: Candidate) -> Candidate:
    slots = _slot_ids(data)
    rooms = {room.id: room for room in data.rooms}
    faculty = {item.id: item for item in data.faculty}
    sections = {item.id: item for item in data.sections}
    session_map = {item.id: item for item in sessions}
    violations: list[dict[str, str]] = []
    seen = Counter(item.session_id for item in candidate.assignments)
    for session in sessions:
        if seen[session.id] != 1:
            code = "MISSING_SESSION" if seen[session.id] == 0 else "DUPLICATE_SESSION"
            violations.append({"code": code, "entity_id": session.requirement_id})
    slot_by_day_period = {(slot.day, slot.period): slot for slot in data.time_slots}
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
        if session.section_id not in sections or session.faculty_id not in faculty:
            violations.append({"code": "INVALID_REFERENCE", "entity_id": session.requirement_id})
            continue
        if room.capacity < sections[session.section_id].size:
            violations.append({"code": "ROOM_CAPACITY", "entity_id": session.requirement_id})
        if room.room_type != session.room_type:
            violations.append({"code": "ROOM_TYPE", "entity_id": session.requirement_id})
        occupied = []
        for offset in range(session.duration):
            occupied_slot = slot_by_day_period.get((slot.day, slot.period + offset))
            if occupied_slot is None:
                violations.append({"code": "BROKEN_CONSECUTIVE_BLOCK", "entity_id": session.requirement_id})
            else:
                occupied.append(occupied_slot.id)
        for occupied_id in occupied:
            if occupied_id in room.unavailable_slots:
                violations.append({"code": "ROOM_UNAVAILABLE", "entity_id": room.id})
            if occupied_id in faculty[session.faculty_id].unavailable_slots:
                violations.append({"code": "FACULTY_UNAVAILABLE", "entity_id": session.faculty_id})
            if occupied_id in sections[session.section_id].unavailable_slots:
                violations.append({"code": "SECTION_UNAVAILABLE", "entity_id": session.section_id})
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for assignment in candidate.assignments:
        session = session_map.get(assignment.session_id)
        if session and assignment.slot_id in slots:
            slot = slots[assignment.slot_id]
            for offset in range(session.duration):
                occupied = (slot.day, slot.period + offset)
                key = f"{occupied[0]}:{occupied[1]}"
                groups[("faculty", session.faculty_id)].append(key)
                groups[("section", session.section_id)].append(key)
                groups[("room", assignment.room_id)].append(key)
    for (kind, entity), values in groups.items():
        duplicates = [value for value, count in Counter(values).items() if count > 1]
        for value in duplicates:
            violations.append({"code": f"{kind.upper()}_OVERLAP", "entity_id": entity, "slot": value})
    candidate.violations = violations
    candidate.hard_violations = len(violations)
    return candidate


def soft_penalty(data: Dataset, sessions: list[Session], candidate: Candidate, weights: dict[str, float]) -> float:
    slots = _slot_ids(data)
    session_map = {item.id: item for item in sessions}
    preferences = {(item.id, slot) for item in data.faculty for slot in item.preferred_slots}
    penalty = 0.0
    by_section: dict[str, list[object]] = defaultdict(list)
    by_faculty_day: dict[tuple[str, str], int] = Counter()
    by_requirement_day: dict[tuple[str, str], int] = Counter()
    for assignment in candidate.assignments:
        session = session_map.get(assignment.session_id)
        slot = slots.get(assignment.slot_id)
        if not session or not slot:
            continue
        if preferences and (session.faculty_id, assignment.slot_id) not in preferences:
            penalty += weights.get("faculty_preference", 1)
        by_section[session.section_id].append(slot)
        by_faculty_day[(session.faculty_id, slot.day)] += 1
        by_requirement_day[(session.requirement_id, slot.day)] += 1
    for values in by_section.values():
        periods = sorted(item.period for item in values)
        penalty += max(0, (periods[-1] - periods[0] + 1) - len(periods)) * weights.get("section_gaps", 1) if periods else 0
    faculty_by_id = {item.id: item for item in data.faculty}
    for (faculty_id, _day), counts in by_faculty_day.items():
        limit = faculty_by_id[faculty_id].daily_load_limit or 3
        if counts > limit:
            penalty += (counts - limit) * weights.get("faculty_daily_load", 1)
    periods_by_faculty_day: dict[tuple[str, str], list[int]] = defaultdict(list)
    for assignment in candidate.assignments:
        session = session_map.get(assignment.session_id)
        slot = slots.get(assignment.slot_id)
        if session and slot:
            periods_by_faculty_day[(session.faculty_id, slot.day)].extend(
                slot.period + offset for offset in range(session.duration)
            )
    for periods in periods_by_faculty_day.values():
        consecutive = 1
        for previous, current in zip(sorted(set(periods)), sorted(set(periods))[1:]):
            consecutive = consecutive + 1 if current == previous + 1 else 1
            if consecutive > 3:
                penalty += weights.get("consecutive_periods", 1)
    for count in by_requirement_day.values():
        if count > 1:
            penalty += (count - 1) * weights.get("repeat_distribution", 1)
    candidate.soft_penalty = penalty
    return penalty


def _random_candidate(rng: random.Random, data: Dataset, sessions: list[Session]) -> Candidate:
    slots = [slot.id for slot in data.time_slots]
    rooms = [room.id for room in data.rooms]
    return Candidate([Assignment(session.id, rng.choice(slots), rng.choice(rooms)) for session in sessions])


def _tournament(rng: random.Random, population: list[Candidate], size: int) -> Candidate:
    return min(rng.sample(population, min(size, len(population))), key=lambda item: item.score())


def _repair_candidate(
    rng: random.Random,
    data: Dataset,
    sessions: list[Session],
    candidate: Candidate,
    attempts_per_assignment: int = 12,
) -> Candidate:
    """Bounded local repair that changes locations but never session identity/count."""
    validate_candidate(data, sessions, candidate)
    for index, assignment in enumerate(candidate.assignments):
        if candidate.hard_violations == 0:
            break
        best = candidate
        for _ in range(attempts_per_assignment):
            trial_assignments = [
                Assignment(item.session_id, item.slot_id, item.room_id)
                for item in candidate.assignments
            ]
            trial_assignments[index] = Assignment(
                assignment.session_id,
                rng.choice(data.time_slots).id,
                rng.choice(data.rooms).id,
            )
            trial = Candidate(trial_assignments)
            validate_candidate(data, sessions, trial)
            if trial.score() < best.score():
                best = trial
        candidate = best
    return candidate


def greedy_baseline(data: Dataset) -> RunResult:
    started = time.perf_counter()
    if not data.time_slots or not data.rooms:
        return RunResult("failed", None, 0, 0, [], ["At least one time slot and room are required."])
    sessions = expand_sessions(data)
    candidate = Candidate([])
    for session in sessions:
        best: Candidate | None = None
        for slot in data.time_slots:
            for room in data.rooms:
                trial = Candidate(candidate.assignments + [Assignment(session.id, slot.id, room.id)])
                validate_candidate(data, sessions, trial)
                soft_penalty(data, sessions, trial, {})
                if best is None or trial.score() < best.score():
                    best = trial
        if best is None:
            return RunResult("failed", None, 0, int((time.perf_counter() - started) * 1000), [], ["No candidate assignment could be constructed."])
        candidate = best
    status = "feasible" if candidate.hard_violations == 0 else "best_effort"
    return RunResult(status, candidate, 0, int((time.perf_counter() - started) * 1000), [], [])


def optimize(
    data: Dataset,
    population_size: int = 80,
    max_generations: int = 250,
    crossover_probability: float = 0.8,
    mutation_probability: float = 0.15,
    tournament_size: int = 3,
    elite_count: int = 2,
    random_seed: int | None = None,
    soft_weights: dict[str, float] | None = None,
) -> RunResult:
    started = time.perf_counter()
    if not data.time_slots or not data.rooms:
        return RunResult("failed", None, 0, 0, [], ["At least one time slot and room are required."])
    sessions = expand_sessions(data)
    rng = random.Random(random_seed)
    weights = soft_weights or {}
    population = [_random_candidate(rng, data, sessions) for _ in range(max(2, population_size))]
    for item in population:
        validate_candidate(data, sessions, item)
        soft_penalty(data, sessions, item, weights)
    history: list[dict[str, float | int]] = []
    best = min(population, key=lambda item: item.score())
    completed = 0
    for generation in range(max_generations + 1):
        population.sort(key=lambda item: item.score())
        best = min(best, population[0], key=lambda item: item.score())
        history.append({"generation": generation, "hard_violations": best.hard_violations, "soft_penalty": best.soft_penalty})
        completed = generation
        if best.hard_violations == 0:
            break
        next_population = [Candidate([Assignment(a.session_id, a.slot_id, a.room_id) for a in item.assignments]) for item in population[:max(1, elite_count)]]
        while len(next_population) < len(population):
            left = _tournament(rng, population, tournament_size)
            right = _tournament(rng, population, tournament_size)
            cut = rng.randrange(len(sessions) + 1)
            child_assignments = left.assignments[:cut] + right.assignments[cut:] if rng.random() < crossover_probability else [Assignment(a.session_id, a.slot_id, a.room_id) for a in left.assignments]
            if rng.random() < mutation_probability and child_assignments:
                index = rng.randrange(len(child_assignments))
                child_assignments[index] = Assignment(child_assignments[index].session_id, rng.choice(data.time_slots).id, rng.choice(data.rooms).id)
            child = Candidate(child_assignments)
            child = _repair_candidate(rng, data, sessions, child)
            validate_candidate(data, sessions, child)
            soft_penalty(data, sessions, child, weights)
            next_population.append(child)
        population = next_population
    validate_candidate(data, sessions, best)
    soft_penalty(data, sessions, best, weights)
    if history:
        history[-1] = {
            "generation": history[-1]["generation"],
            "hard_violations": best.hard_violations,
            "soft_penalty": best.soft_penalty,
        }
    status = "feasible" if best.hard_violations == 0 else "best_effort"
    return RunResult(status, best, completed, int((time.perf_counter() - started) * 1000), history, [] if status == "feasible" else ["No feasible schedule found within the generation limit."])


def randomized_baseline(data: Dataset, random_seed: int | None = None) -> RunResult:
    started = time.perf_counter()
    if not data.time_slots or not data.rooms:
        return RunResult("failed", None, 0, 0, [], ["At least one time slot and room are required."])
    sessions = expand_sessions(data)
    candidate = _random_candidate(random.Random(random_seed), data, sessions)
    validate_candidate(data, sessions, candidate)
    soft_penalty(data, sessions, candidate, {})
    status = "feasible" if candidate.hard_violations == 0 else "best_effort"
    return RunResult(status, candidate, 0, int((time.perf_counter() - started) * 1000), [], [])
