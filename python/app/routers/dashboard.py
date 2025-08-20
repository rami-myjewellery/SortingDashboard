from copy import deepcopy
from typing import Dict

from fastapi import APIRouter, HTTPException

from app.models import Dashboard, Kpi
from app.data.store import get_db

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
            Kpi(label="Picking Speed", value=0, unit="items/sec"),
            Kpi(label="Cartons Processed", value=0, unit="cartons"),
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

# ---------------------------------------------------------------------------
# Endpoints for each category dashboard
# ---------------------------------------------------------------------------

@router.get("/GeekPicking", response_model=Dashboard)
def get_geek_picking():
    return get_db()["geekpicking"]

@router.get("/GeekInbound", response_model=Dashboard)
def get_geek_inbound():
    return get_db()["geekinbound"]

@router.get("/Replenishment", response_model=Dashboard)
def get_replenishment():
    # Use the live dashboard from the in-memory DB for "FMA"
    return get_db()["replenishment"]

@router.get("/Picking", response_model=Dashboard)
def get_mono_picking():
    # Use the live dashboard from the in-memory DB for "MonoPicking"
    return get_db()["pick"]

@router.get("/InboundAndBulk", response_model=Dashboard)
def get_inbound_bulk():
    # Use the live dashboard from the in-memory DB for "InboundAndBulk"
    return get_db()["inbound"]

@router.get("/Returns", response_model=Dashboard)
def get_returns():
    # Use the live dashboard from the in-memory DB for "Returns"
    return get_db()["returns"]

@router.get("/ErrorLanes", response_model=Dashboard)
def get_error_lanes():
    # Use the live dashboard from the in-memory DB for "ErrorLanes"
    return get_db()["error lane"]

@router.get("/Sorting", response_model=Dashboard)
def get_sorting():
    # Use the live dashboard from the in-memory DB
    return get_db()["default"]
