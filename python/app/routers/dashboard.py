from fastapi import APIRouter, HTTPException
from typing import Dict

from app.models import Dashboard, Kpi, Person

router = APIRouter()

from app.models import Dashboard
from app.data.store import get_db

@router.get("/", response_model=Dashboard)
def get_dashboard(profile: str = "default"):
    """
    Return the current dashboard snapshot.
    Use ?profile=xyz to support multiple dashboards later.
    """
    _db = get_db()

    if profile not in _db:
        raise HTTPException(status_code=404, detail="profile not found")
    return _db[profile]


@router.post("/", response_model=Dashboard, status_code=201)
def update_dashboard(payload: Dashboard, profile: str = "default"):
    """
    Replace the current dashboard snapshot.
    In real life you’d PATCH or update specific fields.
    """
    _db[profile] = payload
    return _db[profile]
