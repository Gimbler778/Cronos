from __future__ import annotations

import json
import statistics
from pathlib import Path

from apps.api.domain import Dataset
from apps.api.sample_data import sample_dataset
from apps.api.scheduler import greedy_baseline, optimize


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
