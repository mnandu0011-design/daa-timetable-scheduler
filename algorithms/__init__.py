"""
Shared utilities, validation, timetable slot generator, and unified objective
evaluator for the Student Timetable Optimizer.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple


PRIORITY_WEIGHTS = {
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


def compute_subject_hourly_value(subject: Dict[str, Any]) -> float:
    """
    Computes the utility score of allocating 1 study hour to a subject
    based on priority weight and deadline urgency.
    """
    weight = PRIORITY_WEIGHTS.get(subject["priority"], 1)
    days_left = max(1, int(subject["deadline_days"]))
    urgency_multiplier = 1.0 + (1.0 / days_left)
    return round(weight * 10.0 * urgency_multiplier, 2)


def evaluate_schedule(
    schedule: List[Dict[str, Any]],
    subjects: List[Dict[str, Any]],
    total_days: int,
    daily_hours: int,
) -> Dict[str, Any]:
    """
    Evaluates a generated timetable across all DAA metrics:
    - Optimization score (higher is better)
    - Subject-wise allocated vs required hours
    - Conflict detection (overlapping slots or exceeding daily capacity)
    - Deadline compliance warnings
    """
    subject_map = {s["name"]: s for s in subjects}
    allocated_counts: Dict[str, int] = {s["name"]: 0 for s in subjects}
    daily_counts: Dict[int, int] = {d: 0 for d in range(1, total_days + 1)}

    occupied_slots = set()
    conflicts: List[str] = []
    warnings: List[str] = []
    total_score = 0.0

    for entry in schedule:
        day = entry["day"]
        slot_index = entry["slot_index"]
        subj_name = entry["subject"]

        # Conflict Check 1: Duplicate time slot on same day
        if (day, slot_index) in occupied_slots:
            conflicts.append(
                f"Overlap detected on Day {day} at slot {entry['time_slot']}."
            )
        occupied_slots.add((day, slot_index))

        # Conflict Check 2: Exceeding daily study limit
        daily_counts[day] = daily_counts.get(day, 0) + 1
        if daily_counts[day] > daily_hours:
            conflicts.append(
                f"Day {day} exceeds maximum daily study limit of {daily_hours} hours."
            )

        if subj_name in subject_map:
            subj = subject_map[subj_name]
            allocated_counts[subj_name] += 1
            base_val = compute_subject_hourly_value(subj)
            # The shared optimization objective is additive: urgency-weighted
            # hourly value plus a one-time completion bonus. Deadline compliance
            # is reported separately as a warning, not scored differently here.
            total_score += base_val

    # Completion bonus & remaining requirement tracking
    subject_summary = []
    total_required = 0
    total_allocated = 0

    for subj in subjects:
        name = subj["name"]
        req = int(subj["required_hours"])
        alloc = allocated_counts[name]
        rem = max(0, req - alloc)
        total_required += req
        total_allocated += alloc

        if alloc > req:
            conflicts.append(
                f"Over-allocation for {name}: {alloc}h allocated vs {req}h required."
            )

        if alloc == req and req > 0:
            # Completion bonus for finishing full syllabus of a subject
            total_score += PRIORITY_WEIGHTS.get(subj["priority"], 1) * 5.0

        if rem > 0:
            warnings.append(
                f"{name} ({subj['priority']} priority): {rem} of {req} required hours unscheduled due to time limit."
            )

        # Check if deadline fell before total days and hours were missed before deadline
        deadline_day = int(subj["deadline_days"])
        hours_before_deadline = sum(
            1
            for e in schedule
            if e["subject"] == name and e["day"] <= deadline_day
        )
        if hours_before_deadline < req and deadline_day <= total_days:
            warnings.append(
                f"Deadline alert: {name} exam is on Day {deadline_day}, but only {hours_before_deadline}/{req}h scheduled on or before Day {deadline_day}."
            )

    # Build subject-wise breakdown
    for subj in subjects:
        name = subj["name"]
        req = int(subj["required_hours"])
        alloc = allocated_counts[name]
        subject_summary.append(
            {
                "subject": name,
                "priority": subj["priority"],
                "deadline_days": int(subj["deadline_days"]),
                "required_hours": req,
                "allocated_hours": alloc,
                "remaining_hours": max(0, req - alloc),
                "completion_pct": round((alloc / req) * 100, 1) if req > 0 else 100.0,
            }
        )

    return {
        "optimization_score": round(max(0.0, total_score), 2),
        "is_valid": len(conflicts) == 0,
        "conflicts": conflicts,
        "warnings": warnings,
        "total_allocated_hours": total_allocated,
        "total_required_hours": total_required,
        "daily_summary": [
            {"day": d, "day_label": f"Day {d}", "hours": daily_counts[d]}
            for d in range(1, total_days + 1)
        ],
        "subject_summary": subject_summary,
    }


def build_deadline_aware_assignments(
    allocated_hours: List[int],
    subjects: List[Dict[str, Any]],
    total_days: int,
    daily_hours: int,
) -> Dict[int, List[Dict[str, Any]]]:
    """Place allocated hours in earliest-deadline-first order.

    This ensures hours for the most urgent subject are scheduled before later
    deadlines, rather than round-robin spreading them across all subjects.
    """
    ordered_indices = sorted(
        range(len(subjects)),
        key=lambda i: (
            int(subjects[i]["deadline_days"]),
            -PRIORITY_WEIGHTS.get(subjects[i]["priority"], 1),
            i,
        ),
    )
    remaining = [max(0, int(hours)) for hours in allocated_hours]
    assignments: Dict[int, List[Dict[str, Any]]] = {
        day: [] for day in range(1, total_days + 1)
    }
    for day in range(1, total_days + 1):
        for idx in ordered_indices:
            while remaining[idx] > 0 and len(assignments[day]) < daily_hours:
                assignments[day].append(subjects[idx])
                remaining[idx] -= 1
            if len(assignments[day]) >= daily_hours:
                break
    return assignments


def build_timed_timetable(
    day_assignments: Dict[int, List[Dict[str, Any]]],
    start_time_str: str,
    break_minutes: int,
    total_days: int,
) -> List[Dict[str, Any]]:
    """
    Converts per-day ordered subject blocks (1 hour each) into a clock-accurate
    weekly schedule including formatted time slots and break intervals.
    """
    base_time = datetime.strptime(start_time_str, "%H:%M")
    timetable: List[Dict[str, Any]] = []

    for day in range(1, total_days + 1):
        blocks = day_assignments.get(day, [])
        current_dt = base_time

        for idx, subj in enumerate(blocks):
            end_dt = current_dt + timedelta(hours=1)
            time_slot_label = (
                f"{current_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
            )

            break_after = "None (End of Day)"
            if idx < len(blocks) - 1 and break_minutes > 0:
                break_end = end_dt + timedelta(minutes=break_minutes)
                break_after = (
                    f"{break_minutes} mins ({end_dt.strftime('%I:%M %p')} - {break_end.strftime('%I:%M %p')})"
                )
                next_start = break_end
            else:
                next_start = end_dt

            timetable.append(
                {
                    "day": day,
                    "day_name": f"Day {day}",
                    "slot_index": idx + 1,
                    "time_slot": time_slot_label,
                    "subject": subj["name"],
                    "duration": "1 hr",
                    "priority": subj["priority"],
                    "deadline_days": int(subj["deadline_days"]),
                    "break_after": break_after,
                }
            )
            current_dt = next_start

    return timetable