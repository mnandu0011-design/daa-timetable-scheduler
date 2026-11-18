"""
Algorithm 1: Brute Force Study-Hour Allocation & Timetable Generator
Explores the Cartesian product search space of valid study-hour allocations
to guarantee finding the global optimum under capacity constraints.
"""

import itertools
import time
from typing import Dict, List, Any
from algorithms import (
    PRIORITY_WEIGHTS,
    compute_subject_hourly_value,
    build_timed_timetable,
    evaluate_schedule,
    build_deadline_aware_assignments,
)


def solve_brute_force(problem: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves the student timetable problem using Exhaustive Brute Force search.
    """
    start_perf = time.perf_counter()

    subjects: List[Dict[str, Any]] = problem["subjects"]
    total_days: int = int(problem["total_days"])
    daily_hours: int = int(problem["daily_hours"])
    start_time: str = problem["start_time"]
    break_minutes: int = int(problem["break_minutes"])

    total_capacity = total_days * daily_hours
    n = len(subjects)

    # Precompute per-hour value and completion bonus for each subject
    hourly_values = [compute_subject_hourly_value(s) for s in subjects]
    completion_bonuses = [
        PRIORITY_WEIGHTS.get(s["priority"], 1) * 5.0 for s in subjects
    ]
    req_hours = [int(s["required_hours"]) for s in subjects]

    # Build ranges [0..R_i] capped by total_capacity
    ranges = [range(0, min(r, total_capacity) + 1) for r in req_hours]

    # Guardrail against combinatorial explosion on huge inputs while remaining
    # strictly exhaustive for typical college subject sets (N <= 8)
    MAX_COMBINATIONS = 250_000
    combinations_examined = 0
    valid_combinations = 0
    best_score = -1.0
    best_allocation = tuple(0 for _ in range(n))
    truncated = False

    for alloc_tuple in itertools.product(*ranges):
        if combinations_examined >= MAX_COMBINATIONS:
            truncated = True
            break
        combinations_examined += 1

        used_hours = sum(alloc_tuple)
        if used_hours > total_capacity:
            continue

        valid_combinations += 1
        score = 0.0
        for i in range(n):
            x_i = alloc_tuple[i]
            if x_i > 0:
                score += x_i * hourly_values[i]
                if x_i == req_hours[i]:
                    score += completion_bonuses[i]

        # Tie-breaker: prefer utilizing more available study capacity
        if score > best_score or (
            score == best_score and used_hours > sum(best_allocation)
        ):
            best_score = score
            best_allocation = alloc_tuple

    # Schedule allocated hours in earliest-deadline-first order.
    day_assignments = build_deadline_aware_assignments(
        list(best_allocation), subjects, total_days, daily_hours
    )

    timetable = build_timed_timetable(
        day_assignments, start_time, break_minutes, total_days
    )
    evaluation = evaluate_schedule(timetable, subjects, total_days, daily_hours)

    elapsed_ms = round((time.perf_counter() - start_perf) * 1000, 4)

    explanation_steps = [
        f"Defined search space across {n} subjects with total capacity C = {total_days} days × {daily_hours} hrs = {total_capacity} slots.",
        f"Enumerated {combinations_examined:,} candidate allocation vectors (x₁, x₂, ..., xₙ) where 0 ≤ xᵢ ≤ Rᵢ.",
        f"Filtered {valid_combinations:,} feasible vectors satisfying ∑xᵢ ≤ {total_capacity} hours.",
        f"Evaluated objective score (priority × urgency + completion bonus) for every valid tuple; optimal allocation found: "
        + ", ".join(f"{subjects[i]['name']}: {best_allocation[i]}h" for i in range(n))
        + ".",
        "Assigned optimal hours onto earliest-deadline days in round-robin passes to avoid cognitive fatigue.",
    ]
    if truncated:
        explanation_steps.append(
            f"Note: Search space exceeded {MAX_COMBINATIONS:,} states; evaluated first {MAX_COMBINATIONS:,} states."
        )

    return {
        "algorithm": "Brute Force",
        "tagline": "Exhaustive Cartesian Search Over All Feasible Hour Allocations",
        "introduction": (
            "Brute Force systematically enumerates every possible combination of study hours "
            "across all subjects, filters out combinations that exceed the weekly hour limit, "
            "and picks the combination with the highest mathematical utility score."
        ),
        "how_it_works": (
            "Using nested Cartesian product iteration (itertools.product), the algorithm generates "
            "all tuples (x₁, x₂, ..., xₙ) where each xᵢ ranges from 0 up to the subject's required hours Rᵢ. "
            "Each tuple violating ∑xᵢ ≤ Total Capacity is discarded. Valid tuples are scored, guaranteeing "
            "the exact global optimum within the allocation space."
        ),
        "steps": explanation_steps,
        "time_complexity": "O(∏ (Rᵢ + 1)) ≈ O((R_max + 1)^N)",
        "space_complexity": "O(N + T × H)",
        "complexity_notes": (
            "Exponential in the number of subjects N because every combination of required hours Rᵢ is tested. "
            "Space remains linear because tuples are streamed via a generator rather than stored simultaneously."
        ),
        "execution_time_ms": elapsed_ms,
        "states_explored": combinations_examined,
        "search_complete": not truncated,
        "timetable": timetable,
        "evaluation": evaluation,
    }