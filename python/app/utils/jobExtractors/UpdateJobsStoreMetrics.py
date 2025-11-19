from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any

from app.utils.MainUtils import get_or_create_person
from app.data.store import get_db
from datetime import timezone
# ── Parameters ───────────────────────────────────────────────────────────────
WINDOW = timedelta(seconds=60)   # size of the rolling window
MAX_APM = 100                    # full-bar value

# ── KPI Update Function ──────────────────────────────────────────────────────
def calc_kpi_based_on_event(job_data: Dict[str, Any], dashboard: Any) -> None:
    """
    Increments dashboard KPIs by the quantity in job_data (default 1 if missing):
    - total items processed today
    - items processed per hour
    """
    now = datetime.now(timezone.utc)

    # Extract quantity from job_data
    inner = job_data.get("RAW_GEEK", {}).get("data", {})
    ipg_list = inner.get("ipg_list", [])
    if isinstance(ipg_list, list) and ipg_list:
        qty = sum(int(item.get("base_lv_quantity", 1)) for item in ipg_list)
    else:
        qty = 1  # fallback if ipg_list missing/empty

    # Initialize tracking if not set
    if getattr(dashboard, "kpi_state", None) is None:
        dashboard.kpi_state = {
            "date": now.date(),
            "total": 0,
            "first_event_time": now
        }

    state = dashboard.kpi_state

    # Reset for new day
    if state["date"] != now.date():
        state["date"] = now.date()
        state["total"] = 0
        state["first_event_time"] = now

    # Increment by quantity (instead of +1)
    state["total"] += qty

    # Calculate items/hr
    hours_elapsed = max((now - state["first_event_time"]).total_seconds() / 3600, 1/60)
    per_hour = state["total"] / hours_elapsed

    # Assign to KPIs (assume [0] = per hour, [1] = today)
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

    # 3) Ensure rolling window
    if not hasattr(person, "job_times"):
        person.job_times = deque(maxlen=MAX_APM)  # type: ignore[attr-defined]

    job_times: deque = person.job_times  # type: ignore[attr-defined]
    job_times.append(now.timestamp())

    # 4) Prune old timestamps
    cutoff = (now - WINDOW).timestamp()
    while job_times and job_times[0] < cutoff:
        job_times.popleft()

    # Helper: coerce a value to a non-negative integer, with default
    def _coerce_lines(val, default=1) -> int:
        # Prefer LINE_COUNT, then amount_of_lines; keep default=1 to mimic old +1 behavior when missing
        try:
            if val is None:
                return default
            # allow strings like "7"
            num = int(float(val))
            return max(0, num)  # no negative increments
        except Exception:
            return default

    # Determine how many lines to add
    amount_of_lines = _coerce_lines(
        job_data.get("AMOUNT_OF_LINES", None) if "AMOUNT_OF_LINES" in job_data else job_data.get("AMOUNT_OF_LINES", None),
        default=1
    )

    # 5) Activity & metadata
    person.speed = MAX_APM
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

    # 7) Trim people list
    db.people.sort(
        key=lambda p: (
            -int(getattr(p, "idleSeconds", 0)),  # primary: idle seconds (desc)
            (getattr(p, "last_seen", None) or datetime.min.replace(tzinfo=timezone.utc)),  # tie-breaker
        )
    )
    db.people = db.people[:5]

    # 8) KPI update
    calc_kpi_based_on_event(job_data, db)

    print(f"✅ Dashboard updated: {operator_name} ran '{job_type}' (#{job_id}) — +{amount_of_lines} lines")

    return {"status": "success", "job_id": job_id}
