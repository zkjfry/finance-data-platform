from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.response import pagination_meta, success_response
from app.infrastructure.storage.models import (
    CompanyModel,
    MarketPriceModel,
    SecurityModel,
)
from app.infrastructure.storage.postgres import get_db_session

router = APIRouter(prefix="/markets", tags=["markets"])


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


def _build_market_row(
    company: CompanyModel,
    security: SecurityModel,
    latest_price: MarketPriceModel | None,
    previous_price: MarketPriceModel | None,
) -> dict:
    latest_close = _to_float(latest_price.close) if latest_price else None
    previous_close = _to_float(previous_price.close) if previous_price else None

    change = None
    change_pct = None

    if latest_close is not None and previous_close:
        change = latest_close - previous_close
        change_pct = change / previous_close * 100

    return {
        "company_id": company.id,
        "company_name": company.canonical_name,
        "legal_name": company.legal_name,
        "sector": company.sector,
        "industry": company.industry,
        "country": company.country,
        "security_id": security.id,
        "ticker": security.ticker,
        "exchange": security.exchange,
        "currency": security.currency,
        "security_type": security.security_type,
        "price_date": latest_price.price_date.isoformat() if latest_price else None,
        "open": _to_float(latest_price.open) if latest_price else None,
        "high": _to_float(latest_price.high) if latest_price else None,
        "low": _to_float(latest_price.low) if latest_price else None,
        "close": latest_close,
        "adj_close": _to_float(latest_price.adj_close) if latest_price else None,
        "volume": latest_price.volume if latest_price else None,
        "previous_close": previous_close,
        "change": change,
        "change_pct": change_pct,
    }


@router.get("/securities")
def list_market_securities(
    keyword: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    sort_by: str = Query(default="ticker"),
    sort_dir: str = Query(default="asc"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(db_dependency),
) -> dict:
    """
    Return tracked primary securities with latest close and one-day movement.

    Supported sort_by:
    - ticker
    - company_name
    - sector
    - close
    - change_pct
    - volume
    """
    base_stmt = (
        select(CompanyModel, SecurityModel)
        .join(SecurityModel, SecurityModel.company_id == CompanyModel.id)
        .where(
            CompanyModel.is_active.is_(True),
            SecurityModel.is_primary.is_(True),
        )
    )

    count_stmt = (
        select(func.count())
        .select_from(CompanyModel)
        .join(SecurityModel, SecurityModel.company_id == CompanyModel.id)
        .where(
            CompanyModel.is_active.is_(True),
            SecurityModel.is_primary.is_(True),
        )
    )

    if keyword:
        keyword_like = f"%{keyword.strip().lower()}%"
        base_stmt = base_stmt.where(
            (func.lower(CompanyModel.canonical_name).like(keyword_like))
            | (func.lower(CompanyModel.legal_name).like(keyword_like))
            | (func.lower(SecurityModel.ticker).like(keyword_like))
        )
        count_stmt = count_stmt.where(
            (func.lower(CompanyModel.canonical_name).like(keyword_like))
            | (func.lower(CompanyModel.legal_name).like(keyword_like))
            | (func.lower(SecurityModel.ticker).like(keyword_like))
        )

    if sector:
        sector_like = f"%{sector.strip().lower()}%"
        base_stmt = base_stmt.where(func.lower(CompanyModel.sector).like(sector_like))
        count_stmt = count_stmt.where(func.lower(CompanyModel.sector).like(sector_like))

    total = db.execute(count_stmt).scalar_one()

    base_rows = db.execute(
        base_stmt.order_by(SecurityModel.ticker.asc())
    ).all()

    rows = []

    for company, security in base_rows:
        prices = db.execute(
            select(MarketPriceModel)
            .where(MarketPriceModel.security_id == security.id)
            .order_by(MarketPriceModel.price_date.desc())
            .limit(2)
        ).scalars().all()

        latest_price = prices[0] if prices else None
        previous_price = prices[1] if len(prices) > 1 else None

        rows.append(
            _build_market_row(
                company=company,
                security=security,
                latest_price=latest_price,
                previous_price=previous_price,
            )
        )

    reverse = sort_dir.lower() == "desc"

    def sort_value(row: dict):
        if sort_by == "company_name":
            return row.get("company_name") or ""
        if sort_by == "sector":
            return row.get("sector") or ""
        if sort_by == "close":
            return row.get("close") if row.get("close") is not None else -1
        if sort_by == "change_pct":
            return row.get("change_pct") if row.get("change_pct") is not None else -999999
        if sort_by == "volume":
            return row.get("volume") if row.get("volume") is not None else -1
        return row.get("ticker") or ""

    rows = sorted(rows, key=sort_value, reverse=reverse)
    paged_rows = rows[offset : offset + limit]

    return success_response(
        data=paged_rows,
        meta=pagination_meta(
            limit=limit,
            offset=offset,
            total=total,
        ),
    )