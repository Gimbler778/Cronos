from __future__ import annotations

import json
import statistics
from pathlib import Path

from apps.api.domain import Dataset
from apps.api.sample_data import benchmark_dataset, sample_dataset
from apps.api.scheduler import greedy_baseline, optimize


def _summarize(results: list, seeds: list[int]) -> dict:
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

def evaluate(seeds: list[int]) -> dict:
    sample = sample_dataset()
    benchmark = benchmark_dataset()
    sample_ga = [optimize(sample, population_size=24, max_generations=60, random_seed=seed) for seed in seeds]
    sample_baseline = [greedy_baseline(sample, improve_feasible=False) for _ in seeds]
    benchmark_baseline = [greedy_baseline(benchmark, improve_feasible=False) for _ in seeds]
    benchmark_ga = [
        optimize(benchmark, population_size=24, max_generations=60, random_seed=seed)
        for seed in seeds
    ]
    benchmark_unseeded = [
        optimize(benchmark, population_size=24, max_generations=60, random_seed=seed, use_greedy_seed=False)
        for seed in seeds
    ]
    benchmark_ga_raw = [
        optimize(
            benchmark,
            population_size=24,
            max_generations=60,
            random_seed=seed,
            use_greedy_seed=False,
            improve_feasible=False,
        )
        for seed in seeds
    ]

    return {
        "parameters": {"population_size": 24, "max_generations": 60, "no_improvement_generations": 25},
        "sample": {
            "dataset_counts": {key: len(getattr(sample, key)) for key in ("faculty", "rooms", "sections", "courses", "time_slots", "teaching_requirements")},
            "baseline": _summarize(sample_baseline, seeds),
            "ga": _summarize(sample_ga, seeds),
        },
        "benchmark": {
            "dataset_counts": {key: len(getattr(benchmark, key)) for key in ("faculty", "rooms", "sections", "courses", "time_slots", "teaching_requirements")},
            "greedy": _summarize(benchmark_baseline, seeds),
            "ga_seeded": _summarize(benchmark_ga, seeds),
            "ga_unseeded": _summarize(benchmark_unseeded, seeds),
            "ga_unseeded_without_local_search": _summarize(benchmark_ga_raw, seeds),
        },
    }


if __name__ == "__main__":
    report = evaluate([1, 7, 42, 99, 123])
    output = Path("apps/evaluation-results.json")
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
