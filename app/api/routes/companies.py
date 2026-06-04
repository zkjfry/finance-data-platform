import json
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.response import pagination_meta, success_response
from app.infrastructure.storage.models import (
    CompanyAliasModel,
    CompanyModel,
    DocumentCompanyLinkModel,
    MarketPriceModel,
    NewsArticleModel,
    ResearchReportModel,
    SecurityModel,
)
from app.infrastructure.storage.postgres import get_db_session

router = APIRouter(prefix="/companies", tags=["companies"])


def db_dependency():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []

    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _decimal(value) -> float | None:
    if value is None:
        return None

    if isinstance(value, Decimal):
        return float(value)

    return value


def _company_to_dict(row: CompanyModel) -> dict:
    return {
        "id": row.id,
        "canonical_name": row.canonical_name,
        "legal_name": row.legal_name,
        "description": row.description,
        "sector": row.sector,
        "industry": row.industry,
        "country": row.country,
        "website": row.website,
        "is_active": row.is_active,
        "updated_at": row.updated_at,
    }


def _security_to_dict(row: SecurityModel | None) -> dict | None:
    if row is None:
        return None

    return {
        "id": row.id,
        "company_id": row.company_id,
        "ticker": row.ticker,
        "exchange": row.exchange,
        "currency": row.currency,
        "security_type": row.security_type,
        "is_primary": row.is_primary,
        "updated_at": row.updated_at,
    }


def _price_to_dict(row: MarketPriceModel | None) -> dict | None:
    if row is None:
        return None

    return {
        "id": row.id,
        "security_id": row.security_id,
        "price_date": row.price_date,
        "open": _decimal(row.open),
        "high": _decimal(row.high),
        "low": _decimal(row.low),
        "close": _decimal(row.close),
        "adj_close": _decimal(row.adj_close),
        "volume": row.volume,
        "source": row.source,
        "updated_at": row.updated_at,
    }


def _link_to_dict(row: DocumentCompanyLinkModel | None) -> dict | None:
    if row is None:
        return None

    return {
        "id": row.id,
        "document_type": row.document_type,
        "document_id": row.document_id,
        "company_id": row.company_id,
        "security_id": row.security_id,
        "ticker": row.ticker,
        "match_method": row.match_method,
        "evidence_text": row.evidence_text,
        "review_status": row.review_status,
        "confidence": _decimal(row.confidence),
        "updated_at": row.updated_at,
    }


def _news_to_dict(
        row: NewsArticleModel,
        link: DocumentCompanyLinkModel | None = None,
) -> dict:
    return {
        "id": row.id,
        "source": row.source,
        "article_id": row.article_id,
        "url": row.url,
        "title": row.title,
        "published_at": row.published_at,
        "symbols": _json_list(row.symbols),
        "authors": _json_list(row.authors),
        "summary": row.summary,
        "updated_at": row.updated_at,
        "company_link": _link_to_dict(link),
    }


def _report_to_dict(
        row: ResearchReportModel,
        link: DocumentCompanyLinkModel | None = None,
) -> dict:
    return {
        "id": row.id,
        "source": row.source,
        "report_id": row.report_id,
        "company_name": row.company_name,
        "ticker": row.ticker,
        "title": row.title,
        "report_type": row.report_type,
        "published_at": row.published_at,
        "authors": _json_list(row.authors),
        "detail_url": row.detail_url,
        "pdf_url": row.pdf_url,
        "summary": row.summary,
        "updated_at": row.updated_at,
        "company_link": _link_to_dict(link),
    }


