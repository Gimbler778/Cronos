from __future__ import annotations

import csv
import io
import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from apps.api.domain import Assignment, Candidate, Dataset, Faculty, Room, Section, Course, TimeSlot, TeachingRequirement
from apps.api.sample_data import sample_dataset
from apps.api.scheduler import expand_sessions, greedy_baseline, optimize, randomized_baseline
from apps.api.storage import Storage

router = APIRouter()
storage = Storage()


def _dataset() -> Dataset:
    return storage.load_dataset()


class OptimizationRequest(BaseModel):
    population_size: int = Field(default=80, ge=2, le=1000)
    max_generations: int = Field(default=250, ge=1, le=5000)
    crossover_probability: float = Field(default=0.8, ge=0, le=1)
    mutation_probability: float = Field(default=0.15, ge=0, le=1)
    swap_probability: float = Field(default=0.35, ge=0, le=1)
    tournament_size: int = Field(default=3, ge=2, le=20)
    elite_count: int = Field(default=2, ge=1, le=100)
    random_seed: int | None = None
    soft_weights: dict[str, float] = Field(default_factory=dict)
    no_improvement_generations: int = Field(default=25, ge=1, le=5000)
    target_soft_penalty: float | None = Field(default=None, ge=0)
    use_greedy_seed: bool = True
    improve_feasible: bool = True

    @field_validator("soft_weights")
    @classmethod
    def validate_soft_weights(cls, value: dict[str, float]) -> dict[str, float]:
        if any(not math.isfinite(weight) or weight < 0 for weight in value.values()):
            raise ValueError("soft weights must be finite and non-negative")
        return value


def _validate_references(value: Dataset) -> list[dict[str, str]]:
    ids = {
        "faculty": {item.id for item in value.faculty},
        "rooms": {item.id for item in value.rooms},
        "sections": {item.id for item in value.sections},
        "courses": {item.id for item in value.courses},
        "time_slots": {item.id for item in value.time_slots},
        "teaching_requirements": {item.id for item in value.teaching_requirements},
    }
    errors: list[dict[str, str]] = []
    for kind, items in ids.items():
        values = [item.id for item in getattr(value, kind)]
        if len(values) != len(set(values)):
            errors.append({"code": "DUPLICATE_ID", "message": f"{kind} IDs must be unique.", "entity_id": kind})
    for requirement in value.teaching_requirements:
        for kind, item_id in (("courses", requirement.course_id), ("sections", requirement.section_id), ("faculty", requirement.faculty_id)):
            if item_id not in ids[kind]:
                errors.append({"code": "MISSING_REFERENCE", "message": f"{kind[:-1]} '{item_id}' does not exist.", "entity_id": requirement.id})
    slot_ids = ids["time_slots"]
    for item in value.faculty + value.rooms + value.sections:
        for slot_id in item.unavailable_slots:
            if slot_id not in slot_ids:
                errors.append({"code": "INVALID_SLOT", "message": f"Slot '{slot_id}' does not exist.", "entity_id": item.id})
    for item in value.faculty:
        for slot_id in item.preferred_slots:
            if slot_id not in slot_ids:
                errors.append({"code": "INVALID_SLOT", "message": f"Slot '{slot_id}' does not exist.", "entity_id": item.id})
    return errors


def _validated_dataset(value: Dataset) -> Dataset:
    try:
        return Dataset.model_validate(value.model_dump(mode="json"))
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_INPUT", "message": "Dataset constraints are invalid.", "details": [{"message": str(error)}]},
        ) from error


def _record(run_id: str) -> dict:
    record = storage.load_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Optimization run not found."})
    if "candidate" not in record:
        record["candidate"] = storage.load_candidate(run_id)
    elif isinstance(record["candidate"], dict):
        value = record["candidate"]
        record["candidate"] = Candidate(
            assignments=[Assignment(**item) for item in value["assignments"]],
            hard_violations=value["hard_violations"],
            soft_penalty=value["soft_penalty"],
            violations=value["violations"],
        )
    return record


COLLECTIONS: dict[str, type[BaseModel]] = {
    "faculty": Faculty,
    "rooms": Room,
    "sections": Section,
    "courses": Course,
    "time-slots": TimeSlot,
    "teaching-requirements": TeachingRequirement,
}


def _collection_name(path_name: str) -> str:
    return path_name.replace("-", "_")


@router.get("/health")
def api_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/data")
def get_data() -> Dataset:
    return _dataset()


