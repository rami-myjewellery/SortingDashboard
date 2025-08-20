"""
FastAPI router for Geek Putaways Pub/Sub subscription.
- Robustly decodes CloudEvents-style payloads where the outer `data` is base64 JSON
  and the inner `data` may ALSO be base64 JSON (double-encoded).
- Adapts the decoded payload into the existing job_data shape and routes it to the
  'geek putaways' dashboard via update_jobs_store_metric.
- For now, all operators are set to 'Unknown' until employee codes are reliably provided.

Mount example in app/main.py:
    from app.api.geek_putaway_router import router as geek_putaway_router
    app.include_router(geek_putaway_router, prefix="/actions")

Final URL in that case: /actions/pubsub/geek-putaway
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from app.utils.jobExtractors.UpdateJobsStoreMetrics import (
    update_jobs_store_metric,
)

router = APIRouter()
@router.post("/pubsub/geek-pickorder")
async def handle_geek_pickorder_push(request: Request):
    try:
        body: Dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Body is not valid JSON: {exc}")

    # Navigate into the structure
    order_list = body.get("body", {}).get("order_list", [])
    first_order = order_list[0] if order_list else {}
    containers = first_order.get("container_list", [])
    first_container = containers[0] if containers else {}

    # Extract useful fields
    job_id = first_order.get("out_order_code") or f"pick-{int(datetime.now(timezone.utc).timestamp())}"
    picker = first_container.get("picker") or "Unknown"
    warehouse = first_order.get("warehouse_code") or body.get("header", {}).get("warehouse_code")

    job_data: Dict[str, Any] = {
        "HEADER_ID": job_id,
        "EMPLOYEE_CODE": picker,
        "HIGH_OVER_PROCESS": "GeekPicking",
        "ORIGINAL_EVENT_TIME": first_order.get("finish_date"),
        "RAW_GEEK": body,
        "ACTION": "feedback_outbound_order",
        "ACTIVITY": "pickorder",
        "DEPOT": warehouse,
        "LOGICAL_DEPOT": None,
    }

    update_result = await update_jobs_store_metric(job_data)

    now = datetime.now(timezone.utc).isoformat()
    print(f"✅ [Geek PickOrder] {job_id} at {now} -> metrics={update_result}")

    return {"status": "success", "job_id": job_id, "dashboard": "geek pickorders"}
