/**
 * Student Timetable Optimizer – Algorithm Explorer
 * Frontend Controller: Dynamic Subject Management, Client Validation,
 * API Execution, Algorithm Tab Explorer & Chart.js Comparison.
 */

let latestOptimizationData = null;
let activeAlgorithmKey = "brute_force";
let scoreChartInstance = null;
let timeChartInstance = null;

const ALGO_ORDER = [
  "brute_force",
  "greedy",
  "dynamic_programming",
  "backtracking",
];

// Default balanced B.Tech engineering study dataset
const PRESET_BALANCED = {
  daily_hours: 4,
  total_days: 5,
  start_time: "09:00",
  break_minutes: 15,
  allow_partial: false,
  subjects: [
    { name: "Design & Analysis of Algorithms", required_hours: 6, priority: "High", deadline_days: 3 },
    { name: "Operating Systems", required_hours: 5, priority: "High", deadline_days: 4 },
    { name: "Database Management Systems", required_hours: 4, priority: "Medium", deadline_days: 5 },
    { name: "Discrete Mathematics", required_hours: 3, priority: "Low", deadline_days: 5 },
  ],
};

// Tight exam crunch dataset where algorithms exhibit distinct knapsack & deadline trade-offs
const PRESET_CRUNCH = {
  daily_hours: 3,
  total_days: 4,
  start_time: "17:00",
  break_minutes: 10,
  allow_partial: true,
  subjects: [
    { name: "Compiler Design", required_hours: 6, priority: "High", deadline_days: 3 },
    { name: "Computer Networks", required_hours: 4, priority: "High", deadline_days: 2 },
    { name: "Software Engineering", required_hours: 3, priority: "Medium", deadline_days: 4 },
    { name: "Microprocessors", required_hours: 3, priority: "Low", deadline_days: 4 },
  ],
};

document.addEventListener("DOMContentLoaded", () => {
  loadPreset(PRESET_BALANCED);

  document.getElementById("addSubjectBtn").addEventListener("click", () => {
    addSubjectRow({ name: "", required_hours: 3, priority: "Medium", deadline_days: 4 });
    updateCapacitySummary();
  });

  document.getElementById("presetBalancedBtn").addEventListener("click", () => {
    loadPreset(PRESET_BALANCED);
  });

  document.getElementById("presetCrunchBtn").addEventListener("click", () => {
    loadPreset(PRESET_CRUNCH);
  });

  document.getElementById("loadSampleHeroBtn").addEventListener("click", () => {
    loadPreset(PRESET_CRUNCH);
    document.getElementById("planner").scrollIntoView({ behavior: "smooth" });
  });

  ["dailyHours", "totalDays"].forEach((id) => {
    document.getElementById(id).addEventListener("input", updateCapacitySummary);
  });

  document.getElementById("optimizerForm").addEventListener("submit", handleFormSubmit);

  document.querySelectorAll(".algo-tab").forEach((tabBtn) => {
    tabBtn.addEventListener("click", () => {
      const algoKey = tabBtn.getAttribute("data-algo");
      selectAlgorithmTab(algoKey);
    });
  });
});

function loadPreset(preset) {
  document.getElementById("dailyHours").value = preset.daily_hours;
  document.getElementById("totalDays").value = preset.total_days;
  document.getElementById("startTime").value = preset.start_time;
  document.getElementById("breakMinutes").value = preset.break_minutes;
  document.getElementById("allowPartial").checked = preset.allow_partial;

  const tbody = document.getElementById("subjectsBody");
  tbody.innerHTML = "";
  preset.subjects.forEach((subj) => addSubjectRow(subj));
  hideErrors();
  updateCapacitySummary();
}

function addSubjectRow(subject = { name: "", required_hours: 2, priority: "Medium", deadline_days: 3 }) {
  const tbody = document.getElementById("subjectsBody");
  const tr = document.createElement("tr");

  tr.innerHTML = `
    <td>
      <input type="text" class="subj-name" placeholder="e.g. Data Structures" value="${escapeHtml(subject.name)}" required />
    </td>
    <td>
      <input type="number" class="subj-hours" min="1" max="60" value="${subject.required_hours}" required />
    </td>
    <td>
      <select class="subj-priority">
        <option value="High" ${subject.priority === "High" ? "selected" : ""}>High</option>
        <option value="Medium" ${subject.priority === "Medium" ? "selected" : ""}>Medium</option>
        <option value="Low" ${subject.priority === "Low" ? "selected" : ""}>Low</option>
      </select>
    </td>
    <td>
      <input type="number" class="subj-deadline" min="1" max="30" value="${subject.deadline_days}" required />
    </td>
    <td>
      <button type="button" class="btn-danger-icon" title="Remove Subject">✕</button>
    </td>
  `;

  tr.querySelector(".btn-danger-icon").addEventListener("click", () => {
    if (tbody.children.length > 1) {
      tr.remove();
      updateCapacitySummary();
    } else {
      showErrors(["At least one subject is required to build a study timetable."]);
    }
  });

  tr.querySelector(".subj-hours").addEventListener("input", updateCapacitySummary);
  tbody.appendChild(tr);
}

