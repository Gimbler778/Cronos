from apps.api.domain import Dataset, Faculty, Room, Section, Course, TimeSlot, TeachingRequirement
from apps.api.scheduler import expand_sessions, optimize, soft_penalty, validate_candidate


def sample() -> Dataset:
    return Dataset(
        faculty=[Faculty(id="f1", name="Faculty", department="CS")],
        rooms=[Room(id="r1", name="Room", capacity=30, room_type="lab")],
        sections=[Section(id="s1", name="Section", size=20, department="CS", semester="1")],
        courses=[Course(id="c1", code="CS1", name="Course", required_room_type="lab")],
        time_slots=[TimeSlot(id="a", day="Mon", period=1, start_time="09:00", end_time="10:00"), TimeSlot(id="b", day="Tue", period=1, start_time="09:00", end_time="10:00")],
        teaching_requirements=[TeachingRequirement(id="tr1", course_id="c1", section_id="s1", faculty_id="f1", required_sessions=1)],
    )


def test_seeded_run_is_reproducible():
    data = sample()
    first = optimize(data, population_size=10, max_generations=20, random_seed=42)
    second = optimize(data, population_size=10, max_generations=20, random_seed=42)
    assert first.status == second.status
    assert first.candidate.assignments == second.candidate.assignments


def test_valid_candidate_has_no_hard_violations():
    data = sample()
    sessions = expand_sessions(data)
    candidate = optimize(data, population_size=10, max_generations=20, random_seed=1).candidate
    assert validate_candidate(data, sessions, candidate).hard_violations == 0


def test_required_sessions_are_expanded():
    data = sample()
    data.courses[0].sessions_per_week = 99
    data.teaching_requirements[0].required_sessions = 3
    assert len(expand_sessions(data)) == 3


def test_requirement_inherits_course_duration_when_omitted():
    data = sample()
    data.courses[0].duration = 2
    session = expand_sessions(data)[0]
    assert session.duration == 2


def test_non_consecutive_course_does_not_require_a_complete_block():
    data = sample()
    data.courses[0].duration = 2
    data.courses[0].consecutive_slots_required = False
    sessions = expand_sessions(data)
    candidate = optimize(data, population_size=4, max_generations=1, random_seed=1).candidate
    assert candidate is not None
    assert validate_candidate(data, sessions, candidate).hard_violations == 0


def test_faculty_without_preferences_are_not_penalized():
    data = sample()
    data.faculty.append(Faculty(id="f2", name="Other Faculty", department="CS", preferred_slots={"a"}))
    sessions = expand_sessions(data)
    candidate = optimize(data, population_size=4, max_generations=1, random_seed=1).candidate
    assert candidate is not None
    assert soft_penalty(data, sessions, candidate, {}) == 0


def test_ga_preserves_required_session_identity_after_operators():
    data = sample()
    data.teaching_requirements[0].required_sessions = 3
    result = optimize(data, population_size=8, max_generations=8, random_seed=7)
    assert result.candidate is not None
    assert sorted(item.session_id for item in result.candidate.assignments) == ["tr1:1", "tr1:2", "tr1:3"]


def test_optimizer_retains_feasible_seed_across_repeated_runs():
    data = sample()
    for seed in (1, 7, 42, 99, 123):
        result = optimize(data, population_size=10, max_generations=20, random_seed=seed)
        assert result.status == "feasible"
        assert result.candidate is not None
        assert result.candidate.hard_violations == 0


def test_unseeded_optimizer_can_construct_a_feasible_schedule():
    result = optimize(sample(), population_size=6, max_generations=4, random_seed=42, use_greedy_seed=False)
    assert result.status == "feasible"
    assert result.candidate is not None
    assert result.candidate.hard_violations == 0


def test_optimizer_does_not_stop_at_first_feasible_generation():
    result = optimize(sample(), population_size=10, max_generations=3, random_seed=42)
    assert result.status == "feasible"
    assert result.generations == 3
    assert len(result.history) == 4


def test_optimizer_honors_no_improvement_budget():
    result = optimize(sample(), population_size=10, max_generations=20, random_seed=42, no_improvement_generations=1)
    assert result.status == "feasible"
    assert result.generations < 20
