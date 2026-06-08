from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.infrastructure.storage.models import (
    CompanyModel,
    CrawlRunModel,
    DocumentCompanyLinkModel,
    MarketPriceModel,
    NewsArticleModel,
    ResearchReportModel,
    SecurityModel,
)
from app.infrastructure.storage.postgres import get_db_session

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


SPARKLINE_DAYS = 30


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


def _crawl_run_to_dict(row: CrawlRunModel) -> dict:
    return {
        "id": row.id,
        "crawler_name": row.crawler_name,
        "source": row.source,
        "status": row.status,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
        "items_fetched": row.items_fetched,
        "items_inserted": row.items_inserted,
        "items_skipped": row.items_skipped,
        "items_failed": row.items_failed,
        "error_message": row.error_message,
    }


def _news_to_dict(row: NewsArticleModel) -> dict:
    return {
        "id": row.id,
        "source": row.source,
        "article_id": row.article_id,
        "url": row.url,
        "title": row.title,
        "published_at": row.published_at,
        "summary": row.summary,
    }


def _report_to_dict(row: ResearchReportModel) -> dict:
    return {
        "id": row.id,
        "source": row.source,
        "report_id": row.report_id,
        "company_name": row.company_name,
        "ticker": row.ticker,
        "title": row.title,
        "report_type": row.report_type,
        "published_at": row.published_at,
        "detail_url": row.detail_url,
        "pdf_url": row.pdf_url,
        "summary": row.summary,
    }


def _latest_two_prices_by_security(db: Session):
    """
    Returns:
    - primary securities
    - security_id -> [latest_price, previous_price]
    """
    securities = db.execute(
        select(SecurityModel)
        .where(SecurityModel.is_primary.is_(True))
        .order_by(SecurityModel.ticker.asc())
    ).scalars().all()

    result = {}

    for security in securities:
        prices = db.execute(
            select(MarketPriceModel)
            .where(MarketPriceModel.security_id == security.id)
            .order_by(MarketPriceModel.price_date.desc())
            .limit(2)
        ).scalars().all()

        result[security.id] = prices

    return securities, result


def _sparkline_for_security(db: Session, security_id: int) -> list[dict]:
    """
    Return recent close prices ordered from oldest to newest for frontend sparkline.
    """
    prices = db.execute(
        select(MarketPriceModel)
        .where(MarketPriceModel.security_id == security_id)
        .order_by(MarketPriceModel.price_date.desc())
        .limit(SPARKLINE_DAYS)
    ).scalars().all()

    return [
        {
            "date": row.price_date.isoformat() if row.price_date else None,
            "close": _to_float(row.close),
        }
        for row in reversed(prices)
    ]


def _build_market_cards(db: Session):
    securities, latest_prices_map = _latest_two_prices_by_security(db)

    company_ids = [security.company_id for security in securities]
    companies = {}

    if company_ids:
        company_rows = db.execute(
            select(CompanyModel).where(CompanyModel.id.in_(company_ids))
        ).scalars().all()

        companies = {
            company.id: company
            for company in company_rows
        }

    cards = []

    for security in securities:
        prices = latest_prices_map.get(security.id, [])

        if not prices:
            continue

        latest = prices[0]
        previous = prices[1] if len(prices) > 1 else None

        latest_close = _to_float(latest.close)
        previous_close = _to_float(previous.close) if previous else None

        change = None
        change_pct = None

        if latest_close is not None and previous_close:
            change = latest_close - previous_close
            change_pct = change / previous_close * 100

        company = companies.get(security.company_id)

        cards.append({
            "ticker": security.ticker,
            "company_name": company.canonical_name if company else security.ticker,
            "exchange": security.exchange,
            "currency": security.currency,
            "sector": company.sector if company else None,
            "industry": company.industry if company else None,
            "price_date": latest.price_date.isoformat() if latest.price_date else None,
            "close": latest_close,
            "previous_close": previous_close,
            "change": change,
            "change_pct": change_pct,
            "sparkline": _sparkline_for_security(db, security.id),
        })

    return cards


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(db_dependency),
) -> dict:
    companies_count = db.execute(
        select(func.count()).select_from(CompanyModel)
    ).scalar_one()

    securities_count = db.execute(
        select(func.count()).select_from(SecurityModel)
    ).scalar_one()

    news_count = db.execute(
        select(func.count()).select_from(NewsArticleModel)
    ).scalar_one()

    reports_count = db.execute(
        select(func.count()).select_from(ResearchReportModel)
    ).scalar_one()

    market_prices_count = db.execute(
        select(func.count()).select_from(MarketPriceModel)
    ).scalar_one()

    document_links_count = db.execute(
        select(func.count()).select_from(DocumentCompanyLinkModel)
    ).scalar_one()

    accepted_links_count = db.execute(
        select(func.count())
        .select_from(DocumentCompanyLinkModel)
        .where(DocumentCompanyLinkModel.review_status == "accepted")
    ).scalar_one()

    pending_links_count = db.execute(
        select(func.count())
        .select_from(DocumentCompanyLinkModel)
        .where(DocumentCompanyLinkModel.review_status == "pending")
    ).scalar_one()

    latest_crawl_runs = db.execute(
        select(CrawlRunModel)
        .order_by(CrawlRunModel.started_at.desc())
        .limit(8)
    ).scalars().all()

    market_cards = _build_market_cards(db)

    top_movers = sorted(
        market_cards,
        key=lambda item: abs(item["change_pct"] or 0),
        reverse=True,
    )[:5]

    latest_news = db.execute(
        select(NewsArticleModel)
        .order_by(
            desc(NewsArticleModel.published_at),
            desc(NewsArticleModel.updated_at),
        )
        .limit(5)
    ).scalars().all()

    recent_reports = db.execute(
        select(ResearchReportModel)
        .order_by(
            desc(ResearchReportModel.published_at),
            desc(ResearchReportModel.updated_at),
        )
        .limit(5)
    ).scalars().all()

    return success_response(
        data={
            "counts": {
                "companies": companies_count,
                "securities": securities_count,
                "news_articles": news_count,
                "research_reports": reports_count,
                "market_prices": market_prices_count,
                "document_company_links": document_links_count,
                "accepted_document_links": accepted_links_count,
                "pending_document_links": pending_links_count,
            },
            "market_overview": market_cards[:4],
            "top_movers": top_movers,
            "latest_news": [
                _news_to_dict(row)
                for row in latest_news
            ],
            "recent_reports": [
                _report_to_dict(row)
                for row in recent_reports
            ],
            "heatmap": market_cards,
            "latest_crawl_runs": [
                _crawl_run_to_dict(row)
                for row in latest_crawl_runs
            ],
        }
    )