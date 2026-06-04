from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.infrastructure.storage.postgres import get_db_session
from app.infrastructure.storage.models import CrawlRunModel

router = APIRouter(prefix="/sources", tags=["sources"])


def db_dependency():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def source_health(db: Session = Depends(db_dependency)) -> dict:
    latest_started_at = (
        select(
            CrawlRunModel.source,
            func.max(CrawlRunModel.started_at).label("latest_started_at"),
        )
        .group_by(CrawlRunModel.source)
        .subquery()
    )

    stmt = (
        select(CrawlRunModel)
        .join(
            latest_started_at,
            (CrawlRunModel.source == latest_started_at.c.source)
            & (CrawlRunModel.started_at == latest_started_at.c.latest_started_at),
        )
        .order_by(CrawlRunModel.source.asc())
    )

    rows = db.execute(stmt).scalars().all()

    data = [
        {
            "source": row.source,
            "crawler_name": row.crawler_name,
            "last_status": row.status,
            "last_started_at": row.started_at,
            "last_finished_at": row.finished_at,
            "items_fetched": row.items_fetched,
            "items_inserted": row.items_inserted,
            "items_skipped": row.items_skipped,
            "items_failed": row.items_failed,
            "error_message": row.error_message,
        }
        for row in rows
    ]

    return success_response(data=data)