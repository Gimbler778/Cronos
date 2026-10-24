from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TimeSlot(BaseModel):
    id: str
    day: str
    period: int = Field(ge=1)
    start_time: str
    end_time: str


class Faculty(BaseModel):
    id: str
    name: str
    department: str
    unavailable_slots: set[str] = set()
    preferred_slots: set[str] = set()
    daily_load_limit: int | None = Field(default=None, ge=1)


class Room(BaseModel):
    id: str
    name: str
    capacity: int = Field(gt=0)
    room_type: str
    unavailable_slots: set[str] = set()


class Section(BaseModel):
    id: str
    name: str
    size: int = Field(gt=0)
    department: str
    semester: str
    unavailable_slots: set[str] = set()


class Course(BaseModel):
    id: str
    code: str
    name: str
    required_room_type: str
    duration: int = Field(default=1, ge=1)
    sessions_per_week: int = Field(default=1, ge=1)
    consecutive_slots_required: bool = False


class TeachingRequirement(BaseModel):
    id: str
    course_id: str
    section_id: str
    faculty_id: str
    required_sessions: int = Field(ge=1)
    duration: int = Field(default=1, ge=1)
    room_type: str | None = None


class Dataset(BaseModel):
    faculty: list[Faculty] = Field(default_factory=list)
    rooms: list[Room] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    courses: list[Course] = Field(default_factory=list)
    time_slots: list[TimeSlot] = Field(default_factory=list)
    teaching_requirements: list[TeachingRequirement] = Field(default_factory=list)

    @field_validator("time_slots")
    @classmethod
    def unique_slot_ids(cls, value: list[TimeSlot]) -> list[TimeSlot]:
        ids = [slot.id for slot in value]
        if len(ids) != len(set(ids)):
            raise ValueError("time slot IDs must be unique")
        positions = [(slot.day, slot.period) for slot in value]
        if len(positions) != len(set(positions)):
            raise ValueError("time slot day and period combinations must be unique")
        return value


@dataclass(frozen=True)
class Session:
    id: str
    requirement_id: str
    occurrence: int
    course_id: str
    section_id: str
    faculty_id: str
    duration: int
    room_type: str
    consecutive_required: bool = False


@dataclass
class Assignment:
    session_id: str
    slot_id: str
    room_id: str


@dataclass
class Candidate:
    assignments: list[Assignment]
    hard_violations: int = 0
    soft_penalty: float = 0
    violations: list[dict[str, str]] = field(default_factory=list)

    def score(self) -> tuple[int, float]:
        return self.hard_violations, self.soft_penalty


@dataclass
class RunResult:
    status: Literal["feasible", "best_effort", "failed"]
    candidate: Candidate | None
    generations: int
    runtime_ms: int
    history: list[dict[str, float | int]]
    diagnostics: list[str]