def _find_company_bundle(
        db: Session,
        ticker_or_alias: str,
) -> tuple[CompanyModel, SecurityModel | None]:
    key = ticker_or_alias.strip()
    key_upper = key.upper()

    security = db.execute(
        select(SecurityModel).where(SecurityModel.ticker == key_upper)
    ).scalar_one_or_none()

    if security is not None:
        company = db.execute(
            select(CompanyModel).where(CompanyModel.id == security.company_id)
        ).scalar_one()
        return company, security

    alias = db.execute(
        select(CompanyAliasModel).where(
            func.lower(CompanyAliasModel.alias) == key.lower()
        )
    ).scalar_one_or_none()

    if alias is not None:
        company = db.execute(
            select(CompanyModel).where(CompanyModel.id == alias.company_id)
        ).scalar_one()

        primary_security = db.execute(
            select(SecurityModel).where(
                SecurityModel.company_id == company.id,
                SecurityModel.is_primary.is_(True),
            )
        ).scalar_one_or_none()

        return company, primary_security

    company = db.execute(
        select(CompanyModel).where(
            or_(
                func.lower(CompanyModel.canonical_name) == key.lower(),
                func.lower(CompanyModel.legal_name) == key.lower(),
            )
        )
    ).scalar_one_or_none()

    if company is None:
        raise HTTPException(
            status_code=404,
            detail=f"Company not found: {ticker_or_alias}",
        )

    primary_security = db.execute(
        select(SecurityModel).where(
            SecurityModel.company_id == company.id,
            SecurityModel.is_primary.is_(True),
        )
    ).scalar_one_or_none()

    return company, primary_security


@router.get("")
def list_companies(
        limit: int = Query(default=20, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        db: Session = Depends(db_dependency),
) -> dict:
    stmt = (
        select(CompanyModel, SecurityModel)
            .join(
            SecurityModel,
            (SecurityModel.company_id == CompanyModel.id)
            & (SecurityModel.is_primary.is_(True)),
            isouter=True,
        )
            .order_by(CompanyModel.canonical_name.asc())
    )

    total = db.execute(
        select(func.count()).select_from(CompanyModel)
    ).scalar_one()

    rows = db.execute(stmt.limit(limit).offset(offset)).all()

    data = [
        {
            "company": _company_to_dict(company),
            "primary_security": _security_to_dict(security),
        }
        for company, security in rows
    ]

    return success_response(
        data=data,
        meta=pagination_meta(limit=limit, offset=offset, total=total),
    )


@router.get("/search")
def search_companies(
        keyword: str = Query(..., min_length=1),
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        db: Session = Depends(db_dependency),
) -> dict:
    keyword_like = f"%{keyword}%"

    stmt = (
        select(CompanyModel, SecurityModel)
            .join(SecurityModel, SecurityModel.company_id == CompanyModel.id)
            .outerjoin(CompanyAliasModel, CompanyAliasModel.company_id == CompanyModel.id)
            .where(
            or_(
                CompanyModel.canonical_name.ilike(keyword_like),
                CompanyModel.legal_name.ilike(keyword_like),
                SecurityModel.ticker.ilike(keyword_like),
                CompanyAliasModel.alias.ilike(keyword_like),
            )
        )
            .group_by(CompanyModel.id, SecurityModel.id)
            .order_by(CompanyModel.canonical_name.asc())
    )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.limit(limit).offset(offset)).all()

    data = [
        {
            "company": _company_to_dict(company),
            "primary_security": _security_to_dict(security),
        }
        for company, security in rows
    ]

    return success_response(
        data=data,
        meta=pagination_meta(limit=limit, offset=offset, total=total),
    )


@router.get("/{ticker_or_alias}")
def company_overview(
        ticker_or_alias: str,
        news_limit: int = Query(default=5, ge=0, le=20),
        reports_limit: int = Query(default=5, ge=0, le=20),
        prices_limit: int = Query(default=30, ge=0, le=500),
        db: Session = Depends(db_dependency),
) -> dict:
    company, security = _find_company_bundle(db, ticker_or_alias)

    latest_price = None
    price_rows = []

    if security is not None:
        latest_price = db.execute(
            select(MarketPriceModel)
                .where(MarketPriceModel.security_id == security.id)
                .order_by(MarketPriceModel.price_date.desc())
                .limit(1)
        ).scalar_one_or_none()

        price_rows = db.execute(
            select(MarketPriceModel)
                .where(MarketPriceModel.security_id == security.id)
                .order_by(MarketPriceModel.price_date.desc())
                .limit(prices_limit)
        ).scalars().all()

    news_rows = db.execute(
        select(NewsArticleModel, DocumentCompanyLinkModel)
            .join(
            DocumentCompanyLinkModel,
            DocumentCompanyLinkModel.document_id == NewsArticleModel.id,
        )
            .where(
            DocumentCompanyLinkModel.document_type == "news",
            DocumentCompanyLinkModel.company_id == company.id,
            DocumentCompanyLinkModel.review_status == "accepted",
        )
            .order_by(
            NewsArticleModel.published_at.desc().nullslast(),
            NewsArticleModel.updated_at.desc(),
        )
            .limit(news_limit)
    ).all()

    report_rows = db.execute(
        select(ResearchReportModel, DocumentCompanyLinkModel)
            .join(
            DocumentCompanyLinkModel,
            DocumentCompanyLinkModel.document_id == ResearchReportModel.id,
        )
            .where(
            DocumentCompanyLinkModel.document_type == "report",
            DocumentCompanyLinkModel.company_id == company.id,
            DocumentCompanyLinkModel.review_status == "accepted",
        )
            .order_by(
            ResearchReportModel.published_at.desc().nullslast(),
            ResearchReportModel.updated_at.desc(),
        )
            .limit(reports_limit)
    ).all()

    aliases = db.execute(
        select(CompanyAliasModel.alias)
            .where(CompanyAliasModel.company_id == company.id)
            .order_by(CompanyAliasModel.alias.asc())
    ).scalars().all()

    return success_response(
        data={
            "company": _company_to_dict(company),
            "primary_security": _security_to_dict(security),
            "aliases": aliases,
            "latest_price": _price_to_dict(latest_price),
            "latest_news": [
                _news_to_dict(news, link)
                for news, link in news_rows
            ],
            "latest_reports": [
                _report_to_dict(report, link)
                for report, link in report_rows
            ],
            "price_history": [
                _price_to_dict(row)
                for row in reversed(price_rows)
            ],
        }
    )


