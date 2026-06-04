from fastapi import FastAPI

from app.api.routes.companies import router as companies_router
from app.api.routes.health import router as health_router
from app.api.routes.news import router as news_router
from app.api.routes.reports import router as reports_router
from app.api.routes.search import router as search_router
from app.api.routes.sources import router as sources_router
from app.infrastructure.storage.postgres import init_db
from config.settings import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(health_router)
app.include_router(news_router)
app.include_router(reports_router)
app.include_router(search_router)
app.include_router(sources_router)
app.include_router(companies_router)