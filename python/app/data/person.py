# app/models.py
from datetime import datetime
from typing import Deque

from pydantic import BaseModel, Field

from app.routers.PostSortingActionToDashboard import MAX_APM


class Person(BaseModel):
    name: str
    speed: int          # smoothed jobs/min
    idleSeconds: int    # seconds since last activity
    last_seen: datetime | None = None
    jobs: int = 0       # total jobs handled (optional but handy)
    job_times: Deque[float] = Field(default_factory=lambda: deque(maxlen=MAX_APM))