@router.get("/{ticker_or_alias}/news")
def company_news(
        ticker_or_alias: str,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        db: Session = Depends(db_dependency),
) -> dict:
    company, _ = _find_company_bundle(db, ticker_or_alias)

    stmt = (
        select(NewsArticleModel, DocumentCompanyLinkModel)
            .join(
            DocumentCompanyLinkModel,
            DocumentCompanyLinkModel.document_id == NewsArticleModel.id,
        )
            .where(
            DocumentCompanyLinkModel.document_type == "news",
            DocumentCompanyLinkModel.company_id == company.id,
            DocumentCompanyLinkModel.review_status == "accepted",
        )
            .order_by(
            NewsArticleModel.published_at.desc().nullslast(),
            NewsArticleModel.updated_at.desc(),
        )
    )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.limit(limit).offset(offset)).all()

    return success_response(
        data=[
            _news_to_dict(news, link)
            for news, link in rows
        ],
        meta=pagination_meta(limit=limit, offset=offset, total=total),
    )


@router.get("/{ticker_or_alias}/reports")
def company_reports(
        ticker_or_alias: str,
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        db: Session = Depends(db_dependency),
) -> dict:
    company, _ = _find_company_bundle(db, ticker_or_alias)

    stmt = (
        select(ResearchReportModel, DocumentCompanyLinkModel)
            .join(
            DocumentCompanyLinkModel,
            DocumentCompanyLinkModel.document_id == ResearchReportModel.id,
        )
            .where(
            DocumentCompanyLinkModel.document_type == "report",
            DocumentCompanyLinkModel.company_id == company.id,
            DocumentCompanyLinkModel.review_status == "accepted",
        )
            .order_by(
            ResearchReportModel.published_at.desc().nullslast(),
            ResearchReportModel.updated_at.desc(),
        )
    )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.limit(limit).offset(offset)).all()

    return success_response(
        data=[
            _report_to_dict(report, link)
            for report, link in rows
        ],
        meta=pagination_meta(limit=limit, offset=offset, total=total),
    )


@router.get("/{ticker_or_alias}/prices")
def company_prices(
        ticker_or_alias: str,
        limit: int = Query(default=252, ge=1, le=2000),
        offset: int = Query(default=0, ge=0),
        db: Session = Depends(db_dependency),
) -> dict:
    _, security = _find_company_bundle(db, ticker_or_alias)

    if security is None:
        raise HTTPException(
            status_code=404,
            detail=f"Security not found: {ticker_or_alias}",
        )

    stmt = (
        select(MarketPriceModel)
            .where(MarketPriceModel.security_id == security.id)
            .order_by(MarketPriceModel.price_date.desc())
    )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.limit(limit).offset(offset)).scalars().all()

    return success_response(
        data=[
            _price_to_dict(row)
            for row in reversed(rows)
        ],
        meta=pagination_meta(limit=limit, offset=offset, total=total),
    )
