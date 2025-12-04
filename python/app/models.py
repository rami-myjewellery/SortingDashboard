from collections import deque
from datetime import datetime

from pydantic import BaseModel, Field
from typing import List, Literal, Deque, Optional, Dict, Tuple

MAX_APM = 6000  # samples to keep for per-operator speed (covers the last hour)


class Kpi(BaseModel):
    label: str
    value: float
    unit: str


class Person(BaseModel):
    name: str
    comment: str
    category: str
    speed: int          # smoothed jobs/min
    idleSeconds: int    # seconds since last activity
    last_seen: datetime | None = None
    jobs: int = 0       # total jobs handled (optional but handy)
    job_times: Deque[Tuple[float, int]] = Field(default_factory=lambda: deque(maxlen=MAX_APM))


class Dashboard(BaseModel):
    title: str
    status: Literal["good", "risk", "bad"]
    kpis: List[Kpi]
    historyText: str
    people: List[Person]
    idleThreshold: int = 60
    kpi_state: Optional[Dict] = None
