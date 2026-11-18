"""
Algorithm 2: Greedy Study-Hour Allocation & Timetable Generator
Makes locally optimal choices at each step by prioritizing subjects with the
highest urgency-weighted priority score per hour.
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


def solve_greedy(problem: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves the student timetable problem using a Greedy Heuristic approach.
    """
    start_perf = time.perf_counter()

    subjects: List[Dict[str, Any]] = problem["subjects"]
    total_days: int = int(problem["total_days"])
    daily_hours: int = int(problem["daily_hours"])
    start_time: str = problem["start_time"]
    break_minutes: int = int(problem["break_minutes"])

    # Step 1: Compute greedy selection metric (hourly value + deadline proximity)
    ranked_subjects = []
    for subj in subjects:
        hourly_val = compute_subject_hourly_value(subj)
        weight = PRIORITY_WEIGHTS.get(subj["priority"], 1)
        deadline = int(subj["deadline_days"])
        # Greedy key: highest hourly value first, then earliest deadline, then shortest task
        greedy_ratio = round(hourly_val + (weight * 5.0) / max(1, int(subj["required_hours"])), 2)
        ranked_subjects.append(
            {
                "subject": subj,
                "hourly_val": hourly_val,
                "greedy_ratio": greedy_ratio,
                "deadline": deadline,
                "remaining": int(subj["required_hours"]),
            }
        )

    # Sort descending by greedy_ratio, ascending by deadline
    ranked_subjects.sort(
        key=lambda item: (-item["greedy_ratio"], item["deadline"], item["remaining"])
    )

    selection_log: List[str] = [
        "Ranked subjects by Greedy Value Density = (Priority × Urgency) + Completion Bonus Density: "
        + " → ".join(
            f"{item['subject']['name']} ({item['greedy_ratio']} pts/hr, Due Day {item['deadline']})"
            for item in ranked_subjects
        )
        + "."
    ]

    day_assignments: Dict[int, List[Dict[str, Any]]] = {
        d: [] for d in range(1, total_days + 1)
    }

    # Step 2: Greedily fill available daily time slots day-by-day
    for day in range(1, total_days + 1):
        slots_left = daily_hours
        day_allocs: Dict[str, int] = {}

        for item in ranked_subjects:
            if slots_left == 0:
                break
            if item["remaining"] <= 0:
                continue

            # Greedily take as many hours as fit today (capped at 3h/day if other subjects wait,
            # or full remaining if urgent deadline is today)
            if item["deadline"] <= day:
                take = min(item["remaining"], slots_left)
            else:
                # Cap single-session block to 3 hours to reduce consecutive fatigue when non-urgent
                take = min(item["remaining"], slots_left, max(2, daily_hours // 2))

            for _ in range(take):
                day_assignments[day].append(item["subject"])

            item["remaining"] -= take
            slots_left -= take
            day_allocs[item["subject"]["name"]] = day_allocs.get(item["subject"]["name"], 0) + take

        # Second pass on the same day if slots remain and subjects still have remaining hours
        if slots_left > 0:
            for item in ranked_subjects:
                if slots_left == 0:
                    break
                if item["remaining"] > 0:
                    take = min(item["remaining"], slots_left)
                    for _ in range(take):
                        day_assignments[day].append(item["subject"])
                    item["remaining"] -= take
                    slots_left -= take
                    day_allocs[item["subject"]["name"]] = day_allocs.get(item["subject"]["name"], 0) + take

        if day_allocs:
            summary_str = ", ".join(f"{k}: {v}h" for k, v in day_allocs.items())
            selection_log.append(f"Day {day}: Greedily allocated {summary_str}.")
        else:
            selection_log.append(f"Day {day}: All subject requirements already satisfied.")

    # Preserve greedy's selected total hours, then place them by earliest deadline.
    greedy_allocations = []
    for item in ranked_subjects:
        greedy_allocations.append(
            int(item["subject"]["required_hours"]) - int(item["remaining"])
        )
    day_assignments = build_deadline_aware_assignments(
        greedy_allocations, subjects, total_days, daily_hours
    )

    timetable = build_timed_timetable(
        day_assignments, start_time, break_minutes, total_days
    )
    evaluation = evaluate_schedule(timetable, subjects, total_days, daily_hours)

    elapsed_ms = round((time.perf_counter() - start_perf) * 1000, 4)

    return {
        "algorithm": "Greedy Algorithm",
        "tagline": "Priority & Deadline-Driven Locally Optimal Slot Selection",
        "introduction": (
            "The Greedy Algorithm sorts all subjects by a priority-and-deadline density score "
            "and immediately assigns available daily hours to the highest-ranked subject before "
            "moving to the next."
        ),
        "how_it_works": (
            "1. Compute each subject's greedy heuristic score combining priority weight, deadline urgency, "
            "and completion bonus density.\n"
            "2. Sort subjects in descending order of this score.\n"
            "3. Iterate sequentially from Day 1 to Day T, filling available slots with the highest-priority "
            "unfinished subjects without revisiting or undoing earlier choices."
        ),
        "steps": selection_log,
        "time_complexity": "O(N log N + T × N)",
        "space_complexity": "O(N + T × H)",
        "complexity_notes": (
            "Sorting N subjects takes O(N log N) time, and filling T days across N subjects takes O(T × N) time. "
            "Extremely fast in practice, though greedy choices can miss optimal knapsack combinations when "
            "completion bonuses favor smaller subjects."
        ),
        "execution_time_ms": elapsed_ms,
        "search_complete": True,
        "states_explored": len(ranked_subjects) * total_days,
        "timetable": timetable,
        "evaluation": evaluation,
    }