# Debug Review and Fix Report

## Issues found and corrected

1. **Malformed subject data could crash the API** (`app.py`)
   - The validator called `.get()` on every subject row without checking its type.
   - It now reports a validation error when a row is not a JSON object.

2. **Partial-optimization flag could be interpreted incorrectly** (`app.py`)
   - Python treats non-empty strings such as `"false"` as `True`.
   - The API now accepts actual booleans and common explicit true/false representations safely.

3. **Unexpected algorithm errors had no useful API response** (`app.py`)
   - Optimization execution is now protected and logged; the client receives a clear error response instead of an unhandled traceback.

4. **Brute-force state counter could exceed its advertised limit** (`algorithms/brute_force.py`)
   - The limit check happened after incrementing the counter.
   - The counter now stops exactly at 250,000, and the result reports whether the search completed.

5. **Backtracking node limit was not a hard limit** (`algorithms/backtracking.py`)
   - Recursive calls could continue to increment the node count after the limit was reached.
   - Search now stops at 60,000 visited nodes and reports when the result is only the best result found so far.

6. **Search completeness was not visible in algorithm comparisons** (`app.py`, algorithm modules, `static/js/app.js`, `templates/index.html`)
   - Greedy and Dynamic Programming now explicitly report completed searches.
   - The comparison dashboard displays a Search Status column and marks capped searches.
   - The comparison insight warns that capped results are not guaranteed to be globally optimal.

7. **Client-side validation did not match backend limits** (`static/js/app.js`)
   - Added the 10-subject maximum, 60-hour subject maximum, Day 1–30 deadline range, valid 24-hour time validation, and midnight-overflow check.
   - Invalid/non-JSON server responses now produce a readable error message.

8. **Run instructions contained a Markdown typo** (`readme.md`)
   - Fixed the missing code-fence closure and added the server start command and troubleshooting notes.

## Checks performed

- Python compilation: passed (`python -m compileall`).
- JavaScript syntax: passed (`node --check static/js/app.js`).
- HTML/JavaScript element reference check: passed; no missing static element IDs found.
- Direct tests of all four algorithms on three input sets: passed; generated schedules had no detected overlaps or over-allocation and stayed within daily/weekly capacity.

## Testing limitation

Flask is listed in `requirements.txt`, but it was not installed in the execution environment and package installation was unavailable. Therefore, the Flask HTTP routes were syntax-checked but could not be launched here. Install the project dependencies locally with `pip install -r requirements.txt` before running the web app.

## Important algorithm note

Brute Force and Backtracking have safety limits to keep the web app responsive. When the dashboard says **Limit reached**, that algorithm has returned its best result found so far; it has not necessarily proved a global optimum.

## Additional fixes applied (2026-11-18)

### 9. Deadline-aware timetable placement
- Replaced round-robin placement in Brute Force and Dynamic Programming with a shared earliest-deadline-first placement helper.
- Greedy keeps its selected allocation, then places those hours using the same deadline-aware scheduler.
- This prevents later-deadline subjects from taking early slots needed by urgent subjects.

### 10. Unified optimization score
- Standardized the evaluator and Backtracking search on the same additive objective: urgency-weighted hourly value plus a one-time subject-completion bonus.
- Deadline compliance remains visible through deadline warnings; it is not double-counted as a separate score penalty.
- Removed the evaluator-only consecutive-hour score deduction so displayed scores match the objective being optimized.

### 11. Strict whole-number input validation
- Added a shared parser for daily hours, total days, break minutes, required subject hours, and deadline days.
- Decimal values such as `2.5` and decimal-form strings such as `"2.5"` are rejected instead of being silently truncated.
- Integer values remain accepted.

### Verification
- Python compilation completed successfully.
- All four algorithms passed a shared smoke test with two subjects and a 4-day schedule.
- The urgent subject's 6 required hours were all scheduled by Day 2 in Brute Force, Greedy, and Dynamic Programming.
- All four algorithms returned valid schedules and the same score (395.0) for the smoke-test case.
- Whole-number parser tests passed.
- Flask runtime/API testing was not completed because Flask is not installed in the verification environment; install `requirements.txt` and test `/api/optimize` locally.

## Additional fix applied (2026-11-18)

### 12. Backtracking deadline-feasibility pruning
- Added cumulative deadline-feasibility checks during recursive search. A branch is pruned when its remaining work can no longer fit into the available slots before a feasible deadline.
- The anti-fatigue rule is relaxed only when every alternative subject assignment would make an otherwise feasible deadline impossible. This prevents the consecutive-subject restriction from blocking an urgent subject from completing on time.
- If the submitted workload is inherently infeasible against its deadlines, the algorithm retains best-effort scheduling rather than returning an empty timetable.

### Verification
- Python compilation passed for all project Python files.
- All four algorithms generated valid schedules for the deadline regression case.
- Backtracking scheduled all 6 hours of the urgent subject by Day 2 in the regression case; no deadline warnings remained.
- An inherently infeasible workload was handled with a best-effort timetable and warnings, without crashing.
- Flask runtime/API testing remains pending because Flask is not installed in this verification environment.