@router.get("/data/status")
def get_data_status() -> dict[str, bool]:
    return {"initialized": storage.dataset_exists()}


@router.put("/data")
def replace_data(value: Dataset) -> dict:
    errors = _validate_references(value)
    if errors:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "One or more references are invalid.", "details": errors})
    storage.save_dataset(value)
    return {"saved": True, "counts": {key: len(getattr(value, key)) for key in ("faculty", "rooms", "sections", "courses", "time_slots", "teaching_requirements")}}


@router.delete("/data")
def clear_data() -> dict[str, bool]:
    storage.replace_dataset(Dataset())
    return {"cleared": True}


def _collection(name: str, model: type[BaseModel], value: BaseModel | None = None) -> list | BaseModel:
    dataset = _dataset()
    items = list(getattr(dataset, name))
    if value is None:
        return items
    if any(item.id == value.id for item in items):
        raise HTTPException(status_code=409, detail={"code": "DUPLICATE_ID", "message": f"{name} ID already exists."})
    items.append(value)
    updated = _validated_dataset(dataset.model_copy(update={name: items}))
    errors = _validate_references(updated)
    if errors:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "Entity references are invalid.", "details": errors})
    storage.save_dataset(updated)
    return value


@router.get("/faculty")
def list_faculty() -> list[Faculty]:
    return _collection("faculty", Faculty)


@router.post("/faculty", status_code=201)
def add_faculty(value: Faculty) -> Faculty:
    return _collection("faculty", Faculty, value)


@router.get("/rooms")
def list_rooms() -> list[Room]:
    return _collection("rooms", Room)


@router.post("/rooms", status_code=201)
def add_room(value: Room) -> Room:
    return _collection("rooms", Room, value)


@router.get("/sections")
def list_sections() -> list[Section]:
    return _collection("sections", Section)


@router.post("/sections", status_code=201)
def add_section(value: Section) -> Section:
    return _collection("sections", Section, value)


@router.get("/courses")
def list_courses() -> list[Course]:
    return _collection("courses", Course)


@router.post("/courses", status_code=201)
def add_course(value: Course) -> Course:
    return _collection("courses", Course, value)


@router.get("/time-slots")
def list_time_slots() -> list[TimeSlot]:
    return _collection("time_slots", TimeSlot)


@router.post("/time-slots", status_code=201)
def add_time_slot(value: TimeSlot) -> TimeSlot:
    return _collection("time_slots", TimeSlot, value)


@router.get("/teaching-requirements")
def list_teaching_requirements() -> list[TeachingRequirement]:
    return _collection("teaching_requirements", TeachingRequirement)


@router.post("/teaching-requirements", status_code=201)
def add_teaching_requirement(value: TeachingRequirement) -> TeachingRequirement:
    return _collection("teaching_requirements", TeachingRequirement, value)


@router.put("/{collection}/{item_id}")
def update_collection_item(collection: str, item_id: str, value: dict) -> BaseModel:
    dataset = _dataset()
    model = COLLECTIONS.get(collection)
    if model is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Collection not found."})
    name = _collection_name(collection)
    items = list(getattr(dataset, name))
    if not any(item.id == item_id for item in items):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Entity not found."})
    if value.get("id", item_id) != item_id:
        raise HTTPException(status_code=422, detail={"code": "ID_IMMUTABLE", "message": "Entity IDs cannot be changed."})
    replacement = model.model_validate({**next(item.model_dump(mode="json") for item in items if item.id == item_id), **value})
    updated = _validated_dataset(dataset.model_copy(update={name: [replacement if item.id == item_id else item for item in items]}))
    errors = _validate_references(updated)
    if errors:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "Entity references are invalid.", "details": errors})
    storage.save_dataset(updated)
    return replacement


@router.delete("/{collection}/{item_id}", status_code=204, response_class=Response)
def delete_collection_item(collection: str, item_id: str) -> Response:
    dataset = _dataset()
    model = COLLECTIONS.get(collection)
    if model is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Collection not found."})
    name = _collection_name(collection)
    items = list(getattr(dataset, name))
    if not any(item.id == item_id for item in items):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Entity not found."})
    references = {
        "courses": ("course_id",),
        "sections": ("section_id",),
        "faculty": ("faculty_id",),
    }
    for field in references.get(name, ()):
        if any(getattr(requirement, field) == item_id for requirement in dataset.teaching_requirements):
            raise HTTPException(status_code=409, detail={"code": "REFERENCED_ENTITY", "message": "Entity is referenced by a teaching requirement."})
    updated = _validated_dataset(dataset.model_copy(update={name: [item for item in items if item.id != item_id]}))
    storage.save_dataset(updated)
    return Response(status_code=204)


