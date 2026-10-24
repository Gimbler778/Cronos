from apps.api.domain import Assignment, Candidate
from apps.api.scheduler import expand_sessions, validate_candidate
from test_scheduler import sample


def test_capacity_and_room_type_are_hard_violations():
    data = sample()
    data.rooms[0].capacity = 5
    data.rooms[0].room_type = "lecture"
    sessions = expand_sessions(data)
    candidate = Candidate([Assignment(sessions[0].id, "a", "r1")])
    violations = validate_candidate(data, sessions, candidate).violations
    assert {item["code"] for item in violations} >= {"ROOM_CAPACITY", "ROOM_TYPE"}


def test_unavailability_and_overlap_are_detected():
    data = sample()
    data.faculty[0].unavailable_slots = {"a"}
    data.teaching_requirements[0].required_sessions = 2
    sessions = expand_sessions(data)
    candidate = Candidate([Assignment(session.id, "a", "r1") for session in sessions])
    codes = {item["code"] for item in validate_candidate(data, sessions, candidate).violations}
    assert {"FACULTY_UNAVAILABLE", "FACULTY_OVERLAP", "SECTION_OVERLAP", "ROOM_OVERLAP"} <= codes


def test_duration_requires_a_consecutive_slot_block():
    data = sample()
    data.teaching_requirements[0].duration = 2
    sessions = expand_sessions(data)
    candidate = Candidate([Assignment(sessions[0].id, "a", "r1")])
    codes = {item["code"] for item in validate_candidate(data, sessions, candidate).violations}
    assert "BROKEN_CONSECUTIVE_BLOCK" in codes


def test_time_slot_positions_are_unique():
    data = sample()
    data.time_slots[1].day = "Mon"
    data.time_slots[1].period = 1
    try:
        type(data).model_validate(data.model_dump())
    except ValueError as error:
        assert "day and period" in str(error)
    else:
        raise AssertionError("duplicate time-slot positions should be rejected")
