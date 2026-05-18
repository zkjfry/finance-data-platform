from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.storage.postgres import get_db_session
from app.infrastructure.storage.models import ResearchReportModel

router = APIRouter(prefix="/reports", tags=["reports"])


def db_dependency():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/latest")
def latest_reports(limit: int = 20, db: Session = Depends(db_dependency)) -> list[dict]:
    stmt = (
        select(ResearchReportModel)
        .order_by(ResearchReportModel.updated_at.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).scalars().all()

    return [
        {
            "id": row.id,
            "source": row.source,
            "report_id": row.report_id,
            "title": row.title,
            "detail_url": row.detail_url,
            "pdf_url": row.pdf_url,
            "summary": row.summary,
        }
        for row in rows
    ]