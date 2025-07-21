from copy import deepcopy
from typing import Dict

from fastapi import APIRouter, HTTPException, Query

from app.models import Dashboard, Kpi
from app.data.store import get_db, _tick_lock

router = APIRouter()

# ---------------------------------------------------------------------------
# 1.  A BASE TEMPLATE every endpoint starts from
# ---------------------------------------------------------------------------
_BASE = Dashboard(
    title="Sorting",
    status="good",
    kpis=[
        Kpi(label="Error belt filling level",  value=0, unit="packages"),
        Kpi(label="Single belt filling level", value=0, unit="packages"),
        Kpi(label="Multi belt filling level",  value=0, unit="packages"),
    ],
    historyText="",
    people=[],
    idleThreshold=60,
)

# ---------------------------------------------------------------------------
# 2.  Endpoint-specific patches  (title, extra KPIs, etc.)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 2.  Endpoint-specific patches  – title + KPI overrides
# ---------------------------------------------------------------------------
PATCHES: Dict[str, Dict] = {
    "GeekPicking": {
        "title": "Geek Picking",
        "kpis": [
            Kpi(label="Picks per hour",           value=0, unit="items/h"),
            Kpi(label="Picking accuracy",         value=0, unit="%"),
            Kpi(label="Open pick lines",          value=0, unit="orders"),
        ],
    },
    "GeekInbound": {
        "title": "Geek Inbound",
        "kpis": [
            Kpi(label="Parcels received",         value=0, unit="parcels"),
            Kpi(label="Put-away backlog",         value=0, unit="parcels"),
            Kpi(label="Average unload time",      value=0, unit="min"),
        ],
    },
    "ErrorLanes": {
        "title": "Error Handling",
        "kpis": [
            Kpi(label="Error belt fill level",    value=0, unit="packages"),
            Kpi(label="Mis-sorts per hour",       value=0, unit="items/h"),
            Kpi(label="Blocked chutes",           value=0, unit="chutes"),
        ],
    },
    "FMA": {
        "title": "FMA Pick & Pack",
        "kpis": [
            Kpi(label="Orders packed",            value=0, unit="orders"),
            Kpi(label="Packing speed",            value=0, unit="orders/h"),
            Kpi(label="Packing accuracy",         value=0, unit="%"),
        ],
    },
    "Sorting": {
        "title": "Sorter Overview",
        "kpis": [
            Kpi(label="Error belt filling level", value=0, unit="packages"),
            Kpi(label="Single belt filling level", value=0, unit="packages"),
            Kpi(label="Multi belt filling level", value=0, unit="packages"),
        ],
    },
    "MonoPicking": {
        "title": "Mono Picking",
        "kpis": [
            Kpi(label="Mono picks per hour",      value=0, unit="items/h"),
            Kpi(label="Open mono orders",         value=0, unit="orders"),
            Kpi(label="Picking accuracy",         value=0, unit="%"),
        ],
    },
    "InboundAndBulk": {
        "title": "Inbound & Bulk Handling",
        "kpis": [
            Kpi(label="Bulk pallets processed",   value=0, unit="pallets"),
            Kpi(label="Receiving backlog",        value=0, unit="pallets"),
            Kpi(label="Avg pallet wait time",     value=0, unit="min"),
        ],
    },
    "Returns": {
        "title": "Returns",
        "kpis": [
            Kpi(label="Returns processed",        value=0, unit="items"),
            Kpi(label="Return backlog",           value=0, unit="items"),
            Kpi(label="Disposition rate",         value=0, unit="%"),
        ],
    },
}


# ---------------------------------------------------------------------------
# Endpoints – all using the same algorithm
# ---------------------------------------------------------------------------
@router.get("/GeekPicking", response_model=Dashboard)
def get_geek_picking(profile: str = Query("default")):
    db: Dict[str, Dashboard] = get_db()
    patch = PATCHES.get("GeekPicking")
    if not patch:
        raise HTTPException(status_code=404, detail="No patch for endpoint")

    db[profile].status = patch["good"]
    db[profile].title = patch["title"]
    db[profile].kpis = patch["kpis"]
    return db[profile]


@router.get("/GeekInbound", response_model=Dashboard)
def get_geek_inbound(profile: str = Query("default")):
    db: Dict[str, Dashboard] = get_db()
    patch = PATCHES.get("GeekInbound")
    if not patch:
        raise HTTPException(status_code=404, detail="No patch for endpoint")

    db[profile].status = patch["good"]
    db[profile].title = patch["title"]
    db[profile].kpis = patch["kpis"]
    return db[profile]


@router.get("/ErrorLanes", response_model=Dashboard)
def get_error_lanes(profile: str = Query("default")):
    db: Dict[str, Dashboard] = get_db()
    patch = PATCHES.get("ErrorLanes")
    if not patch:
        raise HTTPException(status_code=404, detail="No patch for endpoint")

    db[profile].status = patch["good"]
    db[profile].title = patch["title"]
    db[profile].kpis = patch["kpis"]
    return db[profile]


@router.get("/FMA", response_model=Dashboard)
def get_fma(profile: str = Query("default")):
    db: Dict[str, Dashboard] = get_db()
    patch = PATCHES.get("FMA")
    if not patch:
        raise HTTPException(status_code=404, detail="No patch for endpoint")

    db[profile].status = patch["good"]
    db[profile].title = patch["title"]
    db[profile].kpis = patch["kpis"]
    return db[profile]


@router.get("/Sorting", response_model=Dashboard)
def get_sorting(profile: str = Query("default")):
    db: Dict[str, Dashboard] = get_db()
    patch = PATCHES.get("Sorting")
    if not patch:
        raise HTTPException(status_code=404, detail="No patch for endpoint")

    db[profile].title = patch["title"]
    db[profile].kpis = patch["kpis"]
    return db[profile]


@router.get("/MonoPicking", response_model=Dashboard)
def get_mono_picking(profile: str = Query("default")):
    db: Dict[str, Dashboard] = get_db()
    patch = PATCHES.get("MonoPicking")
    if not patch:
        raise HTTPException(status_code=404, detail="No patch for endpoint")
    
    db[profile].status = patch["good"]
    db[profile].title = patch["title"]
    db[profile].kpis = patch["kpis"]
    return db[profile]


@router.get("/InboundAndBulk", response_model=Dashboard)
def get_inbound_bulk(profile: str = Query("default")):
    db: Dict[str, Dashboard] = get_db()
    patch = PATCHES.get("InboundAndBulk")
    if not patch:
        raise HTTPException(status_code=404, detail="No patch for endpoint")
    db[profile].status = patch["good"]
    db[profile].title = patch["title"]
    db[profile].kpis = patch["kpis"]
    return db[profile]


@router.get("/Returns", response_model=Dashboard)
def get_returns(profile: str = Query("default")):
    db: Dict[str, Dashboard] = get_db()
    patch = PATCHES.get("Returns")
    if not patch:
        raise HTTPException(status_code=404, detail="No patch for endpoint")

    db[profile].status = patch["good"]
    db[profile].title = patch["title"]
    db[profile].kpis = patch["kpis"]
    return db[profile]