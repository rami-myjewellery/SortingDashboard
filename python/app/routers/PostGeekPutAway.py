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

@router.post("/pubsub/geek-putaway")
async def handle_geek_putaway_push(request: Request):
    """
    Dedicated endpoint for Geek Putaways subscription.
    Robust to:
      - CloudEvents envelope at top-level
      - Google Pub/Sub push wrapper {"message": {...}}
      - base64 JSON at outer .data and at inner .data
      - Alternative WMS schema: {"body": {"receipt_list": [...]}, "header": {...}}
    """
    # 1) Parse request body ---------------------------------------------------
    try:
        body: Dict[str, Any] = await request.json()
    except Exception as exc:  # noqa: BLE001
        log_datadog_event(
            status="error",
            message=f"Body is not valid JSON: {exc}",
            event_type="geek.putaway",
            function_name="handle_geek_putaway_push",
        )
        raise HTTPException(status_code=400, detail=f"Body is not valid JSON: {exc}")

    if "message" in body and isinstance(body["message"], dict) and "data" in body["message"]:
        try:
            decoded_bytes = base64.b64decode(body["message"]["data"])
            inner_json = json.loads(decoded_bytes.decode("utf-8"))
        except Exception as exc:
            log_datadog_event(
                status="error",
                message=f"Failed to decode message.data: {exc}",
                event_type="geek.putaway",
                function_name="handle_geek_putaway_push",
            )
            raise HTTPException(status_code=400, detail=f"Failed to decode message.data: {exc}")
        # Merge header/body if present
        payload = inner_json
        receipt_list = payload.get("body", {}).get("receipt_list", [])
        receipt = receipt_list[0] if receipt_list else {}
        job_id = (
            receipt.get("receipt_code")
            or receipt.get("pallet_code")
            or str(receipt.get("id") or f"geek-{int(datetime.now(timezone.utc).timestamp())}")
        )
        qty = 0
        for rec in receipt_list:
            for sku in rec.get("sku_list", []) or []:
                try:
                    qty += int(sku.get("amount", 0) or 0)
                except Exception:
                    continue
        job_data: Dict[str, Any] = {
            "HEADER_ID": job_id,
            "EMPLOYEE_CODE": "Unknown",
            "HIGH_OVER_PROCESS": "GeekInbound",
            "RAW_GEEK": payload,
            "QUANTITY": max(qty, 1),
        }
        update_result = await update_jobs_store_metric(job_data)
        now = datetime.now(timezone.utc).isoformat()
        log_datadog_event(
            status="ok",
            message=f"Geek Putaway processed ({job_id})",
            event_type="geek.putaway",
            function_name="handle_geek_putaway_push",
            jobs_id=str(job_id) if job_id is not None else None,
            extra={"quantity": job_data["QUANTITY"], "update": update_result},
        )
        print(f"✅ [Geek Putaway-PubSub] {job_id} qty={job_data['QUANTITY']} at {now} update={update_result}")
        return {"status": "success", "job_id": job_id, "dashboard": "geek putaways", "quantity": job_data["QUANTITY"]}
