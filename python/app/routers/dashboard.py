from copy import deepcopy
from typing import Dict

from fastapi import APIRouter, HTTPException

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
# 2.  Endpoint-specific patches – title + KPI overrides
# ---------------------------------------------------------------------------
PATCHES: Dict[str, Dict] = {
    "GeekPicking": {
        "title": "Geek Picking",
        "kpis": [
            Kpi(label="Comming Soon", value=0, unit="wat"),
            Kpi(label="Weet jij een Metric?", value=0, unit="denk"),
            Kpi(label="Deel het met ons", value=0, unit="jij?"),
        ],
    },
    "GeekInbound": {
        "title": "Geek Inbound",
        "kpis": [
            Kpi(label="Parcels received", value=0, unit="parcels"),
            Kpi(label="Put-away backlog", value=0, unit="parcels"),
            Kpi(label="Average unload time", value=0, unit="min"),
        ],
    },
    "ErrorLanes": {
        "title": "Error Handling",
        "kpis": [
            Kpi(label="Error belt fill level", value=0, unit="packages"),
            Kpi(label="Mis-sorts per hour", value=0, unit="items/h"),
            Kpi(label="Blocked chutes", value=0, unit="chutes"),
        ],
    },
    "FMA": {
        "title": "FMA Pick & Pack",
        "kpis": [
            Kpi(label="Orders packed", value=0, unit="orders"),
            Kpi(label="Packing speed", value=0, unit="orders/h"),
            Kpi(label="Packing accuracy", value=0, unit="%"),
        ],
    },
    "MonoPicking": {
        "title": "Mono Picking",
        "kpis": [
            Kpi(label="Mono picks per hour", value=0, unit="items/h"),
            Kpi(label="Open mono orders", value=0, unit="orders"),
            Kpi(label="Picking accuracy", value=0, unit="%"),
        ],
    },
    "InboundAndBulk": {
        "title": "Inbound & Bulk Handling",
        "kpis": [
            Kpi(label="Bulk pallets processed", value=0, unit="pallets"),
            Kpi(label="Receiving backlog", value=0, unit="pallets"),
            Kpi(label="Avg pallet wait time", value=0, unit="min"),
        ],
    },
    "Returns": {
        "title": "Returns",
        "kpis": [
            Kpi(label="Returns processed", value=0, unit="items"),
            Kpi(label="Return backlog", value=0, unit="items"),
            Kpi(label="Disposition rate", value=0, unit="%"),
        ],
    },
}

# ---------------------------------------------------------------------------
# Endpoints – all use deepcopy of _BASE except Sorting (uses live dashboard)
# ---------------------------------------------------------------------------

@router.get("/GeekPicking", response_model=Dashboard)
def get_geek_picking():
    dashboard = deepcopy(_BASE)
    patch = PATCHES["GeekPicking"]
    dashboard.title = patch["title"]
    dashboard.kpis = patch["kpis"]
    return dashboard

@router.get("/GeekInbound", response_model=Dashboard)
def get_geek_inbound():
    dashboard = deepcopy(_BASE)
    patch = PATCHES["GeekInbound"]
    dashboard.title = patch["title"]
    dashboard.kpis = patch["kpis"]
    return dashboard

@router.get("/ErrorLanes", response_model=Dashboard)
def get_error_lanes():
    dashboard = deepcopy(_BASE)
    patch = PATCHES["ErrorLanes"]
    dashboard.title = patch["title"]
    dashboard.kpis = patch["kpis"]
    return dashboard

@router.get("/FMA", response_model=Dashboard)
def get_fma():
    dashboard = deepcopy(_BASE)
    patch = PATCHES["FMA"]
    dashboard.title = patch["title"]
    dashboard.kpis = patch["kpis"]
    return dashboard

@router.get("/MonoPicking", response_model=Dashboard)
def get_mono_picking():
    dashboard = deepcopy(_BASE)
    patch = PATCHES["MonoPicking"]
    dashboard.title = patch["title"]
    dashboard.kpis = patch["kpis"]
    return dashboard

@router.get("/InboundAndBulk", response_model=Dashboard)
def get_inbound_bulk():
    dashboard = deepcopy(_BASE)
    patch = PATCHES["InboundAndBulk"]
    dashboard.title = patch["title"]
    dashboard.kpis = patch["kpis"]
    return dashboard

@router.get("/Returns", response_model=Dashboard)
def get_returns():
    dashboard = deepcopy(_BASE)
    patch = PATCHES["Returns"]
    dashboard.title = patch["title"]
    dashboard.kpis = patch["kpis"]
    return dashboard

@router.get("/Sorting", response_model=Dashboard)
def get_sorting():
    # Use the live dashboard from the in-memory DB
    return get_db()["default"]
