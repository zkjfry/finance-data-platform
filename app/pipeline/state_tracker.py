from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.storage.models import CrawlStateModel
from app.common.time_utils import utc_now


def update_crawl_state(
    db: Session,
    source: str,
    target_key: str,
    content_hash: str | None,
    status: str,
    error_message: str | None = None,
) -> None:
    stmt = select(CrawlStateModel).where(
        CrawlStateModel.source == source,
        CrawlStateModel.target_key == target_key,
    )

    existing = db.execute(stmt).scalar_one_or_none()
    now = utc_now()

    if existing is None:
        model = CrawlStateModel(
            source=source,
            target_key=target_key,
            last_fetched_at=now,
            last_success_at=now if status == "success" else None,
            last_content_hash=content_hash,
            status=status,
            error_message=error_message,
        )
        db.add(model)
    else:
        existing.last_fetched_at = now
        if status == "success":
            existing.last_success_at = now
        existing.last_content_hash = content_hash
        existing.status = status
        existing.error_message = error_message

    db.commit()