function updateCapacitySummary() {
  const daily = parseInt(document.getElementById("dailyHours").value, 10) || 0;
  const days = parseInt(document.getElementById("totalDays").value, 10) || 0;
  const capacity = Math.max(0, daily * days);

  let required = 0;
  document.querySelectorAll(".subj-hours").forEach((input) => {
    const val = parseInt(input.value, 10);
    if (!isNaN(val) && val > 0) {
      required += val;
    }
  });

  document.getElementById("capacityDisplay").textContent = `${capacity} hours`;
  const reqSpan = document.getElementById("requiredDisplay");
  reqSpan.textContent = `${required} hours`;
  reqSpan.style.color = required > capacity ? "#B44332" : "#2F6F44";
}

function collectFormPayload() {
  const subjects = [];
  document.querySelectorAll("#subjectsBody tr").forEach((row) => {
    subjects.push({
      name: row.querySelector(".subj-name").value.trim(),
      required_hours: parseInt(row.querySelector(".subj-hours").value, 10),
      priority: row.querySelector(".subj-priority").value,
      deadline_days: parseInt(row.querySelector(".subj-deadline").value, 10),
    });
  });

  return {
    daily_hours: parseInt(document.getElementById("dailyHours").value, 10),
    total_days: parseInt(document.getElementById("totalDays").value, 10),
    start_time: document.getElementById("startTime").value,
    break_minutes: parseInt(document.getElementById("breakMinutes").value, 10),
    allow_partial: document.getElementById("allowPartial").checked,
    subjects,
  };
}

function clientValidate(payload) {
  const errors = [];
  if (isNaN(payload.daily_hours) || payload.daily_hours < 1 || payload.daily_hours > 16) {
    errors.push("Available study hours per day must be between 1 and 16.");
  }
  if (isNaN(payload.total_days) || payload.total_days < 1 || payload.total_days > 14) {
    errors.push("Number of study days must be between 1 and 14.");
  }
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(payload.start_time || "")) {
    errors.push("Preferred study start time must be a valid 24-hour time.");
  } else if (payload.daily_hours >= 1 && payload.break_minutes >= 0) {
    const [hours, minutes] = payload.start_time.split(":").map(Number);
    const startMinutes = hours * 60 + minutes;
    const requiredMinutes = payload.daily_hours * 60 + Math.max(0, payload.daily_hours - 1) * payload.break_minutes;
    if (startMinutes + requiredMinutes > 24 * 60) {
      errors.push("The selected study hours and breaks would extend past midnight.");
    }
  }
  if (isNaN(payload.break_minutes) || payload.break_minutes < 0 || payload.break_minutes > 60) {
    errors.push("Break duration must be between 0 and 60 minutes.");
  }

  if (payload.subjects.length < 1) {
    errors.push("Please add at least one subject.");
  }
  if (payload.subjects.length > 10) {
    errors.push("A maximum of 10 subjects can be optimized at once.");
  }

  const seen = new Set();
  let totalReq = 0;

  payload.subjects.forEach((s, i) => {
    if (!s.name) {
      errors.push(`Row ${i + 1}: Subject name cannot be empty.`);
    } else {
      const key = s.name.toLowerCase();
      if (seen.has(key)) {
        errors.push(`Duplicate subject name: "${s.name}".`);
      }
      seen.add(key);
    }

    if (isNaN(s.required_hours) || s.required_hours <= 0) {
      errors.push(`"${s.name || "Row " + (i + 1)}": Required study hours must be positive.`);
    } else {
      totalReq += s.required_hours;
    }

    if (isNaN(s.required_hours) || s.required_hours > 60) {
      errors.push(`"${s.name || "Row " + (i + 1)}": Required study hours cannot exceed 60.`);
    }

    if (isNaN(s.deadline_days) || s.deadline_days < 1 || s.deadline_days > 30) {
      errors.push(`"${s.name || "Row " + (i + 1)}": Deadline day must be between Day 1 and Day 30.`);
    }
  });

  const cap = (payload.daily_hours || 0) * (payload.total_days || 0);
  if (errors.length === 0 && totalReq > cap && !payload.allow_partial) {
    errors.push(
      `Impossible schedule: ${totalReq} required hours exceed ${cap} available hours (${payload.total_days} days × ${payload.daily_hours} hrs). Enable "Allow Partial Optimization" or adjust hours.`
    );
  }

  return errors;
}

