from __future__ import annotations

import json
import statistics
from pathlib import Path

from apps.api.domain import Course, Dataset, Faculty, Room, Section, TeachingRequirement, TimeSlot
from apps.api.scheduler import greedy_baseline, optimize


def sample_dataset() -> Dataset:
    return Dataset(
        faculty=[Faculty(id="f1", name="Dr. Ada Lovelace", department="CS", preferred_slots={"mon-1"})],
        rooms=[Room(id="r1", name="Lab 1", capacity=40, room_type="lab"), Room(id="r2", name="Room 2", capacity=40, room_type="lecture")],
        sections=[Section(id="s1", name="BSc CS A", size=30, department="CS", semester="1")],
        courses=[Course(id="c1", code="CS101", name="Programming", required_room_type="lab", sessions_per_week=2)],
        time_slots=[
            TimeSlot(id="mon-1", day="Monday", period=1, start_time="09:00", end_time="10:00"),
            TimeSlot(id="mon-2", day="Monday", period=2, start_time="10:00", end_time="11:00"),
            TimeSlot(id="tue-1", day="Tuesday", period=1, start_time="09:00", end_time="10:00"),
        ],
        teaching_requirements=[TeachingRequirement(id="tr1", course_id="c1", section_id="s1", faculty_id="f1", required_sessions=2)],
    )


def evaluate(seeds: list[int]) -> dict:
    ga = [optimize(sample_dataset(), population_size=40, max_generations=100, random_seed=seed) for seed in seeds]
    baseline = [greedy_baseline(sample_dataset()) for _ in seeds]

    def summarize(results: list) -> dict:
        hard = [result.candidate.hard_violations if result.candidate else None for result in results]
        soft = [result.candidate.soft_penalty if result.candidate else None for result in results]
        runtime = [result.runtime_ms for result in results]
        return {
            "seeds": seeds,
            "hard_violations": hard,
            "soft_penalty": soft,
            "runtime_ms": runtime,
            "mean_hard_violations": statistics.mean(hard),
            "mean_soft_penalty": statistics.mean(soft),
            "mean_runtime_ms": statistics.mean(runtime),
            "feasible_runs": sum(result.status == "feasible" for result in results),
            "total_runs": len(results),
        }

    return {"dataset_counts": {key: len(getattr(sample_dataset(), key)) for key in ("faculty", "rooms", "sections", "courses", "time_slots", "teaching_requirements")}, "parameters": {"population_size": 40, "max_generations": 100}, "baseline": summarize(baseline), "ga": summarize(ga)}


if __name__ == "__main__":
    report = evaluate([1, 7, 42, 99, 123])
    output = Path("apps/evaluation-results.json")
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
