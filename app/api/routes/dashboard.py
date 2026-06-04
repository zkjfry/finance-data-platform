from fastapi import APIRouter, Depends
from sqlalchemy import func, select
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


def db_dependency():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


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
        .limit(10)
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
            "latest_crawl_runs": [
                _crawl_run_to_dict(row)
                for row in latest_crawl_runs
            ],
        }
    )