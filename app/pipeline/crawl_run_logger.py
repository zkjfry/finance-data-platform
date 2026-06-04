from sqlalchemy.orm import Session

from app.common.time_utils import utc_now
from app.infrastructure.storage.models import CrawlRunModel


def start_crawl_run(
    db: Session,
    crawler_name: str,
    source: str,
) -> CrawlRunModel:
    run = CrawlRunModel(
        crawler_name=crawler_name,
        source=source,
        status="running",
        started_at=utc_now(),
        items_fetched=0,
        items_inserted=0,
        items_skipped=0,
        items_failed=0,
    )

    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finish_crawl_run(
    db: Session,
    run: CrawlRunModel,
    status: str,
    items_fetched: int,
    items_inserted: int,
    items_skipped: int,
    items_failed: int,
    error_message: str | None = None,
) -> CrawlRunModel:
    run.status = status
    run.finished_at = utc_now()
    run.items_fetched = items_fetched
    run.items_inserted = items_inserted
    run.items_skipped = items_skipped
    run.items_failed = items_failed
    run.error_message = error_message

    db.commit()
    db.refresh(run)
    return run