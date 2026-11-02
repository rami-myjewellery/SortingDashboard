import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException

from app.models import Dashboard, Kpi
from app.data.store import get_db
from app.services.manual_finish import get_manual_finish_metrics
from app.services.next_day_progress import get_next_day_loads
from datadog_logger import log_datadog_event

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# 1.  A BASE TEMPLATE for the dashboards
# ---------------------------------------------------------------------------
_BASE = Dashboard(
    title="Sorting",
    status="good",
    kpis=[
        Kpi(label="Error belt filling level", value=0, unit="packages"),
        Kpi(label="Single belt filling level", value=0, unit="packages"),
        Kpi(label="Multi belt filling level", value=0, unit="packages"),
    ],
    historyText="",
    people=[],
    idleThreshold=60,
)

# ---------------------------------------------------------------------------
# 2.  Endpoint-specific patches – title + KPI overrides
# ---------------------------------------------------------------------------
PATCHES: Dict[str, Dict] = {
    "GeekPicking": {
        "title": "Geek Picking",
        "kpis": [
            Kpi(label="Picking Speed", value=0, unit="lines/sec"),
            Kpi(label="Lines Processed", value=0, unit="cartons"),
            Kpi(label="Pick Efficiency", value=0, unit="%"),
        ],
    },
    "GeekInbound": {
        "title": "Geek Inbound",
        "kpis": [
            Kpi(label="Inbound Volume", value=0, unit="m³"),
            Kpi(label="Item Count", value=0, unit="items"),
            Kpi(label="Handling Units Processed", value=0, unit="units"),
        ],
    },
    "ErrorLanes": {
        "title": "Error Handling",
        "kpis": [
            Kpi(label="Error Rate", value=0, unit="%"),
            Kpi(label="Handled Errors", value=0, unit="errors"),
            Kpi(label="Unresolved Errors", value=0, unit="errors"),
        ],
    },
    "FMA": {
        "title": "FMA Pick & Pack",
        "kpis": [
            Kpi(label="Packing Speed", value=0, unit="items/sec"),
            Kpi(label="Units Packed", value=0, unit="units"),
            Kpi(label="Volume Processed", value=0, unit="m³"),
        ],
    },
    "MonoPicking": {
        "title": "Mono Picking",
        "kpis": [
            Kpi(label="Picking Time per Item", value=0, unit="sec/item"),
            Kpi(label="Mono Units Processed", value=0, unit="units"),
            Kpi(label="Mono Efficiency", value=0, unit="%"),
        ],
    },
    "InboundAndBulk": {
        "title": "Inbound & Bulk Handling",
        "kpis": [
            Kpi(label="Bulk Units Processed", value=0, unit="units"),
            Kpi(label="Bulk Volume", value=0, unit="m³"),
            Kpi(label="Processing Time", value=0, unit="sec"),
        ],
    },
    "Returns": {
        "title": "Returns",
        "kpis": [
            Kpi(label="Return Volume", value=0, unit="m³"),
            Kpi(label="Returns Processed", value=0, unit="items"),
            Kpi(label="Return Processing Time", value=0, unit="sec"),
        ],
    },
}

# ── Manual finish tile configuration ────────────────────────────────────────
@dataclass(frozen=True)
class ManualFinishTileConfig:
    metric: str
    label: str
    unit: str = "jobs"


MANUAL_FINISH_TILES: Dict[str, ManualFinishTileConfig] = {
    # Only Pick & GeekPicking dashboards receive the manual-finish queue tile.
    "pick": ManualFinishTileConfig(metric="fma", label="Waiting carts (FMA)", unit="carts"),
    "geekpicking": ManualFinishTileConfig(metric="geek", label="Waiting carts (Geek)", unit="carts"),
}


async def _build_dashboard_response(store_key: str) -> Dashboard:
    """
    Create an isolated snapshot of the dashboard, enrich it with manual finish
    metrics (if configured), and return it to the caller.
    """
    db = get_db()
    if store_key not in db:
        log_datadog_event(
            status="error",
            message=f"Dashboard '{store_key}' not found",
            event_type="dashboard.fetch",
            function_name="_build_dashboard_response",
            extra={"store_key": store_key},
        )
        raise HTTPException(status_code=404, detail=f"Dashboard '{store_key}' not found.")

    dashboard = deepcopy(db[store_key])
    await _inject_manual_finish_tile(store_key, dashboard)
    log_datadog_event(
        status="ok",
        message=f"Dashboard '{store_key}' served",
        event_type="dashboard.fetch",
        function_name="_build_dashboard_response",
        extra={"store_key": store_key, "kpi_count": len(dashboard.kpis)},
    )
    return dashboard


