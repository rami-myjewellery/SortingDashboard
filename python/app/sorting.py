from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from models import Dashboard, Kpi, Person

app = FastAPI(
    title="Sorting Dashboard API",
    version="1.0.0",
    docs_url="/",          # Swagger on root for convenience
)

# Allow your Vite dev-server + production host
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5180", "https://your-vue-host.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- In-memory store (replace later with DB/Redis) -----------------
_db: Dict[str, Dashboard] = {
    "default": Dashboard(
        title="Sorting",
        status="risk",
        kpis=[
            Kpi(label="Multi belt filling level",  value=78, unit="%"),
            Kpi(label="Single belt filling level", value=3,  unit="%"),
            Kpi(label="Error belt filling level",  value=3,  unit="%"),
        ],
        historyText="Gem. vulgraad • uur 74 % • vandaag 76 % • gisteren 72 %",
        people=[
            Person(name="Alex",     speed=80, idleSeconds=10),
            Person(name="Muhammed", speed=65, idleSeconds=40),
            Person(name="Deborah",  speed=30, idleSeconds=55),
            Person(name="Bo",       speed=55, idleSeconds=45),
        ],
        idleThreshold=40,
    )
}
# ---------------------------------------------------------------------

@app.get("/dashboard", response_model=Dashboard)
def get_dashboard(profile: str = "default"):
    """
    Return the current dashboard data.
    Use ?profile=xyz to support multiple dashboards later.
    """
    if profile not in _db:
        raise HTTPException(status_code=404, detail="profile not found")
    return _db[profile]

@app.post("/dashboard", response_model=Dashboard, status_code=201)
def update_dashboard(payload: Dashboard, profile: str = "default"):
    """
    Replace the current dashboard snapshot.  
    In real life you’d PATCH or update specific fields.
    """
    _db[profile] = payload
    return _db[profile]


if __name__ == "__main__":
    import uvicorn, os
    port = int(os.getenv("PORT", 5001))

    # OPTION A – keep the string style but use the right module path
    uvicorn.run("sorting:app",
                host="0.0.0.0", port=port, log_level="info")
