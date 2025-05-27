from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import dashboard, sortingBeltAnalyser  # import other routers as you add them

ALLOWED_ORIGINS = [
    "http://localhost:5180",
    "https://sorting-dashboard-web-208732756826.europe-west4.run.app",
]

def create_app() -> FastAPI:
    app = FastAPI(
        title="Sorting Dashboard API",
        version="1.0.0",
        docs_url="/",               # Swagger on root for convenience
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------- register routers here ---------------------------------
    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(sortingBeltAnalyser.router, prefix="/analysis", tags=["analyse-belt"])
    # ------------------------------------------------------------------

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn, os
    port = int(os.getenv("PORT", 5001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True, log_level="info")