@router.post("/validate")
def validate_data() -> dict:
    dataset = _dataset()
    errors = _validate_references(dataset)
    return {"valid": not errors, "errors": errors, "warnings": []}


@router.post("/optimization-runs")
def create_run(request: OptimizationRequest) -> dict:
    dataset = _dataset()
    errors = _validate_references(dataset)
    if errors:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "Validate data before running optimization.", "details": errors})
    run_id = str(uuid.uuid4())
    result = optimize(dataset, **request.model_dump())
    record = {
        "id": run_id,
        "status": result.status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": request.random_seed,
        "parameters": request.model_dump(),
        "hard_violations": result.candidate.hard_violations if result.candidate else None,
        "soft_penalty": result.candidate.soft_penalty if result.candidate else None,
        "violations": result.candidate.violations if result.candidate else [],
        "runtime_ms": result.runtime_ms,
        "generations": result.generations,
        "diagnostics": result.diagnostics,
        "history": result.history,
        "dataset": dataset.model_dump(mode="json"),
        "candidate": {
            "assignments": [item.__dict__ for item in result.candidate.assignments] if result.candidate else [],
            "hard_violations": result.candidate.hard_violations if result.candidate else 0,
            "soft_penalty": result.candidate.soft_penalty if result.candidate else 0,
            "violations": result.candidate.violations if result.candidate else [],
        },
    }
    storage.save_run(run_id, record)
    return {key: value for key, value in record.items() if key != "candidate"}


@router.get("/optimization-runs")
def list_runs() -> list[dict]:
    records = storage.list_runs()
    return [{key: value for key, value in record.items() if key not in ("candidate", "history")} for record in records]


@router.post("/baseline")
def create_baseline(request: OptimizationRequest) -> dict:
    dataset = _dataset()
    errors = _validate_references(dataset)
    if errors:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "Validate data before running baseline.", "details": errors})
    result = randomized_baseline(dataset, request.random_seed, request.soft_weights)
    return {
        "status": result.status,
        "hard_violations": result.candidate.hard_violations if result.candidate else None,
        "soft_penalty": result.candidate.soft_penalty if result.candidate else None,
        "runtime_ms": result.runtime_ms,
    }


@router.post("/baseline/greedy")
def create_greedy_baseline(request: OptimizationRequest | None = None) -> dict:
    dataset = _dataset()
    errors = _validate_references(dataset)
    if errors:
        raise HTTPException(status_code=422, detail={"code": "INVALID_INPUT", "message": "Validate data before running baseline.", "details": errors})
    result = greedy_baseline(dataset, request.soft_weights if request else None)
    return {
        "status": result.status,
        "hard_violations": result.candidate.hard_violations if result.candidate else None,
        "soft_penalty": result.candidate.soft_penalty if result.candidate else None,
        "runtime_ms": result.runtime_ms,
    }


@router.get("/optimization-runs/{run_id}")
def get_run(run_id: str) -> dict:
    record = _record(run_id)
    return {key: value for key, value in record.items() if key not in ("candidate", "history")}


@router.get("/optimization-runs/{run_id}/metrics")
def get_metrics(run_id: str) -> dict:
    record = _record(run_id)
    return {"run_id": run_id, "history": record["history"]}


@router.get("/optimization-runs/{run_id}/schedule")
def get_schedule(run_id: str) -> dict:
    record = _record(run_id)
    candidate = record["candidate"]
    run_dataset = Dataset.model_validate(record["dataset"])
    sessions = {item.id: item for item in expand_sessions(run_dataset)}
    slots = {item.id: item for item in run_dataset.time_slots}
    rooms = {item.id: item for item in run_dataset.rooms}
    courses = {item.id: item for item in run_dataset.courses}
    sections = {item.id: item for item in run_dataset.sections}
    faculty = {item.id: item for item in run_dataset.faculty}
    rows = []
    for item in candidate.assignments:
        session = sessions.get(item.session_id)
        slot = slots.get(item.slot_id)
        room = rooms.get(item.room_id)
        course = courses.get(session.course_id) if session else None
        section = sections.get(session.section_id) if session else None
        person = faculty.get(session.faculty_id) if session else None
        if not (session and slot and room and course and section and person):
            continue
        rows.append(
            {
                **item.__dict__,
                "course_id": session.course_id,
                "section_id": session.section_id,
                "faculty_id": session.faculty_id,
                "duration": session.duration,
                "consecutive_required": session.consecutive_required,
                "slot": slot.model_dump(mode="json"),
                "room": room.model_dump(mode="json"),
                "course": course.model_dump(mode="json"),
                "section": section.model_dump(mode="json"),
                "faculty": person.model_dump(mode="json"),
            }
        )
    return {"run_id": run_id, "status": record["status"], "sessions": rows, "violations": candidate.violations}


