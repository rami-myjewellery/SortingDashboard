from copy import deepcopy
from typing import Dict

from fastapi import APIRouter, HTTPException, Query
from app.models import Dashboard, Kpi
from app.data.store import get_db

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
            Kpi(label="Parcels sorted",           value=0, unit="parcels"),
            Kpi(label="Sorter utilisation",       value=0, unit="%"),
            Kpi(label="Active destinations",      value=0, unit="lanes"),
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
# 3.  Helper that applies a patch and stores the snapshot in _db
# ---------------------------------------------------------------------------
def _snapshot(mode: str, profile: str = "default") -> Dashboard:
    db: Dict[str, Dashboard] = get_db()

    if mode not in PATCHES:
        raise HTTPException(status_code=404, detail="unknown mode")

    # start from a fresh copy of the base template
    dash = deepcopy(_BASE)

    # apply the endpoint-specific changes
    for field, value in PATCHES[mode].items():
        setattr(dash, field, value)

    # store / overwrite
    db[profile + ":" + mode] = dash
    return dash

# ---------------------------------------------------------------------------
# 4.  Eight GET endpoints – one liner each
# ---------------------------------------------------------------------------
@router.get("/GeekPicking",    response_model=Dashboard)
def get_geek_picking(profile: str = Query("default")):
    return _snapshot("GeekPicking", profile)

@router.get("/GeekInbound",    response_model=Dashboard)
def get_geek_inbound(profile: str = Query("default")):
    return _snapshot("GeekInbound", profile)

@router.get("/ErrorLanes",     response_model=Dashboard)
def get_error_lanes(profile: str = Query("default")):
    return _snapshot("ErrorLanes", profile)

@router.get("/FMA",            response_model=Dashboard)
def get_fma(profile: str = Query("default")):
    return _snapshot("FMA", profile)

@router.get("/Sorting",        response_model=Dashboard)
def get_sorting(profile: str = Query("default")):
    return _snapshot("Sorting", profile)

@router.get("/MonoPicking",    response_model=Dashboard)
def get_mono_picking(profile: str = Query("default")):
    return _snapshot("MonoPicking", profile)

@router.get("/InboundAndBulk", response_model=Dashboard)
def get_inbound_bulk(profile: str = Query("default")):
    return _snapshot("InboundAndBulk", profile)

@router.get("/Returns",        response_model=Dashboard)
def get_returns(profile: str = Query("default")):
    return _snapshot("Returns", profile)
