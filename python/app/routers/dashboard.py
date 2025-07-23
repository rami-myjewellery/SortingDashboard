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
            Kpi(label="wat", value=0, unit="Comming Soon"),
            Kpi(label="denk", value=0, unit="Weet jij een Metric?"),
            Kpi(label="jij?", value=0, unit="Deel het met ons!"),
        ],
    },
    "GeekInbound": {
        "title": "Geek Inbound",
        "kpis": [
            Kpi(label="wat", value=0, unit="Comming Soon"),
            Kpi(label="denk", value=0, unit="Weet jij een Metric?"),
            Kpi(label="jij?", value=0, unit="Deel het met ons!"),

        ],
    },
    "ErrorLanes": {
        "title": "Error Handling",
        "kpis": [
            Kpi(label="wat", value=0, unit="Comming Soon"),
            Kpi(label="denk", value=0, unit="Weet jij een Metric?"),
            Kpi(label="jij?", value=0, unit="Deel het met ons!"),

        ],
    },
    "FMA": {
        "title": "FMA Pick & Pack",
        "kpis": [
            Kpi(label="wat", value=0, unit="Comming Soon"),
            Kpi(label="denk", value=0, unit="Weet jij een Metric?"),
            Kpi(label="jij?", value=0, unit="Deel het met ons!"),

        ],
    },
    "MonoPicking": {
        "title": "Mono Picking",
        "kpis": [
            Kpi(label="wat", value=0, unit="Comming Soon"),
            Kpi(label="denk", value=0, unit="Weet jij een Metric?"),
            Kpi(label="jij?", value=0, unit="Deel het met ons!"),

        ],
    },
    "InboundAndBulk": {
        "title": "Inbound & Bulk Handling",
        "kpis": [
            Kpi(label="wat", value=0, unit="Comming Soon"),
            Kpi(label="denk", value=0, unit="Weet jij een Metric?"),
            Kpi(label="jij?", value=0, unit="Deel het met ons!"),

        ],
    },
    "Returns": {
        "title": "Returns",
        "kpis": [
            Kpi(label="wat", value=0, unit="Comming Soon"),
            Kpi(label="denk", value=0, unit="Weet jij een Metric?"),
            Kpi(label="jij?", value=0, unit="Deel het met ons!"),

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
