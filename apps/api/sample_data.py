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


def benchmark_dataset() -> Dataset:
    """A constrained benchmark kept separate from the small UI demo dataset."""
    days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    time_slots = [
        TimeSlot(
            id=f"{day[:3].lower()}-{period}",
            day=day,
            period=period,
            start_time=f"{8 + period:02d}:00",
            end_time=f"{9 + period:02d}:00",
        )
        for day in days
        for period in range(1, 5)
    ]
    return Dataset(
        faculty=[
            Faculty(id="bf1", name="Benchmark Ada", department="CS", preferred_slots={"mon-1", "wed-1"}, daily_load_limit=4, unavailable_slots={"fri-4"}),
            Faculty(id="bf2", name="Benchmark Grace", department="CS", preferred_slots={"tue-1", "thu-1"}, daily_load_limit=4, unavailable_slots={"mon-4"}),
            Faculty(id="bf3", name="Benchmark Alan", department="Math", preferred_slots={"wed-2", "fri-1"}, daily_load_limit=4, unavailable_slots={"tue-4"}),
            Faculty(id="bf4", name="Benchmark Katherine", department="Physics", preferred_slots={"mon-2", "thu-2"}, daily_load_limit=4, unavailable_slots={"wed-4"}),
            Faculty(id="bf5", name="Benchmark Tim", department="CS", preferred_slots={"tue-2", "fri-2"}, daily_load_limit=4, unavailable_slots={"thu-4"}),
        ],
        rooms=[
            Room(id="br1", name="Benchmark Lab 1", capacity=35, room_type="lab", unavailable_slots={"mon-4", "wed-4"}),
            Room(id="br2", name="Benchmark Lab 2", capacity=45, room_type="lab", unavailable_slots={"tue-4", "thu-4"}),
            Room(id="br3", name="Benchmark Lecture 1", capacity=90, room_type="lecture", unavailable_slots={"fri-4"}),
            Room(id="br4", name="Benchmark Lecture 2", capacity=55, room_type="lecture", unavailable_slots={"mon-4", "wed-4"}),
        ],
        sections=[
            Section(id="bs1", name="Benchmark CS A", size=32, department="CS", semester="1", unavailable_slots={"mon-4"}),
            Section(id="bs2", name="Benchmark CS B", size=28, department="CS", semester="1", unavailable_slots={"tue-4"}),
            Section(id="bs3", name="Benchmark CS C", size=40, department="CS", semester="2", unavailable_slots={"wed-4"}),
            Section(id="bs4", name="Benchmark Math", size=38, department="Math", semester="1", unavailable_slots={"thu-4"}),
            Section(id="bs5", name="Benchmark Physics", size=45, department="Physics", semester="1", unavailable_slots={"fri-4"}),
        ],
        courses=[
            Course(id="bc1", code="B-CS101", name="Benchmark Programming", required_room_type="lab", duration=1),
            Course(id="bc2", code="B-CS201", name="Benchmark Algorithms", required_room_type="lecture", duration=1),
            Course(id="bc3", code="B-CS202", name="Benchmark Database Lab", required_room_type="lab", duration=2, consecutive_slots_required=True),
            Course(id="bc4", code="B-MATH101", name="Benchmark Discrete Math", required_room_type="lecture", duration=1),
            Course(id="bc5", code="B-PHY101", name="Benchmark Physics Lab", required_room_type="lab", duration=2, consecutive_slots_required=True),
            Course(id="bc6", code="B-CS301", name="Benchmark Networks", required_room_type="lecture", duration=1),
        ],
        time_slots=time_slots,
        teaching_requirements=[
            TeachingRequirement(id="btr1", course_id="bc1", section_id="bs1", faculty_id="bf1", required_sessions=3),
            TeachingRequirement(id="btr2", course_id="bc2", section_id="bs1", faculty_id="bf2", required_sessions=2),
            TeachingRequirement(id="btr3", course_id="bc3", section_id="bs1", faculty_id="bf5", required_sessions=2),
            TeachingRequirement(id="btr4", course_id="bc1", section_id="bs2", faculty_id="bf1", required_sessions=3),
            TeachingRequirement(id="btr5", course_id="bc2", section_id="bs2", faculty_id="bf2", required_sessions=2),
            TeachingRequirement(id="btr6", course_id="bc6", section_id="bs2", faculty_id="bf5", required_sessions=2),
            TeachingRequirement(id="btr7", course_id="bc3", section_id="bs3", faculty_id="bf5", required_sessions=2),
            TeachingRequirement(id="btr8", course_id="bc6", section_id="bs3", faculty_id="bf2", required_sessions=2),
            TeachingRequirement(id="btr9", course_id="bc4", section_id="bs4", faculty_id="bf3", required_sessions=3),
            TeachingRequirement(id="btr10", course_id="bc5", section_id="bs4", faculty_id="bf4", required_sessions=2),
            TeachingRequirement(id="btr11", course_id="bc4", section_id="bs5", faculty_id="bf3", required_sessions=3),
            TeachingRequirement(id="btr12", course_id="bc5", section_id="bs5", faculty_id="bf4", required_sessions=2),
        ],
    )