async def _inject_manual_finish_tile(store_key: str, dashboard: Dashboard) -> None:
    config: Optional[ManualFinishTileConfig] = MANUAL_FINISH_TILES.get(store_key)
    if not config:
        return

    try:
        metrics = await get_manual_finish_metrics()
    except Exception as exc:  # pragma: no cover - defensive logging path
        # Keep dashboard functional even when the upstream metric is unavailable.
        logger.warning("manual-finish metrics unavailable for '%s': %s", store_key, exc)
        log_datadog_event(
            status="error",
            message=f"manual-finish metrics unavailable: {exc}",
            event_type="manual_finish.tile",
            function_name="_inject_manual_finish_tile",
            extra={"store_key": store_key},
        )
        return

    value = getattr(metrics, config.metric, None)
    if value is None:
        return

    dashboard.kpis.append(Kpi(label=config.label, value=value, unit=config.unit))
    log_datadog_event(
        status="ok",
        message="manual-finish tile updated",
        event_type="manual_finish.tile",
        function_name="_inject_manual_finish_tile",
        extra={"store_key": store_key, "metric": config.metric, "value": value},
    )


# ---------------------------------------------------------------------------
# Endpoints for each category dashboard
# ---------------------------------------------------------------------------

@router.get("/GeekPicking", response_model=Dashboard)
async def get_geek_picking():
    return await _build_dashboard_response("geekpicking")

@router.get("/GeekInbound", response_model=Dashboard)
async def get_geek_inbound():
    return await _build_dashboard_response("geekinbound")

@router.get("/Replenishment", response_model=Dashboard)
async def get_replenishment():
    # Use the live dashboard from the in-memory DB for "FMA"
    return await _build_dashboard_response("replenishment")

@router.get("/Picking", response_model=Dashboard)
async def get_mono_picking():
    # Use the live dashboard from the in-memory DB for "MonoPicking"
    return await _build_dashboard_response("pick")

@router.get("/InboundAndBulk", response_model=Dashboard)
async def get_inbound_bulk():
    # Use the live dashboard from the in-memory DB for "InboundAndBulk"
    return await _build_dashboard_response("inbound")

@router.get("/Returns", response_model=Dashboard)
async def get_returns():
    # Use the live dashboard from the in-memory DB for "Returns"
    return await _build_dashboard_response("returns")

@router.get("/ErrorLanes", response_model=Dashboard)
async def get_error_lanes():
    # Use the live dashboard from the in-memory DB for "ErrorLanes"
    return await _build_dashboard_response("error lane")

@router.get("/Sorting", response_model=Dashboard)
async def get_sorting():
    # Use the live dashboard from the in-memory DB
    return await _build_dashboard_response("default")


# ── Next Day Progress (Live Reflex query for PNLMAI, PNLPAR, DHLFY) ─────────
def _compute_next_day_status(loads: list[dict]) -> str:
    """
    Determine dashboard status ('good', 'risk', 'bad') based on the earliest
    upcoming pickup moment (including all loads sharing that same earliest time):
      - Groen ('good'): > 85%
      - Oranje ('risk'): 50% - 85%
      - Rood ('bad'): < 50%
    """
    if not loads:
        return "good"

    def _norm_time(t: str) -> int:
        parts = t.split(":")
        h = int(parts[0]) if parts else 0
        m = int(parts[1]) if len(parts) > 1 else 0
        return (h + 24) * 60 + m if h < 6 else h * 60 + m

    sorted_loads = sorted(loads, key=lambda l: _norm_time(str(l.get("scheduled_time", "00:00"))))
    earliest_time = sorted_loads[0].get("scheduled_time")
    earliest_group = [l for l in sorted_loads if l.get("scheduled_time") == earliest_time]

    active_group = [l for l in earliest_group if int(l.get("picks_total", 0)) > 0] or earliest_group
    min_pct = min(float(l.get("pick_pct", l.get("picks_percentage", 0))) for l in active_group)
    if min_pct > 85:
        return "good"
    if min_pct >= 50:
        return "risk"
    return "bad"


@router.get("/NextDayProgress", response_model=Dashboard)
async def get_next_day_progress():
    loads = await get_next_day_loads()
    total_picks_confirmed = sum(int(l.get("picks_confirmed", l.get("picks_done", 0))) for l in loads)
    total_picks_target = sum(int(l.get("picks_total", 0)) for l in loads)
    remaining_picks = max(0, total_picks_target - total_picks_confirmed)
    first_load = loads[0] if loads else {}
    status = _compute_next_day_status(loads)

    first_name = first_load.get("load_designation") or first_load.get("load_code") or "—"
    first_time = first_load.get("scheduled_time") or "—"
    first_dock = first_load.get("dock") or "—"

    return Dashboard(
        title="Next Day Progress",
        status=status,
        kpis=[
            Kpi(label="Openstaande Picks", value=remaining_picks, unit="picks"),
            Kpi(label="Geconfirmde Picks", value=total_picks_confirmed, unit="picks"),
        ],
        historyText=f"Eerstvolgende load: {first_time} · {first_name} ({first_dock})",
        people=[],
        idleThreshold=60,
        loads=loads,
    )
