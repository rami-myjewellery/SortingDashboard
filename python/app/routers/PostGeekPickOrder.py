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
from datadog_logger import log_datadog_event


router = APIRouter()

@router.post("/pubsub/geek-pickorder")
async def handle_geek_pickorder_push(request: Request):
    try:
        outer = await request.json()
    except Exception as exc:
        log_datadog_event(
            status="error",
            message=f"PubSub envelope not valid JSON: {exc}",
            event_type="geek.pickorder",
            function_name="handle_geek_pickorder_push",
        )
        raise HTTPException(status_code=400, detail=f"PubSub envelope not valid JSON: {exc}")

    # ---- Step 1: Pub/Sub base64 decode ----
    try:
        msg = outer.get("message", {})
        encoded = msg.get("data")
        if not encoded:
            raise ValueError("Missing 'message.data' field in Pub/Sub envelope")

        decoded_bytes = base64.b64decode(encoded)
        body = json.loads(decoded_bytes)

    except Exception as exc:
        log_datadog_event(
            status="error",
            message=f"Failed to decode Geek message.data: {exc}",
            event_type="geek.pickorder",
            function_name="handle_geek_pickorder_push",
        )
        raise HTTPException(status_code=400, detail=f"Failed to decode message.data: {exc}")

    # ---- Step 2: Extract Geek structure ----
    order_list = body.get("body", {}).get("order_list", [])
    first_order = order_list[0] if order_list else {}
    containers = first_order.get("container_list", [])
    first_container = containers[0] if containers else {}

    # Order-level SKU list
    order_sku_list = first_order.get("sku_list", []) or []

    # ---- Step 3: Determine NUMBER_OF_LINES ----
    number_of_lines = sum(
        1 for sku in order_sku_list
        if (sku.get("pickup_amount") or 0) > 0
    )

    # ---- Step 4: Common metadata ----
    job_id = first_order.get("out_order_code") or f"pick-{int(datetime.now(timezone.utc).timestamp())}"
    picker = first_container.get("picker") or "Unknown"
    warehouse = first_order.get("warehouse_code") or body.get("header", {}).get("warehouse_code")

    # ---- Step 5: job_data for dashboard ----
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
        "NUMBER_OF_LINES": number_of_lines,   # 🔥 the unified metric
    }

    update_result = await update_jobs_store_metric(job_data)

    now = datetime.now(timezone.utc).isoformat()

    log_datadog_event(
        status="ok",
        message=f"Geek PickOrder processed ({job_id})",
        event_type="geek.pickorder",
        function_name="handle_geek_pickorder_push",
        jobs_id=str(job_id),
        extra={
            "dashboard": "geek pickorders",
            "update": update_result,
            "number_of_lines": number_of_lines,
        },
    )

    print(f"✅ [Geek PickOrder] {job_id} at {now} -> NUMBER_OF_LINES={number_of_lines}")

    return {
        "status": "success",
        "job_id": job_id,
        "NUMBER_OF_LINES": number_of_lines,
        "dashboard": "geek pickorders",
    }
