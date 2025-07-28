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
from app.utils.jobExtractors.GetJobType import get_job_type
from app.utils.jobExtractors.JobMetricExtractor import extract_fma_metrics, extract_monopicking_metrics, \
    extract_inbound_and_bulk_metrics, extract_returns_metrics, extract_errorlanes_metrics
from app.utils.jobExtractors.UpdateJobsStoreMetrics import update_jobs_store_metric

router = APIRouter()

# ── Input contract ───────────────────────────────────────────────────────────
class PubSubMessage(BaseModel):
    message: Dict[str, Any]
    subscription: str




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
    comment       = job_data.get("comment", "").strip()   # Change here
    operator_name = job_data.get("EMPLOYEE_CODE", "").strip() or "Unknown"
    now           = datetime.now(timezone.utc)
    job_type = get_job_type(comment)  # Get the job type based on comment

    # 3) Define a dictionary to map job types to their respective metric extractor functions
    job_type_to_extractor = {
        "FMA": extract_fma_metrics,
        "MonoPicking": extract_monopicking_metrics,
        "InboundAndBulk": extract_inbound_and_bulk_metrics,
        "Returns": extract_returns_metrics,
        "ErrorLanes": extract_errorlanes_metrics
    }

    # 4) Call the appropriate metric extraction function based on job type
    extractor_function = job_type_to_extractor.get(job_type)

    if not extractor_function:
        raise HTTPException(status_code=400, detail=f"Unsupported job type: {job_type}")

    job_metrics = await extractor_function(job_data)

    # 6) Update the job metrics in the store (for the correct job type and dashboard)
    update_result = await update_jobs_store_metric(job_data)  # Update the store with job data

    print(f"✅ Job {job_id} processed with metrics: {job_metrics}")
    return {"status": "success", "job_id": job_id}