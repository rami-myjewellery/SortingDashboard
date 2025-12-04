from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any

from app.utils.MainUtils import get_or_create_person
from app.data.store import get_db, MAX_PEOPLE
from datetime import timezone

# ── Parameters ───────────────────────────────────────────────────────────────
ROLLING_WINDOW = timedelta(minutes=60)   # size of the rolling KPI window
JOB_TIMES_MAXLEN = 6000                  # keep enough events to cover the hour
MAX_RECENT_EVENTS = 6000                 # keep enough events for the last hour

# ── KPI Update Function ──────────────────────────────────────────────────────

def calc_kpi_based_on_event(job_data: Dict[str, Any], dashboard: Any) -> None:
    """
    Increments dashboard KPIs by the quantity in job_data:
    - For Pick jobs: use NUMBER_OF_LINES (fallback 1), but only when PICKBATCH_CONFIRMED == 1
    - For GeekPicking: use NUMBER_OF_LINES (fallback 1)
    - Else: use RAW_GEEK.data.ipg_list[*].base_lv_quantity (fallback 1)
    """
    now = datetime.now(timezone.utc)

    job_type = job_data.get("job_type")

    # ----- Determine qty -----
    if job_type == "Pick" and job_data.get("PICKBATCH_CONFIRMED") == 1:
        # Dynamic quantity based on NUMBER_OF_LINES (or NUMBER_OF_HANDING_UNITS if you prefer)
        raw_val = job_data.get("NUMBER_OF_LINES")  # or "NUMBER_OF_HANDING_UNITS"
        try:
            qty = int(raw_val)
        except (ValueError, TypeError):
            qty = 0

    elif job_type == "GeekPicking":
        # Geek picking jobs: also count NUMBER_OF_LINES
        raw_val = job_data.get("NUMBER_OF_LINES")
        try:
            qty = int(raw_val)
        except (ValueError, TypeError):
            qty = 0

    else:
        # Original RAW_GEEK-based logic as fallback for other job types
        inner = job_data.get("RAW_GEEK", {}).get("data", {})
        ipg_list = inner.get("ipg_list", [])
        if isinstance(ipg_list, list) and ipg_list:
            def safe_int(x, default=1):
                try:
                    return int(x)
                except (ValueError, TypeError):
                    return default

            qty = sum(safe_int(item.get("base_lv_quantity", 1)) for item in ipg_list)
        else:
            qty = 1  # fallback if ipg_list missing/empty

    # ----- Initialise KPI state if needed -----
    if getattr(dashboard, "kpi_state", None) is None:
        dashboard.kpi_state = {
            "date": now.date(),
            "total": 0,
            "first_event_time": now,
            "recent": [],
        }

    state = dashboard.kpi_state

    # ----- Reset for a new day -----
    if state.get("date") != now.date():
        state["date"] = now.date()
        state["total"] = 0
        state["first_event_time"] = now
        state["recent"] = []

    # ----- Update totals -----
    state["total"] += qty

    # ----- Maintain rolling one-hour window -----
    recent_events = state.get("recent") or []
    recent = deque(
        (
            (float(event.get("ts", 0)), int(event.get("qty", 0)))
            for event in recent_events
            if isinstance(event, dict)
        ),
        maxlen=MAX_RECENT_EVENTS,
    )
    recent.append((now.timestamp(), qty))

    cutoff_ts = (now - ROLLING_WINDOW).timestamp()
    while recent and recent[0][0] < cutoff_ts:
        recent.popleft()

    window_total = sum(amount for _, amount in recent)
    per_hour = window_total * (3600 / ROLLING_WINDOW.total_seconds())

    # Persist recent events in a JSON-friendly format
    state["recent"] = [{"ts": ts, "qty": amount} for ts, amount in recent]

    # Assume [0] = per hour, [1] = total today
    dashboard.kpis[0].value = round(per_hour, 0)
    dashboard.kpis[1].value = state["total"]

# ── Main Update Function ─────────────────────────────────────────────────────
async def update_jobs_store_metric(job_data: Dict[str, Any]) -> Dict[str, Any]:
    # Extract required information
    job_id = job_data.get("HEADER_ID")
    comment = (job_data.get("comment") or "").strip()
    operator_name = (job_data.get("EMPLOYEE_CODE") or "").strip() or "Unknown"
    job_type = (job_data.get("HIGH_OVER_PROCESS") or "").strip()
    now = datetime.now(timezone.utc)

    job_data["job_type"] = job_type  # keep for downstream KPI calculation, etc.

    # 1) Get dashboard
    db = get_db().get(job_type.lower())
    if not db:
        return {"status": "error", "detail": f"Dashboard for job type '{job_type}' not found."}

    # 2) Get/create operator
    person = get_or_create_person(db.people, operator_name, job_type, comment)

    # 3) Determine how many lines to add
    def _coerce_lines(val, default=1) -> int:
        # Prefer LINE_COUNT, then amount_of_lines; keep default=1 to mimic old +1 behavior when missing
        try:
            if val is None:
                return default
            num = int(float(val))  # allow strings like "7"
            return max(0, num)  # no negative increments
        except Exception:
            return default

    amount_of_lines = _coerce_lines(
        job_data.get("NUMBER_OF_LINES", None) if "NUMBER_OF_LINES" in job_data else job_data.get("NUMBER_OF_LINES", None),
        default=1,
    )

    # 4) Ensure rolling window (store [timestamp, qty] pairs) and speed
    existing_times = getattr(person, "job_times", None)
    normalized_times = deque(maxlen=JOB_TIMES_MAXLEN)
    if existing_times:
        for entry in existing_times:
            if isinstance(entry, (list, tuple)) and len(entry) == 2:
                ts, qty = entry
            else:
                ts, qty = entry, 1
            try:
                normalized_times.append((float(ts), int(qty)))
            except (TypeError, ValueError):
                continue
    person.job_times = normalized_times  # type: ignore[attr-defined]
    job_times: deque = person.job_times  # type: ignore[attr-defined]
    job_times.append((now.timestamp(), amount_of_lines))

    cutoff = (now - ROLLING_WINDOW).timestamp()
    while job_times and job_times[0][0] < cutoff:
        job_times.popleft()

    window_lines = sum(max(qty, 0) for ts, qty in job_times if ts >= cutoff)
    window_hours = ROLLING_WINDOW.total_seconds() / 3600 or 1
    person.speed = int(round(window_lines / window_hours))

    # 5) Activity & metadata
    person.jobs = (getattr(person, "jobs", 0) or 0) + amount_of_lines  # ✅ add number of lines
    person.last_seen = now
    person.idleSeconds = 0
    person.category = job_type
    person.comment = comment

    # 6) Update idleSeconds for others
    for p in db.people:
        if p is person or not getattr(p, "last_seen", None):
            continue
        p.idleSeconds = int((datetime.now(timezone.utc) - p.last_seen).total_seconds())

    # 7) Trim people list (most recent activity first)
    db.people.sort(
        key=lambda p: (getattr(p, "last_seen", None) or datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True,
    )
    db.people = db.people[:MAX_PEOPLE]

    # 8) KPI update
    calc_kpi_based_on_event(job_data, db)

    print(f"✅ Dashboard updated: {operator_name} ran '{job_type}' (#{job_id}) — +{amount_of_lines} lines")

    return {"status": "success", "job_id": job_id}
