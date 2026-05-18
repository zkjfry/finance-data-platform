from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.storage.models import NewsArticleModel, ResearchReportModel


def is_duplicate_article(
    db: Session,
    source: str,
    article_id: str,
    content_hash: str,
) -> bool:
    stmt = select(NewsArticleModel).where(
        NewsArticleModel.source == source,
        NewsArticleModel.article_id == article_id,
    )

    existing = db.execute(stmt).scalar_one_or_none()

    if existing is None:
        return False

    return existing.content_hash == content_hash


def is_duplicate_report(
    db: Session,
    source: str,
    report_id: str,
    content_hash: str,
) -> bool:
    stmt = select(ResearchReportModel).where(
        ResearchReportModel.source == source,
        ResearchReportModel.report_id == report_id,
    )

    existing = db.execute(stmt).scalar_one_or_none()

    if existing is None:
        return False

    return existing.content_hash == content_hash