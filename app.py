"""
Main Flask Backend Application for:
STUDENT TIMETABLE OPTIMIZER – ALGORITHM EXPLORER
"""

from datetime import datetime
from typing import Dict, List, Any, Tuple
from flask import Flask, render_template, request, jsonify

from algorithms.brute_force import solve_brute_force
from algorithms.greedy import solve_greedy
from algorithms.dynamic_programming import solve_dynamic_programming
from algorithms.backtracking import solve_backtracking

app = Flask(__name__)

VALID_PRIORITIES = {"High", "Medium", "Low"}


def parse_whole_number(value: Any) -> int:
    """Parse an integer without silently truncating decimal input."""
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid whole numbers.")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError("Decimal values are not valid whole numbers.")
    if isinstance(value, str):
        text = value.strip()
        if text and text.lstrip("+-").isdigit():
            return int(text)
    raise ValueError("Value must be a whole number.")


def validate_student_input(data: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validates all student input fields and checks mathematical feasibility.
    Returns (is_valid, error_messages, cleaned_problem_dict).
    """
    errors: List[str] = []

    if not isinstance(data, dict):
        return False, ["Invalid request payload format."], {}

    # 1. Validate schedule parameters
    try:
        daily_hours = parse_whole_number(data.get("daily_hours", 0))
        if daily_hours < 1 or daily_hours > 16:
            errors.append("Available study hours per day must be between 1 and 16 hours.")
    except (ValueError, TypeError):
        errors.append("Available study hours per day must be a valid whole number.")
        daily_hours = 0

    try:
        total_days = parse_whole_number(data.get("total_days", 0))
        if total_days < 1 or total_days > 14:
            errors.append("Number of study days must be between 1 and 14 days.")
    except (ValueError, TypeError):
        errors.append("Number of study days must be a valid whole number.")
        total_days = 0

    try:
        break_minutes = parse_whole_number(data.get("break_minutes", 0))
        if break_minutes < 0 or break_minutes > 60:
            errors.append("Break duration must be between 0 and 60 minutes.")
    except (ValueError, TypeError):
        errors.append("Break duration must be a valid whole number of minutes.")
        break_minutes = 0

    start_time = str(data.get("start_time", "")).strip()
    try:
        parsed_start = datetime.strptime(start_time, "%H:%M")
        # Check if total daily study + breaks overflows past 23:59
        if daily_hours > 0 and break_minutes >= 0:
            total_minutes_needed = (daily_hours * 60) + max(0, daily_hours - 1) * break_minutes
            start_minutes = parsed_start.hour * 60 + parsed_start.minute
            if start_minutes + total_minutes_needed > 24 * 60:
                errors.append(
                    f"Impossible daily schedule: Starting at {start_time} for {daily_hours}h "
                    f"with {break_minutes}-min breaks exceeds midnight (24:00)."
                )
    except ValueError:
        errors.append("Preferred study start time must be a valid time (HH:MM).")

    # 2. Validate subjects list
    raw_subjects = data.get("subjects", [])
    if not isinstance(raw_subjects, list) or len(raw_subjects) == 0:
        errors.append("Please add at least one subject to generate a timetable.")
        return False, errors, {}

    if len(raw_subjects) > 10:
        errors.append("Maximum 10 subjects allowed per optimization run for accurate comparison.")

    cleaned_subjects: List[Dict[str, Any]] = []
    seen_names = set()
    total_required_hours = 0

    for idx, item in enumerate(raw_subjects, start=1):
        if not isinstance(item, dict):
            errors.append(f"Row {idx}: Subject must be an object with name, hours, priority, and deadline fields.")
            continue

        name = str(item.get("name", "")).strip()
        if not name:
            errors.append(f"Row {idx}: Subject name cannot be empty.")
            continue

        normalized_name = name.lower()
        if normalized_name in seen_names:
            errors.append(f"Duplicate subject name detected: '{name}'. Each subject must be unique.")
        seen_names.add(normalized_name)

        try:
            req_hours = parse_whole_number(item.get("required_hours", 0))
            if req_hours <= 0:
                errors.append(f"'{name}': Required study hours must be greater than 0 (cannot be negative or zero).")
            elif req_hours > 60:
                errors.append(f"'{name}': Required study hours cannot exceed 60 hours.")
        except (ValueError, TypeError):
            errors.append(f"'{name}': Required study hours must be a valid integer.")
            req_hours = 0

        priority = str(item.get("priority", "")).strip()
        if priority not in VALID_PRIORITIES:
            errors.append(f"'{name}': Priority must be High, Medium, or Low.")

        try:
            deadline_days = parse_whole_number(item.get("deadline_days", 0))
            if deadline_days < 1 or deadline_days > 30:
                errors.append(f"'{name}': Deadline / exam day must be between Day 1 and Day 30.")
        except (ValueError, TypeError):
            errors.append(f"'{name}': Deadline must be a valid day number.")
            deadline_days = 1

        total_required_hours += max(0, req_hours)
        cleaned_subjects.append(
            {
                "name": name,
                "required_hours": req_hours,
                "priority": priority,
                "deadline_days": deadline_days,
            }
        )

    # 3. Check impossible scheduling constraints (if strict mode or zero capacity)
    total_capacity = daily_hours * total_days
    if total_capacity <= 0 and not errors:
        errors.append("Total available weekly study hours must be at least 1 hour.")

    raw_allow_partial = data.get("allow_partial", False)
    if isinstance(raw_allow_partial, bool):
        allow_partial = raw_allow_partial
    elif isinstance(raw_allow_partial, str) and raw_allow_partial.strip().lower() in {"true", "1", "yes", "on"}:
        allow_partial = True
    elif isinstance(raw_allow_partial, (int, float)) and raw_allow_partial in (0, 1):
        allow_partial = bool(raw_allow_partial)
    else:
        allow_partial = False
        if raw_allow_partial not in (None, "", 0):
            errors.append("Allow Partial Optimization must be a boolean value.")
    if not errors and total_required_hours > total_capacity and not allow_partial:
        errors.append(
            f"Impossible scheduling requirement: Total required study hours ({total_required_hours}h) "
            f"exceed total available study capacity ({total_days} days × {daily_hours}h = {total_capacity}h). "
            "Increase daily hours/days, reduce subject hours, or enable 'Allow Partial Optimization under Tight Deadlines'."
        )

    if errors:
        return False, errors, {}

    cleaned_problem = {
        "subjects": cleaned_subjects,
        "daily_hours": daily_hours,
        "total_days": total_days,
        "start_time": start_time,
        "break_minutes": break_minutes,
        "total_capacity": total_capacity,
        "total_required_hours": total_required_hours,
    }
    return True, [], cleaned_problem


@app.route("/")
def index():
    """Renders the main Student Timetable Optimizer dashboard."""
    return render_template("index.html")


@app.route("/api/optimize", methods=["POST"])
def optimize_timetable():
    """
    Validates student input and executes all four DAA algorithms on the exact same
    problem instance, returning results, complexity metrics, and comparisons.
    """
    payload = request.get_json(silent=True)
    is_valid, errors, problem = validate_student_input(payload)

    if not is_valid:
        return jsonify({"success": False, "errors": errors}), 400

    # Execute each algorithm independently so one unexpected failure does not
    # crash the entire API request without a useful diagnostic.
    try:
        bf_result = solve_brute_force(problem)
        greedy_result = solve_greedy(problem)
        dp_result = solve_dynamic_programming(problem)
        bt_result = solve_backtracking(problem)
    except (ArithmeticError, KeyError, TypeError, ValueError, RecursionError) as exc:
        app.logger.exception("Timetable optimization failed")
        return jsonify({
            "success": False,
            "errors": [f"The optimizer could not complete this input: {type(exc).__name__}. Please check the subject details and try again."],
        }), 500

    results = {
        "brute_force": bf_result,
        "greedy": greedy_result,
        "dynamic_programming": dp_result,
        "backtracking": bt_result,
    }

    # Generate analytical comparison summary explaining differences
    scores = {k: v["evaluation"]["optimization_score"] for k, v in results.items()}
    best_algo_key = max(scores, key=lambda k: scores[k])
    best_algo_name = results[best_algo_key]["algorithm"]
    incomplete_algorithms = [
        result["algorithm"] for result in results.values()
        if not result.get("search_complete", True)
    ]

    unique_scores = set(scores.values())
    if len(unique_scores) == 1:
        comparison_insight = (
            f"All four algorithms achieved the exact same optimal score ({scores[best_algo_key]} pts) "
            "because the available weekly study capacity was sufficient to satisfy subject priorities "
            "without forcing difficult knapsack trade-offs."
        )
    else:
        comparison_insight = (
            f"{best_algo_name} achieved the highest optimization score ({scores[best_algo_key]} pts). "
            "Differences arise because Greedy selects locally highest priority-density subjects without "
            "lookahead for completion bonuses, Backtracking enforces anti-fatigue slot spacing and deadline "
            "penalties directly on days, whereas Dynamic Programming and Brute Force solve the exact global "
            "hour-allocation knapsack before assigning slots."
        )

    if incomplete_algorithms:
        comparison_insight += (
            " Search-limit note: " + ", ".join(incomplete_algorithms)
            + " stopped at a safety limit, so their displayed results are the best found so far, "
            "not a proof of global optimality."
        )

    return jsonify(
        {
            "success": True,
            "problem_summary": {
                "total_subjects": len(problem["subjects"]),
                "total_required_hours": problem["total_required_hours"],
                "total_capacity": problem["total_capacity"],
                "daily_hours": problem["daily_hours"],
                "total_days": problem["total_days"],
                "start_time": problem["start_time"],
                "break_minutes": problem["break_minutes"],
            },
            "results": results,
            "best_algorithm": best_algo_key,
            "comparison_insight": comparison_insight,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)