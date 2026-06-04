from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, literal, or_, select
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.infrastructure.storage.postgres import get_db_session
from app.infrastructure.storage.models import NewsArticleModel, ResearchReportModel

router = APIRouter(prefix="/search", tags=["search"])


def db_dependency():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


def _news_vector():
    return func.to_tsvector(
        literal("english"),
        func.concat_ws(
            " ",
            func.coalesce(NewsArticleModel.title, ""),
            func.coalesce(NewsArticleModel.summary, ""),
            func.coalesce(NewsArticleModel.body_text, ""),
            func.coalesce(NewsArticleModel.symbols, ""),
        ),
    )


def _report_vector():
    return func.to_tsvector(
        literal("english"),
        func.concat_ws(
            " ",
            func.coalesce(ResearchReportModel.title, ""),
            func.coalesce(ResearchReportModel.summary, ""),
            func.coalesce(ResearchReportModel.body_text, ""),
            func.coalesce(ResearchReportModel.company_name, ""),
            func.coalesce(ResearchReportModel.ticker, ""),
            func.coalesce(ResearchReportModel.report_type, ""),
        ),
    )


@router.get("")
def global_search(
    keyword: str = Query(..., min_length=1),
    source: str | None = Query(default=None),
    ticker: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(db_dependency),
) -> dict:
    ts_query = func.websearch_to_tsquery(literal("english"), keyword)
    keyword_like = f"%{keyword}%"

    news_relevance = func.ts_rank_cd(_news_vector(), ts_query).label("relevance")

    news_stmt = select(NewsArticleModel, news_relevance).where(
        or_(
            _news_vector().op("@@")(ts_query),
            NewsArticleModel.title.ilike(keyword_like),
            NewsArticleModel.summary.ilike(keyword_like),
            NewsArticleModel.body_text.ilike(keyword_like),
            NewsArticleModel.symbols.ilike(keyword_like),
        )
    )

    if source:
        news_stmt = news_stmt.where(NewsArticleModel.source == source)

    if ticker:
        news_stmt = news_stmt.where(NewsArticleModel.symbols.ilike(f"%{ticker}%"))

    if start_date:
        news_stmt = news_stmt.where(NewsArticleModel.published_at >= start_date)

    if end_date:
        news_stmt = news_stmt.where(NewsArticleModel.published_at <= end_date)

    news_stmt = (
        news_stmt
        .order_by(
            news_relevance.desc(),
            NewsArticleModel.published_at.desc().nullslast(),
        )
        .limit(limit)
    )

    report_relevance = func.ts_rank_cd(_report_vector(), ts_query).label("relevance")

    report_stmt = select(ResearchReportModel, report_relevance).where(
        or_(
            _report_vector().op("@@")(ts_query),
            ResearchReportModel.title.ilike(keyword_like),
            ResearchReportModel.summary.ilike(keyword_like),
            ResearchReportModel.body_text.ilike(keyword_like),
            ResearchReportModel.company_name.ilike(keyword_like),
            ResearchReportModel.ticker.ilike(keyword_like),
            ResearchReportModel.report_type.ilike(keyword_like),
        )
    )

    if source:
        report_stmt = report_stmt.where(ResearchReportModel.source == source)

    if ticker:
        report_stmt = report_stmt.where(ResearchReportModel.ticker.ilike(f"%{ticker}%"))

    if start_date:
        report_stmt = report_stmt.where(ResearchReportModel.published_at >= start_date)

    if end_date:
        report_stmt = report_stmt.where(ResearchReportModel.published_at <= end_date)

    report_stmt = (
        report_stmt
        .order_by(
            report_relevance.desc(),
            ResearchReportModel.published_at.desc().nullslast(),
        )
        .limit(limit)
    )

    results: list[dict] = []

    for row, relevance in db.execute(news_stmt).all():
        results.append(
            {
                "type": "news",
                "id": row.id,
                "source": row.source,
                "title": row.title,
                "url": row.url,
                "published_at": row.published_at,
                "ticker": row.symbols,
                "summary": row.summary,
                "relevance": float(relevance),
            }
        )

    for row, relevance in db.execute(report_stmt).all():
        results.append(
            {
                "type": "report",
                "id": row.id,
                "source": row.source,
                "title": row.title,
                "url": row.detail_url or row.pdf_url,
                "published_at": row.published_at,
                "ticker": row.ticker,
                "company_name": row.company_name,
                "summary": row.summary,
                "relevance": float(relevance),
            }
        )

    results.sort(
        key=lambda item: (
            item["relevance"],
            item["published_at"].timestamp() if item["published_at"] else 0,
        ),
        reverse=True,
    )

    return success_response(
        data=results[:limit],
        meta={"keyword": keyword, "limit": limit},
    )