"""
Utilities to emit Datadog-friendly JSON logs with consistent metadata.
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

DATADOG_LOGGER_NAME = "datadog"


def _default_serializer(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc).isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, bytearray):
        return base64.b64encode(bytes(value)).decode("ascii")
    return value


@dataclass(slots=True)
class DatadogLog:
    status: str
    message: str
    event_type: str
    function_name: str
    jobs_id: Optional[str] = None
    variant_id: Optional[str] = None
    work_mode_code: Optional[str] = None
    trace_id: Optional[str] = None
    event_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "status": self.status,
            "message": self.message,
            "event_type": self.event_type,
            "function_name": self.function_name,
            "jobs_id": self.jobs_id,
            "variant_id": self.variant_id,
            "work_mode_code": self.work_mode_code,
            "trace_id": self.trace_id,
            "event_time": self.event_time,
        }
        payload.update(self.extra)
        return {key: value for key, value in payload.items() if value is not None}

    def log(self) -> str:
        payload = self.to_payload()
        serialized = json.dumps(payload, default=_default_serializer, separators=(",", ":"))
        logger = logging.getLogger(DATADOG_LOGGER_NAME)
        logger.info(serialized)
        print(serialized, flush=True)
        return serialized


def log_datadog_event(
    *,
    status: str,
    message: str,
    event_type: str,
    function_name: str,
    jobs_id: Optional[str] = None,
    variant_id: Optional[str] = None,
    work_mode_code: Optional[str] = None,
    trace_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Helper to quickly emit Datadog structured logs.
    """
    log_entry = DatadogLog(
        status=status,
        message=message,
        event_type=event_type,
        function_name=function_name,
        jobs_id=jobs_id,
        variant_id=variant_id,
        work_mode_code=work_mode_code,
        trace_id=trace_id,
        extra=extra or {},
    )
    return log_entry.log()
