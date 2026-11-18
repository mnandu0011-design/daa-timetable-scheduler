"""
Algorithm 4: Backtracking Constraint-Satisfaction & Branch-and-Bound Search
Assigns subjects directly to discrete (Day, Slot) positions, pruning invalid
branches and backtracking when constraints or upper bounds are violated.
"""

import time
from typing import Dict, List, Any
from algorithms import (
    PRIORITY_WEIGHTS,
    compute_subject_hourly_value,
    build_timed_timetable,
    evaluate_schedule,
)


def solve_backtracking(problem: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves the student timetable problem using Recursive Backtracking with
    constraint pruning and upper-bound optimization.
    """
    start_perf = time.perf_counter()

    subjects: List[Dict[str, Any]] = problem["subjects"]
    total_days: int = int(problem["total_days"])
    daily_hours: int = int(problem["daily_hours"])
    start_time: str = problem["start_time"]
    break_minutes: int = int(problem["break_minutes"])

    n = len(subjects)
    total_slots = total_days * daily_hours

    # Sort candidate order so high-priority / urgent subjects are branched on first
    sorted_indices = sorted(
        range(n),
        key=lambda idx: (
            -compute_subject_hourly_value(subjects[idx]),
            int(subjects[idx]["deadline_days"]),
        ),
    )

    hourly_vals = [compute_subject_hourly_value(s) for s in subjects]
    completion_bonuses = [
        PRIORITY_WEIGHTS.get(s["priority"], 1) * 5.0 for s in subjects
    ]
    req_hours = [int(s["required_hours"]) for s in subjects]
    deadlines = [int(s["deadline_days"]) for s in subjects]

    # If the cumulative workload due by every deadline fits in the available
    # capacity, treat those deadlines as hard constraints during search. This
    # prevents a high-scoring later-deadline subject from consuming slots that
    # an earlier-deadline subject needs. If the input is inherently infeasible,
    # retain best-effort scheduling rather than returning an empty timetable.
    deadline_feasible = all(
        sum(
            req_hours[i]
            for i in range(n)
            if deadlines[i] <= deadline_day
        )
        <= min(deadline_day, total_days) * daily_hours
        for deadline_day in sorted(set(deadlines))
    )

    def deadlines_still_reachable(next_slot_pos: int) -> bool:
        if not deadline_feasible:
            return True
        for deadline_day in sorted(set(deadlines)):
            slots_through_deadline = min(deadline_day, total_days) * daily_hours
            slots_left = max(0, slots_through_deadline - next_slot_pos)
            hours_due = sum(
                max(0, req_hours[i] - used_hours[i])
                for i in range(n)
                if deadlines[i] <= deadline_day
            )
            if hours_due > slots_left:
                return False
        return True

    def has_deadline_safe_alternative(excluded_idx: int, next_slot_pos: int) -> bool:
        """Check whether another subject can occupy this slot without making
        any feasible cumulative deadline impossible to meet.
        """
        if not deadline_feasible:
            return True
        for other_idx in range(n):
            if other_idx == excluded_idx or used_hours[other_idx] >= req_hours[other_idx]:
                continue
            used_hours[other_idx] += 1
            safe = deadlines_still_reachable(next_slot_pos)
            used_hours[other_idx] -= 1
            if safe:
                return True
        return False
    max_single_hourly_val = max(hourly_vals) if hourly_vals else 0.0

    # State variables for recursive search
    current_slots: List[int] = [-1] * total_slots  # -1 represents an unassigned/free slot
    used_hours: List[int] = [0] * n

    best_score = -1.0
    best_slots: List[int] = [-1] * total_slots
    nodes_visited = 0
    backtracks_count = 0
    pruned_branches = 0
    search_limit_reached = False

    MAX_NODES = 60_000  # Safety ceiling to keep interactive web response instantaneous

    def backtrack(slot_pos: int, current_score: float) -> None:
        nonlocal best_score, best_slots, nodes_visited, backtracks_count, pruned_branches, search_limit_reached

        if nodes_visited >= MAX_NODES:
            search_limit_reached = True
            return
        nodes_visited += 1

        # Base case: all weekly time slots have been decided
        if slot_pos == total_slots:
            if current_score > best_score:
                best_score = current_score
                best_slots = current_slots.copy()
            return

        # Branch-and-bound pruning: compute optimistic upper bound for remaining slots
        slots_remaining = total_slots - slot_pos
        hours_still_needed = sum(max(0, req_hours[i] - used_hours[i]) for i in range(n))
        if hours_still_needed == 0:
            # All subjects completely satisfied; record optimal state immediately
            if current_score > best_score:
                best_score = current_score
                best_slots = current_slots.copy()
            return

        max_possible_gain = (
            min(slots_remaining, hours_still_needed) * (max_single_hourly_val + 15.0)
        )
        if current_score + max_possible_gain <= best_score:
            pruned_branches += 1
            return

        day = (slot_pos // daily_hours) + 1
        slot_in_day = slot_pos % daily_hours

        # Try assigning each valid subject to this slot
        for idx in sorted_indices:
            # Constraint 1: Do not exceed subject's required hours
            if used_hours[idx] >= req_hours[idx]:
                pruned_branches += 1
                continue

            # Constraint 2: Avoid >2 consecutive identical subjects on the same day
            # if another subject still needs hours
            if (
                slot_in_day >= 2
                and current_slots[slot_pos - 1] == idx
                and current_slots[slot_pos - 2] == idx
                and any(
                    used_hours[other] < req_hours[other]
                    for other in range(n)
                    if other != idx
                )
                # Relax the fatigue rule only when every alternative subject
                # would make an otherwise feasible deadline impossible.
                and has_deadline_safe_alternative(idx, slot_pos + 1)
            ):
                pruned_branches += 1
                continue

            # Compute incremental score gain for placing subject `idx` on `day`
            gain = hourly_vals[idx]
            if used_hours[idx] + 1 == req_hours[idx]:
                gain += completion_bonuses[idx]

            # Choose (forward step)
            current_slots[slot_pos] = idx
            used_hours[idx] += 1

            # Reject a branch immediately if it leaves insufficient slots
            # before any feasible cumulative deadline for the remaining work.
            if deadlines_still_reachable(slot_pos + 1):
                backtrack(slot_pos + 1, current_score + gain)
            else:
                pruned_branches += 1

            # Undo choice (Backtrack)
            used_hours[idx] -= 1
            current_slots[slot_pos] = -1
            backtracks_count += 1
            if search_limit_reached:
                break

        # Option: Leave slot empty only if no subject can legally be placed
        if not search_limit_reached and all(used_hours[i] >= req_hours[i] for i in range(n)):
            backtrack(slot_pos + 1, current_score)

    backtrack(0, 0.0)

    # Convert best_slots array into per-day subject list
    day_assignments: Dict[int, List[Dict[str, Any]]] = {
        d: [] for d in range(1, total_days + 1)
    }
    for pos, subj_idx in enumerate(best_slots):
        if subj_idx != -1:
            day = (pos // daily_hours) + 1
            day_assignments[day].append(subjects[subj_idx])

    timetable = build_timed_timetable(
        day_assignments, start_time, break_minutes, total_days
    )
    evaluation = evaluate_schedule(timetable, subjects, total_days, daily_hours)

    elapsed_ms = round((time.perf_counter() - start_perf) * 1000, 4)

    bt_steps = [
        f"Modeled {total_slots} sequential time slots across {total_days} days as a recursive decision tree of depth {total_slots}.",
        "Applied pruning rules for required-hour caps, anti-fatigue constraints, deadline feasibility, and an optimistic score upper bound.",
        f"Visited {nodes_visited:,} decision nodes, pruned {pruned_branches:,} invalid/suboptimal branches, and performed {backtracks_count:,} backtracks.",
        f"Selected the highest-scoring conflict-free slot assignment found with score {evaluation['optimization_score']}.",
    ]
    if search_limit_reached:
        bt_steps.append(
            f"Search stopped at the {MAX_NODES:,}-node safety limit; this result is the best found so far and is not guaranteed globally optimal."
        )

    return {
        "algorithm": "Backtracking",
        "tagline": "Constraint-Satisfaction Slot Assignment with Branch Pruning",
        "introduction": (
            "Backtracking builds the weekly timetable slot-by-slot, checking scheduling rules "
            "at every step. Whenever a subject exceeds its hour limit, creates excessive consecutive "
            "fatigue, or cannot beat the best known score, the algorithm prunes that path and backtracks."
        ),
        "how_it_works": (
            "1. Represent the timetable as a sequence of S = T × H slots.\n"
            "2. At slot pos, try assigning each eligible subject sorted by urgency.\n"
            "3. Verify subject hour caps, anti-fatigue constraints, and whether remaining work can still meet feasible cumulative deadlines.\n"
            "4. Recurse to pos + 1; upon returning, undo the assignment (backtrack) to explore alternative slot placements."
        ),
        "steps": bt_steps,
        "time_complexity": "O(N^(T × H)) worst-case (heavily pruned in practice)",
        "space_complexity": "O(T × H)",
        "complexity_notes": (
            "The recursion stack depth equals total weekly slots S = T × H, requiring O(T × H) auxiliary memory. "
            "Although the unpruned branching factor is N^S, constraint checking and branch-and-bound pruning "
            "eliminate invalid subtrees early."
        ),
        "execution_time_ms": elapsed_ms,
        "states_explored": nodes_visited,
        "search_complete": not search_limit_reached,
        "timetable": timetable,
        "evaluation": evaluation,
    }