# app/models.py
from collections import deque
from datetime import datetime
from typing import Deque, Tuple

from pydantic import BaseModel, Field

MAX_APM = 6000  # keep last hour of activity samples


class Person(BaseModel):
    name: str
    speed: int          # smoothed jobs/min
    idleSeconds: int    # seconds since last activity
    last_seen: datetime | None = None
    jobs: int = 0       # total jobs handled (optional but handy)
    job_times: Deque[Tuple[float, int]] = Field(default_factory=lambda: deque(maxlen=MAX_APM))
