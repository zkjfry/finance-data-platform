from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, literal, or_, select
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.infrastructure.storage.models import (
    CompanyAliasModel,
    CompanyModel,
    NewsArticleModel,
    ResearchReportModel,
    SecurityModel,
)
from app.infrastructure.storage.postgres import get_db_session

router = APIRouter(prefix="/search", tags=["search"])


def db_dependency():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


def _to_float(value):
    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    return value


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


def _company_to_result(company: CompanyModel, security: SecurityModel | None) -> dict:
    return {
        "type": "company",
        "id": company.id,
        "company_name": company.canonical_name,
        "legal_name": company.legal_name,
        "description": company.description,
        "sector": company.sector,
        "industry": company.industry,
        "country": company.country,
        "website": company.website,
        "ticker": security.ticker if security else None,
        "exchange": security.exchange if security else None,
        "currency": security.currency if security else None,
        "security_type": security.security_type if security else None,
    }


def _news_to_result(row: NewsArticleModel, relevance=None) -> dict:
    return {
        "type": "news",
        "id": row.id,
        "source": row.source,
        "article_id": row.article_id,
        "title": row.title,
        "url": row.url,
        "published_at": row.published_at,
        "ticker": row.symbols,
        "summary": row.summary,
        "relevance": _to_float(relevance) or 0,
    }


def _report_to_result(row: ResearchReportModel, relevance=None) -> dict:
    return {
        "type": "report",
        "id": row.id,
        "source": row.source,
        "report_id": row.report_id,
        "company_name": row.company_name,
        "ticker": row.ticker,
        "title": row.title,
        "report_type": row.report_type,
        "url": row.pdf_url or row.detail_url,
        "detail_url": row.detail_url,
        "pdf_url": row.pdf_url,
        "published_at": row.published_at,
        "summary": row.summary,
        "relevance": _to_float(relevance) or 0,
    }


@router.get("")
def global_search(
    q: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    source: str | None = Query(default=None),
    ticker: str | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    limit: int = Query(default=8, ge=1, le=50),
    db: Session = Depends(db_dependency),
) -> dict:
    search_text = (q or keyword or "").strip()

    if not search_text:
        raise HTTPException(status_code=400, detail="Search keyword is required.")

    keyword_like = f"%{search_text}%"

    company_stmt = (
        select(CompanyModel, SecurityModel)
        .join(
            SecurityModel,
            (SecurityModel.company_id == CompanyModel.id)
            & (SecurityModel.is_primary.is_(True)),
            isouter=True,
        )
        .outerjoin(CompanyAliasModel, CompanyAliasModel.company_id == CompanyModel.id)
        .where(
            or_(
                CompanyModel.canonical_name.ilike(keyword_like),
                CompanyModel.legal_name.ilike(keyword_like),
                CompanyModel.description.ilike(keyword_like),
                CompanyModel.sector.ilike(keyword_like),
                CompanyModel.industry.ilike(keyword_like),
                SecurityModel.ticker.ilike(keyword_like),
                CompanyAliasModel.alias.ilike(keyword_like),
            )
        )
        .group_by(CompanyModel.id, SecurityModel.id)
        .order_by(CompanyModel.canonical_name.asc())
        .limit(limit)
    )

    company_rows = db.execute(company_stmt).all()
    companies = [
        _company_to_result(company, security)
        for company, security in company_rows
    ]

    ts_query = func.websearch_to_tsquery(literal("english"), search_text)

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

    news = [
        _news_to_result(row, relevance)
        for row, relevance in db.execute(news_stmt).all()
    ]

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

    reports = [
        _report_to_result(row, relevance)
        for row, relevance in db.execute(report_stmt).all()
    ]

    return success_response(
        data={
            "keyword": search_text,
            "companies": companies,
            "news": news,
            "reports": reports,
            "total": len(companies) + len(news) + len(reports),
        },
        meta={
            "keyword": search_text,
            "limit": limit,
            "counts": {
                "companies": len(companies),
                "news": len(news),
                "reports": len(reports),
            },
        },
    )