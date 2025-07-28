# app/routers/PostSortingActionToDashboard.py
# ─────────────────────────────────────────────────────────────────────────────
#  • Decodes Pub/Sub messages coming from GCP
#  • Keeps a 60-second deque of job timestamps per operator
#  • “speed” is the activity-bar value: it jumps to 100 on an action and
#    drifts down elsewhere (via the heartbeat task)
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import base64
import json
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.data.store import get_db
from app.models import Person
from app.utils.MainUtils import get_or_create_person

router = APIRouter()

# ── Input contract ───────────────────────────────────────────────────────────
class PubSubMessage(BaseModel):
    message: Dict[str, Any]
    subscription: str

# ── Parameters ───────────────────────────────────────────────────────────────
WINDOW   = timedelta(seconds=60)   # size of the rolling window
MAX_APM  = 100                     # full-bar value
# ── Endpoint ─────────────────────────────────────────────────────────────────
@router.post("/pubsub/jobs-action")
async def handle_pubsub_push(pubsub_msg: PubSubMessage):
    # 1) Decode Pub/Sub payload ------------------------------------------------
    try:
        data_b64: str = pubsub_msg.message.get("data", "")
        decoded_json  = base64.b64decode(data_b64).decode("utf-8")
        job_data: Dict[str, Any] = json.loads(decoded_json)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to decode Pub/Sub payload: {exc}",
        )

    # 2) Extract useful fields -------------------------------------------------
    job_id        = job_data.get("HEADER_ID")
    category      = job_data.get("category", "").strip()  # Change here
    comment       = job_data.get("comment", "").strip()   # Change here
    operator_name = job_data.get("EMPLOYEE_CODE", "").strip() or "Unknown"
    now           = datetime.now(timezone.utc)

    # 3) Locate / create the operator record ----------------------------------
    db                = get_db()["default"]
    person: Person    = get_or_create_person(db.people, operator_name, category , comment  )  # Change here

    # 4) Make sure the rolling deque exists -----------------------------------
    if not hasattr(person, "job_times"):
        person.job_times = deque(maxlen=MAX_APM)   # type: ignore[attr-defined]

    job_times: deque = person.job_times            # type: ignore[attr-defined]

    # 5) Record the new action -------------------------------------------------
    job_times.append(now.timestamp())

    # (optional) prune anything older than WINDOW just to keep the deque tidy
    cutoff = (now - WINDOW).timestamp()
    while job_times and job_times[0] < cutoff:
        job_times.popleft()

    # ——— Reset activity bar to 100 ———
    person.speed = MAX_APM

    # 6) Book-keeping ----------------------------------------------------------
    person.jobs       += 1
    person.last_seen   = now
    person.idleSeconds = 0
    person.category = category  # Add category to person record
    person.comment = comment    # Add comment to person record

    for p in db.people:
        if p is person or not p.last_seen:
            continue
        p.idleSeconds = int((now - p.last_seen).total_seconds())

    # 7) Keep only the five most-recent operators -----------------------------
    db.people.sort(key=lambda p: p.last_seen or now, reverse=True)
    db.people = db.people[:5]

    print(f"✅ Dashboard updated: {operator_name} ran '{category}' (#{job_id})")
    return {"status": "success", "job_id": job_id}
