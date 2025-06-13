from typing import Dict
from app.models import Dashboard, Kpi, Person

_db: Dict[str, Dashboard] = {
    "default": Dashboard(
        title="Sorting",
        status="good",
        kpis=[
            Kpi(label="Error belt filling level", value=0, unit="packages"),
            Kpi(label="Single belt filling level", value=0, unit="packages"),
            Kpi(label="Multi belt filling level", value=0, unit="packages"),
        ],
        historyText="",
        people=[
            Person(name="Alex",     speed=80, idleSeconds=10),
            Person(name="Muhammed", speed=65, idleSeconds=40),
            Person(name="Deborah",  speed=30, idleSeconds=55),
            Person(name="Bo",       speed=55, idleSeconds=45),
        ],
        idleThreshold=40,
    )
}

def get_db() -> Dict[str, Dashboard]:
    return _db
