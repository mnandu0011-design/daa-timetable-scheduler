"""
Algorithm 3: Dynamic Programming (Bounded Knapsack Formulation)
Decomposes the weekly study-hour optimization into overlapping subproblems
dp[i][w] = max utility using the first i subjects within w total study hours.
"""

import time
from typing import Dict, List, Any
from algorithms import (
    PRIORITY_WEIGHTS,
    compute_subject_hourly_value,
    build_timed_timetable,
    evaluate_schedule,
    build_deadline_aware_assignments,
)


def solve_dynamic_programming(problem: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves the student timetable problem using Bottom-Up Dynamic Programming.
    """
    start_perf = time.perf_counter()

    subjects: List[Dict[str, Any]] = problem["subjects"]
    total_days: int = int(problem["total_days"])
    daily_hours: int = int(problem["daily_hours"])
    start_time: str = problem["start_time"]
    break_minutes: int = int(problem["break_minutes"])

    n = len(subjects)
    capacity = total_days * daily_hours

    # Precompute item value functions V_i(h) for allocating h hours to subject i
    hourly_values = [compute_subject_hourly_value(s) for s in subjects]
    completion_bonuses = [
        PRIORITY_WEIGHTS.get(s["priority"], 1) * 5.0 for s in subjects
    ]
    req_hours = [int(s["required_hours"]) for s in subjects]

    # DP Table: dp[i][w] stores maximum score using subjects[0..i-1] with w hours
    dp: List[List[float]] = [[0.0] * (capacity + 1) for _ in range(n + 1)]
    # Decision Table: choice[i][w] stores how many hours h were assigned to subject i-1
    choice: List[List[int]] = [[0] * (capacity + 1) for _ in range(n + 1)]

    subproblems_solved = 0

    for i in range(1, n + 1):
        idx = i - 1
        max_h_for_subject = min(req_hours[idx], capacity)
        h_val = hourly_values[idx]
        bonus = completion_bonuses[idx]
        req = req_hours[idx]

        for w in range(capacity + 1):
            subproblems_solved += 1
            # Option 0: Allocate 0 hours to subject idx
            best_val = dp[i - 1][w]
            best_h = 0

            # Options 1..max_h_for_subject: Allocate h hours to subject idx
            for h in range(1, max_h_for_subject + 1):
                if h <= w:
                    gain = h * h_val + (bonus if h == req else 0.0)
                    candidate = dp[i - 1][w - h] + gain
                    if candidate > best_val:
                        best_val = candidate
                        best_h = h

            dp[i][w] = round(best_val, 4)
            choice[i][w] = best_h

    # Reconstruct optimal hour allocation from DP decision table
    # Pick capacity w <= capacity that maximizes dp[n][w] (prefer larger w on ties)
    best_w = 0
    for w in range(1, capacity + 1):
        if dp[n][w] >= dp[n][best_w]:
            best_w = w

    allocated_hours = [0] * n
    curr_w = best_w
    for i in range(n, 0, -1):
        h_taken = choice[i][curr_w]
        allocated_hours[i - 1] = h_taken
        curr_w -= h_taken

    # Schedule reconstructed allocations in earliest-deadline-first order.
    day_assignments = build_deadline_aware_assignments(
        allocated_hours, subjects, total_days, daily_hours
    )

    timetable = build_timed_timetable(
        day_assignments, start_time, break_minutes, total_days
    )
    evaluation = evaluate_schedule(timetable, subjects, total_days, daily_hours)

    elapsed_ms = round((time.perf_counter() - start_perf) * 1000, 4)

    dp_steps = [
        f"Constructed DP state table dp[0..{n}][0..{capacity}] representing {n} subjects and {capacity} total weekly hours.",
        "Recurrence relation: dp[i][w] = max_{0 ≤ h ≤ min(Rᵢ, w)} ( dp[i-1][w-h] + Value(i, h) ).",
        f"Evaluated {subproblems_solved:,} DP states in polynomial time, reusing optimal subproblem solutions.",
        f"Optimal DP table value dp[{n}][{best_w}] = {dp[n][best_w]:.2f}.",
        "Backtracked through decision matrix choice[i][w] to extract optimal hours: "
        + ", ".join(f"{subjects[i]['name']}: {allocated_hours[i]}h" for i in range(n))
        + ".",
        "Mapped allocated hours into daily time slots ordered by earliest exam deadline with anti-fatigue interleaving.",
    ]

    return {
        "algorithm": "Dynamic Programming",
        "tagline": "Bounded Knapsack Subproblem Decomposition & Memoized Table",
        "introduction": (
            "Dynamic Programming breaks the weekly timetable allocation into smaller capacity "
            "subproblems, storing the best achievable score for every subject subset and hour budget "
            "so no subproblem is ever recomputed."
        ),
        "how_it_works": (
            "We define dp[i][w] as the maximum optimization score achievable using the first i subjects "
            "within w total study hours. For each subject i and capacity w, the algorithm tests allocating "
            "h ∈ [0, Rᵢ] hours and adds the value of h hours to the previously stored optimal subproblem "
            "dp[i-1][w-h]. Finally, it backtracks through choice[i][w] to recover exact subject hours."
        ),
        "steps": dp_steps,
        "time_complexity": "O(N × C × R_max)",
        "space_complexity": "O(N × C)",
        "complexity_notes": (
            "Where N is the number of subjects, C = T × H is total weekly hours, and R_max is the maximum "
            "required hours for a single subject. Unlike Brute Force's exponential O((R_max+1)^N) runtime, "
            "DP runs in pseudo-polynomial time while still guaranteeing exact allocation optimality."
        ),
        "execution_time_ms": elapsed_ms,
        "search_complete": True,
        "states_explored": subproblems_solved,
        "timetable": timetable,
        "evaluation": evaluation,
    }