from pydantic import BaseModel
from typing import List, Literal

class Kpi(BaseModel):
    label: str
    value: float
    unit: str

class Person(BaseModel):
    name: str
    speed: int          # 0-100
    idleSeconds: int

class Dashboard(BaseModel):
    title: str
    status: Literal["good", "risk", "bad"]
    kpis: List[Kpi]
    historyText: str
    people: List[Person]
    idleThreshold: int = 40
