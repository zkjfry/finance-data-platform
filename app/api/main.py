import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.companies import router as companies_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.markets import router as markets_router
from app.api.routes.news import router as news_router
from app.api.routes.reports import router as reports_router
from app.api.routes.search import router as search_router
from app.api.routes.sources import router as sources_router
from app.infrastructure.storage.postgres import init_db
from config.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)


def get_frontend_origins() -> list[str]:
    default_origins = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ]

    env_origins = os.getenv("FRONTEND_ORIGINS")
    if not env_origins:
        return default_origins

    extra_origins = [
        origin.strip()
        for origin in env_origins.split(",")
        if origin.strip()
    ]

    return default_origins + extra_origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(health_router)
app.include_router(news_router)
app.include_router(reports_router)
app.include_router(search_router)
app.include_router(sources_router)
app.include_router(companies_router)
app.include_router(markets_router)
app.include_router(dashboard_router)