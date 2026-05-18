from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.storage.postgres import get_db_session
from app.infrastructure.storage.models import NewsArticleModel

router = APIRouter(prefix="/news", tags=["news"])


def db_dependency():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/latest")
def latest_news(limit: int = 20, db: Session = Depends(db_dependency)) -> list[dict]:
    stmt = (
        select(NewsArticleModel)
        .order_by(NewsArticleModel.updated_at.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).scalars().all()

    return [
        {
            "id": row.id,
            "source": row.source,
            "article_id": row.article_id,
            "url": row.url,
            "title": row.title,
            "summary": row.summary,
            "body_text": row.body_text,
        }
        for row in rows
    ]