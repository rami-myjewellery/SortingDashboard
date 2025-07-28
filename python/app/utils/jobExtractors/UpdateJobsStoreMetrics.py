from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any

from app.utils.MainUtils import get_or_create_person
from app.data.store import get_db
from app.utils.jobExtractors.GetJobType import get_job_type
# ── Parameters ───────────────────────────────────────────────────────────────
WINDOW   = timedelta(seconds=60)   # size of the rolling window
MAX_APM  = 100                     # full-bar value

# Update the job metrics in the store based on the correct job type and dashboard
async def update_jobs_store_metric(job_data: Dict[str, Any]) -> Dict[str, Any]:
    # Extract required information from the job data
    job_id = job_data.get("HEADER_ID")
    comment = job_data.get("comment", "").strip()
    operator_name = job_data.get("EMPLOYEE_CODE", "").strip() or "Unknown"
    job_type = get_job_type(comment)  # Get the job type based on the comment
    now = datetime.now()

    # 1) Get the dashboard corresponding to the job type ----------------------------------
    db = get_db().get(
        job_type.lower())  # Fetch the correct dashboard based on job_type (e.g., 'fma', 'monopicking', etc.)

    if not db:
        return {"status": "error", "detail": f"Dashboard for job type '{job_type}' not found."}

    # 2) Get or create the operator record ----------------------------------
    person = get_or_create_person(db.people, operator_name, job_type, comment)

    # 3) Make sure the rolling deque exists -----------------------------------
    if not hasattr(person, "job_times"):
        person.job_times = deque(maxlen=MAX_APM)  # type: ignore[attr-defined]

    job_times: deque = person.job_times  # type: ignore[attr-defined]

    # 4) Record the new action -------------------------------------------------
    job_times.append(now.timestamp())

    # (optional) prune anything older than WINDOW just to keep the deque tidy
    cutoff = (now - WINDOW).timestamp()
    while job_times and job_times[0] < cutoff:
        job_times.popleft()

    # 5) Reset activity bar to 100 -------------------------------------------
    person.speed = MAX_APM

    # 6) Book-keeping ----------------------------------------------------------
    person.jobs += 1
    person.last_seen = now
    person.idleSeconds = 0
    person.category = job_type  # Add category to person record
    person.comment = comment  # Add comment to person record

    # 7) Update other operators' idle times ---------------------------------
    for p in db.people:
        if p is person or not p.last_seen:
            continue
        p.idleSeconds = int((now - p.last_seen).total_seconds())

    # 8) Keep only the five most-recent operators -----------------------------
    db.people.sort(key=lambda p: p.last_seen or now, reverse=True)
    db.people = db.people[:5]

    print(f"✅ Dashboard updated: {operator_name} ran '{job_type}' (#{job_id})")

    return {"status": "success", "job_id": job_id}