async function handleFormSubmit(event) {
  event.preventDefault();
  const payload = collectFormPayload();
  const clientErrors = clientValidate(payload);

  if (clientErrors.length > 0) {
    showErrors(clientErrors);
    return;
  }

  hideErrors();
  const submitBtn = document.getElementById("runOptimizerBtn");
  const originalLabel = submitBtn.textContent;
  submitBtn.disabled = true;
  submitBtn.textContent = "Running 4 DAA Algorithms...";

  try {
    const response = await fetch("/api/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    let data;
    try {
      data = await response.json();
    } catch (_) {
      throw new Error("The server returned an unreadable response.");
    }
    if (!response.ok || !data.success) {
      showErrors(data.errors || ["Optimization failed due to invalid input."]);
      return;
    }

    latestOptimizationData = data;
    renderAllResults(data);
  } catch (err) {
    showErrors([err.message || "Network or server error while communicating with Flask backend."]);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalLabel;
  }
}

function renderAllResults(data) {
  document.getElementById("explorer").classList.remove("hidden");
  document.getElementById("comparison").classList.remove("hidden");

  // Update tab score previews
  ALGO_ORDER.forEach((key) => {
    const res = data.results[key];
    const searchStatus = res.search_complete === false ? " • Search limit reached" : "";
    document.getElementById(`tabScore_${key}`).textContent =
      `Score: ${res.evaluation.optimization_score} • ${res.execution_time_ms} ms${searchStatus}`;
  });

  // Render active algorithm tab (default to best algorithm)
  selectAlgorithmTab(data.best_algorithm || "brute_force");

  // Render comparison dashboard
  renderComparisonDashboard(data);

  document.getElementById("explorer").scrollIntoView({ behavior: "smooth" });
}

function selectAlgorithmTab(algoKey) {
  activeAlgorithmKey = algoKey;
  document.querySelectorAll(".algo-tab").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-algo") === algoKey);
  });

  if (!latestOptimizationData) return;
  const algoData = latestOptimizationData.results[algoKey];
  const prob = latestOptimizationData.problem_summary;
  const evalData = algoData.evaluation;

  document.getElementById("algoTagline").textContent = algoData.tagline;
  document.getElementById("algoTitle").textContent = algoData.algorithm;
  document.getElementById("algoScore").textContent = `${evalData.optimization_score} pts`;
  document.getElementById("algoExecTime").textContent = `${algoData.execution_time_ms} ms`;
  document.getElementById("algoStates").textContent = algoData.states_explored.toLocaleString();

  document.getElementById("algoIntro").textContent = algoData.introduction;
  document.getElementById("algoHowItWorks").textContent = algoData.how_it_works;
  document.getElementById("algoTimeComp").textContent = algoData.time_complexity;
  document.getElementById("algoSpaceComp").textContent = algoData.space_complexity;
  document.getElementById("algoCompNotes").textContent = algoData.complexity_notes;

  const stepsList = document.getElementById("algoStepsList");
  stepsList.innerHTML = algoData.steps.map((s) => `<li>${escapeHtml(s)}</li>`).join("");

  // Warnings & Conflicts
  const alertsDiv = document.getElementById("scheduleAlerts");
  alertsDiv.innerHTML = "";
  evalData.conflicts.forEach((c) => {
    alertsDiv.innerHTML += `<div class="alert-warning"><strong>Conflict:</strong> ${escapeHtml(c)}</div>`;
  });
  evalData.warnings.forEach((w) => {
    alertsDiv.innerHTML += `<div class="alert-warning"><strong>Notice:</strong> ${escapeHtml(w)}</div>`;
  });

  // KPIs
  const remainingTotal = Math.max(0, evalData.total_required_hours - evalData.total_allocated_hours);
  const dailyAvg = (evalData.total_allocated_hours / prob.total_days).toFixed(1);
  document.getElementById("kpiTotalHours").textContent =
    `${evalData.total_allocated_hours} / ${prob.total_capacity} hrs`;
  document.getElementById("kpiValidity").textContent =
    evalData.is_valid ? "Conflict-Free ✓" : "Conflicts Found ⚠";
  document.getElementById("kpiDailyAvg").textContent = `${dailyAvg} hrs/day`;
  document.getElementById("kpiRemaining").textContent = `${remainingTotal} hrs`;

  // Subject-wise allocation table
  const subjBody = document.getElementById("subjectSummaryBody");
  subjBody.innerHTML = evalData.subject_summary
    .map(
      (s) => `
      <tr>
        <td><strong>${escapeHtml(s.subject)}</strong></td>
        <td><span class="priority-pill priority-${s.priority}">${s.priority}</span></td>
        <td>Day ${s.deadline_days}</td>
        <td>${s.allocated_hours} / ${s.required_hours} hrs (${s.completion_pct}%)</td>
        <td>${s.remaining_hours} hrs</td>
      </tr>
    `
    )
    .join("");

  // Daily study-hour summary bars
  const dailyBarsDiv = document.getElementById("dailySummaryBars");
  dailyBarsDiv.innerHTML = evalData.daily_summary
    .map((d) => {
      const pct = Math.min(100, Math.round((d.hours / prob.daily_hours) * 100));
      return `
        <div class="daily-bar-row">
          <div class="daily-bar-meta">
            <span>${d.day_label}</span>
            <span>${d.hours} / ${prob.daily_hours} hrs</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill" style="width: ${pct}%"></div>
          </div>
        </div>
      `;
    })
    .join("");

  // Weekly Timetable Table
  document.getElementById("timetableAlgoBadge").textContent = `${algoData.algorithm} Schedule`;
  const ttBody = document.getElementById("timetableBody");
  if (algoData.timetable.length === 0) {
    ttBody.innerHTML = `<tr><td colspan="6">No study sessions scheduled.</td></tr>`;
  } else {
    ttBody.innerHTML = algoData.timetable
      .map(
        (slot) => `
        <tr>
          <td><span class="day-pill">${slot.day_name}</span></td>
          <td><code>${slot.time_slot}</code></td>
          <td><strong>${escapeHtml(slot.subject)}</strong> <small>(Due Day ${slot.deadline_days})</small></td>
          <td>${slot.duration}</td>
          <td><span class="priority-pill priority-${slot.priority}">${slot.priority}</span></td>
          <td>${slot.break_after}</td>
        </tr>
      `
      )
      .join("");
  }
}

