import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException

from app.models import Dashboard, Kpi
from app.data.store import get_db
from app.services.manual_finish import get_manual_finish_metrics
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


# ── Next Day Progress (Mock dataset based on Reflex Dock Management) ────────
NEXT_DAY_LOADS = [
    {
        "id": "load-b2ceu",
        "load_code": "23/10/26 B2CEU",
        "carrier": "B2C Europe",
        "dock": "DOCK-003",
        "work_mode": "LOA - LOAD",
        "scheduling": "18h00 - 19h00",
        "scheduled_time": "18:00",
        "status": "Carrier expected",
        "picks_done": 94,
        "picks_total": 104,
        "picks_percentage": 90.4,
        "hds_loaded": 0,
        "hds_total": 48,
        "load_percentage": 0.0,
        "urgency": "critical",
    },
    {
        "id": "load-pnlpar",
        "load_code": "23/10/26 PNLPAR",
        "carrier": "PostNL Pakketten",
        "dock": "DOCK-003",
        "work_mode": "LOA - LOAD",
        "scheduling": "23h00 - 23h45",
        "scheduled_time": "23:00",
        "status": "Picking in progress",
        "picks_done": 582,
        "picks_total": 970,
        "picks_percentage": 60.0,
        "hds_loaded": 0,
        "hds_total": 64,
        "load_percentage": 0.0,
        "urgency": "warning",
    },
    {
        "id": "load-pnleur",
        "load_code": "23/10/26 PNLEUR",
        "carrier": "PostNL Europe",
        "dock": "DOCK-004",
        "work_mode": "LOA - LOAD",
        "scheduling": "23h00 - 23h45",
        "scheduled_time": "23:00",
        "status": "Picking in progress",
        "picks_done": 296,
        "picks_total": 510,
        "picks_percentage": 58.0,
        "hds_loaded": 0,
        "hds_total": 36,
        "load_percentage": 0.0,
        "urgency": "warning",
    },
    {
        "id": "load-dhlfy",
        "load_code": "23/10/26 DHLFY",
        "carrier": "DHL Parcel",
        "dock": "DOCK-005",
        "work_mode": "LOA - LOAD",
        "scheduling": "23h30 - 00h30",
        "scheduled_time": "23:30",
        "status": "Picking started",
        "picks_done": 145,
        "picks_total": 520,
        "picks_percentage": 27.9,
        "hds_loaded": 0,
        "hds_total": 42,
        "load_percentage": 0.0,
        "urgency": "upcoming",
    },
    {
        "id": "load-inthq",
        "load_code": "23/10/26 INTHQ",
        "carrier": "Internal HQ Transfer",
        "dock": "DOCK-008",
        "work_mode": "LOA - LOAD",
        "scheduling": "00h00 - 01h00",
        "scheduled_time": "00:00",
        "status": "Scheduled",
        "picks_done": 12,
        "picks_total": 150,
        "picks_percentage": 8.0,
        "hds_loaded": 0,
        "hds_total": 24,
        "load_percentage": 0.0,
        "urgency": "scheduled",
    },
]


@router.get("/NextDayProgress", response_model=Dashboard)
async def get_next_day_progress():
    total_picks_done = sum(l["picks_done"] for l in NEXT_DAY_LOADS)
    total_picks_target = sum(l["picks_total"] for l in NEXT_DAY_LOADS)
    total_hds_target = sum(l["hds_total"] for l in NEXT_DAY_LOADS)
    total_hds_loaded = sum(l["hds_loaded"] for l in NEXT_DAY_LOADS)
    remaining_picks = total_picks_target - total_picks_done
    remaining_hds = total_hds_target - total_hds_loaded
    overall_pick_pct = round((total_picks_done / total_picks_target * 100), 1) if total_picks_target else 0

    return Dashboard(
        title="Next Day Cut-Off & Loading",
        status="risk" if any(l["urgency"] == "critical" for l in NEXT_DAY_LOADS) else "good",
        kpis=[
            Kpi(label="Next Cut-off", value=18.0, unit="18:00 (B2CEU)"),
            Kpi(label="Open Picks", value=remaining_picks, unit="picks"),
            Kpi(label="Open HDs", value=remaining_hds, unit="HDs"),
            Kpi(label="Picks Ready", value=overall_pick_pct, unit="%"),
        ],
        historyText="Reflex Dock Management: Geordend van eerstvolgend naar later vertrekmoment",
        people=[],
        idleThreshold=60,
        loads=NEXT_DAY_LOADS,
    )
