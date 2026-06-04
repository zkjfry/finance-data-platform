from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, literal, or_, select
from sqlalchemy.orm import Session

from app.api.response import pagination_meta, success_response
from app.infrastructure.storage.postgres import get_db_session
from app.infrastructure.storage.models import ResearchReportModel

router = APIRouter(prefix="/reports", tags=["reports"])


def db_dependency():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


def _report_to_dict(row: ResearchReportModel, relevance: float | None = None) -> dict:
    result = {
        "id": row.id,
        "source": row.source,
        "report_id": row.report_id,
        "company_name": row.company_name,
        "ticker": row.ticker,
        "title": row.title,
        "report_type": row.report_type,
        "published_at": row.published_at,
        "authors": row.authors,
        "detail_url": row.detail_url,
        "pdf_url": row.pdf_url,
        "pdf_local_path": row.pdf_local_path,
        "summary": row.summary,
        "body_text": row.body_text,
        "updated_at": row.updated_at,
    }

    if relevance is not None:
        result["relevance"] = float(relevance)

    return result


def _report_search_vector():
    searchable_text = func.concat_ws(
        " ",
        func.coalesce(ResearchReportModel.title, ""),
        func.coalesce(ResearchReportModel.summary, ""),
        func.coalesce(ResearchReportModel.body_text, ""),
        func.coalesce(ResearchReportModel.company_name, ""),
        func.coalesce(ResearchReportModel.ticker, ""),
        func.coalesce(ResearchReportModel.report_type, ""),
    )

    return func.to_tsvector(literal("english"), searchable_text)


@router.get("")
def search_reports(
    keyword: str | None = Query(default=None),
    source: str | None = Query(default=None),
    company: str | None = Query(default=None),
    ticker: str | None = Query(default=None),
    report_type: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_dependency),
) -> dict:
    stmt = select(ResearchReportModel)

    if keyword:
        ts_query = func.websearch_to_tsquery(literal("english"), keyword)
        search_vector = _report_search_vector()
        relevance = func.ts_rank_cd(search_vector, ts_query).label("relevance")

        stmt = select(ResearchReportModel, relevance)

        keyword_like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                search_vector.op("@@")(ts_query),
                ResearchReportModel.title.ilike(keyword_like),
                ResearchReportModel.summary.ilike(keyword_like),
                ResearchReportModel.body_text.ilike(keyword_like),
                ResearchReportModel.company_name.ilike(keyword_like),
                ResearchReportModel.ticker.ilike(keyword_like),
                ResearchReportModel.report_type.ilike(keyword_like),
            )
        )
    else:
        relevance = None

    if source:
        stmt = stmt.where(ResearchReportModel.source == source)

    if company:
        stmt = stmt.where(ResearchReportModel.company_name.ilike(f"%{company}%"))

    if ticker:
        stmt = stmt.where(ResearchReportModel.ticker.ilike(f"%{ticker}%"))

    if report_type:
        stmt = stmt.where(ResearchReportModel.report_type.ilike(f"%{report_type}%"))

    if start_date:
        stmt = stmt.where(ResearchReportModel.published_at >= start_date)

    if end_date:
        stmt = stmt.where(ResearchReportModel.published_at <= end_date)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    if keyword:
        stmt = stmt.order_by(
            relevance.desc(),
            ResearchReportModel.published_at.desc().nullslast(),
            ResearchReportModel.updated_at.desc(),
        )
    else:
        stmt = stmt.order_by(
            ResearchReportModel.published_at.desc().nullslast(),
            ResearchReportModel.updated_at.desc(),
        )

    rows = db.execute(stmt.limit(limit).offset(offset)).all()

    if keyword:
        data = [_report_to_dict(row[0], row[1]) for row in rows]
    else:
        data = [_report_to_dict(row[0]) for row in rows]

    return success_response(
        data=data,
        meta=pagination_meta(limit=limit, offset=offset, total=total),
    )


@router.get("/latest")
def latest_reports(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(db_dependency),
) -> dict:
    stmt = (
        select(ResearchReportModel)
        .order_by(ResearchReportModel.updated_at.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).scalars().all()
    data = [_report_to_dict(row) for row in rows]

    return success_response(data=data, meta={"limit": limit})