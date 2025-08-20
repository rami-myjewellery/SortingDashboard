

from fastapi import FastAPI

from app.routers import dashboard, sortingBeltAnalyser, \
    PostJobsActionToDashboard, PostGeekPutAway, PostGeekPickOrder  # import other routers as you add them


def create_app() -> FastAPI:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.routers import dashboard, sortingBeltAnalyser

    ALLOWED_ORIGINS = [
        "http://127.0.0.1:5176",
        "https://sorting-dashboard-web-208732756826.europe-west4.run.app",
    ]

    app = FastAPI(title="Sorting Dashboard API", version="1.0.0", docs_url="/")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
    app.include_router(sortingBeltAnalyser.router, prefix="/analysis", tags=["analyse-belt"])
    app.include_router(PostJobsActionToDashboard.router, prefix="/actions", tags=["sorting-actions"])
    app.include_router(PostGeekPutAway.router, prefix="/actions", tags=["put-away"])
    app.include_router(PostGeekPickOrder.router, prefix="/actions", tags=["pick-order"])
    return app


app = create_app()

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", 5001))

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


