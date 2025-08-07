from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any

from app.utils.MainUtils import get_or_create_person
from app.data.store import get_db
from app.utils.jobExtractors.GetJobType import get_job_type
from datetime import timezone
# ── Parameters ───────────────────────────────────────────────────────────────
WINDOW = timedelta(seconds=60)   # size of the rolling window
MAX_APM = 100                    # full-bar value

# ── KPI Update Function ──────────────────────────────────────────────────────
def calc_kpi_based_on_event(job_data: Dict[str, Any], dashboard: Any) -> None:
    """
    Increments dashboard KPIs by 1 per job event:
    - total items processed today
    - items processed per hour
    """
    now = datetime.now(timezone.utc)

    # Initialize tracking if not set
    if dashboard.kpi_state is None:
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

    # +1 per event
    state["total"] += 1

    # Calculate items/hr
    hours_elapsed = max((now - state["first_event_time"]).total_seconds() / 3600, 1/60)
    per_hour = state["total"] / hours_elapsed

    # Assign to KPIs
    dashboard.kpis[0].value = state["total"]
    dashboard.kpis[1].value = round(per_hour, 0)


# ── Main Update Function ─────────────────────────────────────────────────────
async def update_jobs_store_metric(job_data: Dict[str, Any]) -> Dict[str, Any]:
    # Extract required information
    job_id = job_data.get("HEADER_ID")
    comment = job_data.get("comment", "").strip()
    operator_name = job_data.get("EMPLOYEE_CODE", "").strip() or "Unknown"
    job_type = get_job_type(comment)
    now = datetime.now(timezone.utc)

    job_data["job_type"] = job_type

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

    # 5) Activity & metadata
    person.speed = MAX_APM
    person.jobs += 1
    person.last_seen = now
    person.idleSeconds = 0
    person.category = job_type
    person.comment = comment

    # 6) Update idleSeconds for others
    for p in db.people:
        if p is person or not p.last_seen:
            continue
        p.idleSeconds = int((datetime.now(timezone.utc) - p.last_seen).total_seconds())

    # 7) Trim people list
    db.people.sort(key=lambda p: p.last_seen or now, reverse=True)
    db.people = db.people[:5]

    # 8) KPI update
    calc_kpi_based_on_event(job_data, db)

    print(f"✅ Dashboard updated: {operator_name} ran '{job_type}' (#{job_id})")

    return {"status": "success", "job_id": job_id}