function renderComparisonDashboard(data) {
  document.getElementById("comparisonInsightBanner").innerHTML =
    `<strong>DAA Comparative Analysis:</strong> ${escapeHtml(data.comparison_insight)}`;

  const labels = ALGO_ORDER.map((k) => data.results[k].algorithm);
  const scores = ALGO_ORDER.map((k) => data.results[k].evaluation.optimization_score);
  const times = ALGO_ORDER.map((k) => data.results[k].execution_time_ms);

  // Matrix Table
  const matrixBody = document.getElementById("comparisonMatrixBody");
  matrixBody.innerHTML = ALGO_ORDER.map((key) => {
    const r = data.results[key];
    const isBest = key === data.best_algorithm;
    return `
      <tr class="${isBest ? "best-row" : ""}">
        <td><strong>${r.algorithm}</strong> ${isBest ? "★" : ""}</td>
        <td>${r.evaluation.optimization_score} pts</td>
        <td>${r.evaluation.total_allocated_hours} / ${r.evaluation.total_required_hours} hrs</td>
        <td>${r.evaluation.is_valid ? "Valid (No Overlaps)" : "Invalid"}</td>
        <td>${r.execution_time_ms} ms</td>
        <td>${r.states_explored.toLocaleString()}</td>
        <td>${r.search_complete === false ? "Limit reached" : "Complete"}</td>
        <td><code>${r.time_complexity}</code></td>
        <td><code>${r.space_complexity}</code></td>
      </tr>
    `;
  }).join("");

  // Render Chart.js visualizations
  const scoreCtx = document.getElementById("scoreChart").getContext("2d");
  if (scoreChartInstance) scoreChartInstance.destroy();
  scoreChartInstance = new Chart(scoreCtx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Optimization Score (pts)",
          data: scores,
          backgroundColor: ["#A67C52", "#C9A682", "#87613C", "#D6BFA6"],
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } },
    },
  });

  const timeCtx = document.getElementById("timeChart").getContext("2d");
  if (timeChartInstance) timeChartInstance.destroy();
  timeChartInstance = new Chart(timeCtx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Execution Time (ms)",
          data: times,
          backgroundColor: ["#87613C", "#A67C52", "#C9A682", "#D6BFA6"],
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } },
    },
  });
}

function showErrors(errors) {
  const banner = document.getElementById("errorBanner");
  const list = document.getElementById("errorList");
  list.innerHTML = errors.map((e) => `<li>${escapeHtml(e)}</li>`).join("");
  banner.classList.remove("hidden");
  banner.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideErrors() {
  document.getElementById("errorBanner").classList.add("hidden");
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}