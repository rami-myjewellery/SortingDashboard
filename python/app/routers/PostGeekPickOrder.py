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

# ──────────────────────────────────────────────────────────────────────────────
# Decoding helpers
# ──────────────────────────────────────────────────────────────────────────────

def _try_b64_or_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            return json.loads(value.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Failed to parse bytes as JSON: {exc}")
    if isinstance(value, str):
        s = value.strip()
        try:
            decoded = base64.b64decode(s, validate=True)
            return json.loads(decoded.decode("utf-8"))
        except Exception:
            pass
        try:
            return json.loads(s)
        except Exception:
            return value
    return value


def _decode_geek_event(envelope: Dict[str, Any]) -> Dict[str, Any]:
    if "data" not in envelope:
        raise HTTPException(status_code=400, detail="Missing 'data' field in payload")

    outer = _try_b64_or_json(envelope["data"])
    if not isinstance(outer, dict):
        raise HTTPException(status_code=400, detail="Outer data is not a JSON object")

    if isinstance(outer.get("data"), str):
        inner_decoded = _try_b64_or_json(outer["data"])
        if isinstance(inner_decoded, dict):
            outer["data"] = inner_decoded

    return outer


# ──────────────────────────────────────────────────────────────────────────────
# ID helpers
# ──────────────────────────────────────────────────────────────────────────────

def _derive_header_id(decoded: Dict[str, Any], envelope: Dict[str, Any], body: Dict[str, Any]) -> str:
    uuid32 = decoded.get("uuid32")
    inner = decoded.get("data") or {}
    hd_num = inner.get("hd_number")
    return str(uuid32 or hd_num or envelope.get("id") or body.get("id") or f"geek-{int(datetime.now(timezone.utc).timestamp())}")


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/pubsub/pick-order")
async def handle_geek_putaway_push(request: Request):
    try:
        body: Dict[str, Any] = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Body is not valid JSON: {exc}")

    envelope: Dict[str, Any] = body.get("message") if isinstance(body.get("message"), dict) else body

    decoded = _decode_geek_event(envelope)

    inner = decoded.get("data") or {}
    job_id = _derive_header_id(decoded, envelope, body)

    job_data: Dict[str, Any] = {
        "HEADER_ID": job_id,
        # For now always Unknown (until employee_code is populated correctly)
        "EMPLOYEE_CODE": "Unknown",
        "HIGH_OVER_PROCESS": "geekInbound",
        "ORIGINAL_EVENT_TIME": body.get("time") or envelope.get("time") or decoded.get("create_timestamp"),
        "RAW_GEEK": decoded,
        "ACTION": body.get("action") or envelope.get("action"),
        "ACTIVITY": body.get("activity") or envelope.get("activity") or inner.get("activity_code"),
        "DEPOT": body.get("depot") or envelope.get("depot") or inner.get("physical_depot_code"),
        "LOGICAL_DEPOT": body.get("logicalDepot") or envelope.get("logicalDepot"),
    }

    update_result = await update_jobs_store_metric(job_data)

    now = datetime.now(timezone.utc).isoformat()
    print(
        f"✅ [Geek Putaway] {job_id} at {now} -> metrics={update_result} | update={update_result}"
    )

    return {"status": "success", "job_id": job_id, "dashboard": "geek putaways"}
