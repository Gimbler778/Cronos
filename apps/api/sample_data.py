from apps.api.domain import Course, Dataset, Faculty, Room, Section, TeachingRequirement, TimeSlot


def sample_dataset() -> Dataset:
    return Dataset(
        faculty=[
            Faculty(id="f1", name="Dr. Ada Lovelace", department="CS", preferred_slots={"mon-1", "wed-1"}, daily_load_limit=3),
            Faculty(id="f2", name="Dr. Grace Hopper", department="CS", preferred_slots={"tue-1", "thu-1"}, daily_load_limit=3),
            Faculty(id="f3", name="Dr. Alan Turing", department="Mathematics", preferred_slots={"wed-2", "fri-1"}, daily_load_limit=3),
        ],
        rooms=[
            Room(id="r1", name="Computer Lab 1", capacity=40, room_type="lab"),
            Room(id="r2", name="Computer Lab 2", capacity=35, room_type="lab"),
            Room(id="r3", name="Lecture Hall 1", capacity=80, room_type="lecture"),
            Room(id="r4", name="Lecture Room 2", capacity=50, room_type="lecture"),
        ],
        sections=[
            Section(id="s1", name="BSc CS A", size=30, department="CS", semester="1"),
            Section(id="s2", name="BSc CS B", size=25, department="CS", semester="1"),
            Section(id="s3", name="BSc Mathematics A", size=35, department="Mathematics", semester="1"),
        ],
        courses=[
            Course(id="c1", code="CS101", name="Programming", required_room_type="lab", duration=1, sessions_per_week=3),
            Course(id="c2", code="CS201", name="Data Structures", required_room_type="lecture", duration=1, sessions_per_week=2),
            Course(id="c3", code="CS202", name="Database Laboratory", required_room_type="lab", duration=1, sessions_per_week=2),
            Course(id="c4", code="MATH101", name="Discrete Mathematics", required_room_type="lecture", duration=1, sessions_per_week=2),
        ],
        time_slots=[
            TimeSlot(id="mon-1", day="Monday", period=1, start_time="09:00", end_time="10:00"),
            TimeSlot(id="mon-2", day="Monday", period=2, start_time="10:00", end_time="11:00"),
            TimeSlot(id="mon-3", day="Monday", period=3, start_time="11:00", end_time="12:00"),
            TimeSlot(id="tue-1", day="Tuesday", period=1, start_time="09:00", end_time="10:00"),
            TimeSlot(id="tue-2", day="Tuesday", period=2, start_time="10:00", end_time="11:00"),
            TimeSlot(id="tue-3", day="Tuesday", period=3, start_time="11:00", end_time="12:00"),
            TimeSlot(id="wed-1", day="Wednesday", period=1, start_time="09:00", end_time="10:00"),
            TimeSlot(id="wed-2", day="Wednesday", period=2, start_time="10:00", end_time="11:00"),
            TimeSlot(id="wed-3", day="Wednesday", period=3, start_time="11:00", end_time="12:00"),
            TimeSlot(id="thu-1", day="Thursday", period=1, start_time="09:00", end_time="10:00"),
            TimeSlot(id="thu-2", day="Thursday", period=2, start_time="10:00", end_time="11:00"),
            TimeSlot(id="thu-3", day="Thursday", period=3, start_time="11:00", end_time="12:00"),
            TimeSlot(id="fri-1", day="Friday", period=1, start_time="09:00", end_time="10:00"),
            TimeSlot(id="fri-2", day="Friday", period=2, start_time="10:00", end_time="11:00"),
            TimeSlot(id="fri-3", day="Friday", period=3, start_time="11:00", end_time="12:00"),
        ],
        teaching_requirements=[
            TeachingRequirement(id="tr1", course_id="c1", section_id="s1", faculty_id="f1", required_sessions=3),
            TeachingRequirement(id="tr2", course_id="c2", section_id="s1", faculty_id="f2", required_sessions=2),
            TeachingRequirement(id="tr3", course_id="c3", section_id="s2", faculty_id="f3", required_sessions=2),
            TeachingRequirement(id="tr4", course_id="c4", section_id="s3", faculty_id="f1", required_sessions=2),
            TeachingRequirement(id="tr5", course_id="c2", section_id="s2", faculty_id="f2", required_sessions=2),
            TeachingRequirement(id="tr6", course_id="c1", section_id="s3", faculty_id="f3", required_sessions=2),
        ],
    )