@router.get("/optimization-runs/{run_id}/analytics")
def get_analytics(run_id: str) -> dict:
    record = _record(run_id)
    history = record.get("history", [])
    candidate = record.get("candidate")
    by_slot: dict[str, int] = {}
    by_room: dict[str, int] = {}
    by_section: dict[str, int] = {}
    if candidate:
        run_dataset = Dataset.model_validate(record["dataset"])
        sessions = {item.id: item for item in expand_sessions(run_dataset)}
        for assignment in candidate.assignments:
            by_slot[assignment.slot_id] = by_slot.get(assignment.slot_id, 0) + 1
            by_room[assignment.room_id] = by_room.get(assignment.room_id, 0) + 1
            session = sessions.get(assignment.session_id)
            if session:
                by_section[session.section_id] = by_section.get(session.section_id, 0) + 1
    return {"run_id": run_id, "history": history, "sessions_by_slot": by_slot, "sessions_by_room": by_room, "sessions_by_section": by_section}


def _export_matches(row: dict[str, object], filters: dict[str, str]) -> bool:
    if filters["day"] and row["day"] != filters["day"]:
        return False
    for key, labels in (
        ("room", ("room_id", "room_name")),
        ("section", ("section_id", "section_name")),
        ("faculty", ("faculty_id", "faculty_name")),
    ):
        if filters[key] and filters[key] not in (str(row[label]) for label in labels):
            return False
    if filters["q"]:
        haystack = " ".join(str(value or "") for value in row.values()).lower()
        if filters["q"].lower() not in haystack:
            return False
    return True


@router.get("/optimization-runs/{run_id}/export.csv")
def export_csv(
    run_id: str,
    q: str | None = None,
    day: str | None = None,
    room: str | None = None,
    section: str | None = None,
    faculty: str | None = None,
) -> StreamingResponse:
    record = _record(run_id)
    run_dataset = Dataset.model_validate(record["dataset"])
    sessions = {item.id: item for item in expand_sessions(run_dataset)}
    slots = {item.id: item for item in run_dataset.time_slots}
    rooms = {item.id: item for item in run_dataset.rooms}
    courses = {item.id: item for item in run_dataset.courses}
    sections = {item.id: item for item in run_dataset.sections}
    faculty_members = {item.id: item for item in run_dataset.faculty}
    filters = {"q": q or "", "day": day or "", "room": room or "", "section": section or "", "faculty": faculty or ""}
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "session_id",
            "day",
            "period",
            "period_label",
            "start_time",
            "end_time",
            "course_id",
            "course_code",
            "course_name",
            "section_id",
            "section_name",
            "faculty_id",
            "faculty_name",
            "room_id",
            "room_name",
            "room_type",
        ]
    )
    for assignment in record["candidate"].assignments:
        session = sessions.get(assignment.session_id)
        slot = slots.get(assignment.slot_id)
        room_item = rooms.get(assignment.room_id)
        course = courses.get(session.course_id) if session else None
        section_item = sections.get(session.section_id) if session else None
        person = faculty_members.get(session.faculty_id) if session else None
        if not (session and slot and room_item and course and section_item and person):
            continue
        row = {
            "session_id": assignment.session_id,
            "day": slot.day,
            "period": slot.period,
            "period_label": f"P{slot.period}",
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "course_id": course.id,
            "course_code": course.code,
            "course_name": course.name,
            "section_id": section_item.id,
            "section_name": section_item.name,
            "faculty_id": person.id,
            "faculty_name": person.name,
            "room_id": room_item.id,
            "room_name": room_item.name,
            "room_type": room_item.room_type,
        }
        if _export_matches(row, filters):
            writer.writerow([row[key] for key in row])
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="cronos-{run_id}.csv"'})


@router.post("/sample-data")
def load_sample_data() -> dict:
    dataset = sample_dataset()
    storage.replace_dataset(dataset)
    return {"loaded": True}
