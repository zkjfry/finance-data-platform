from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.time_utils import utc_now
from app.infrastructure.storage.models import CompanyAliasModel, CompanyModel, SecurityModel

DEFAULT_COMPANIES = [
    {
        "canonical_name": "Apple Inc.",
        "legal_name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "country": "US",
        "website": "https://www.apple.com",
        "ticker": "AAPL",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Apple", "Apple Inc", "AAPL", "NASDAQ:AAPL"],
    },
    {
        "canonical_name": "Microsoft Corporation",
        "legal_name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software",
        "country": "US",
        "website": "https://www.microsoft.com",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Microsoft", "Microsoft Corp", "MSFT", "NASDAQ:MSFT"],
    },
    {
        "canonical_name": "NVIDIA Corporation",
        "legal_name": "NVIDIA Corporation",
        "sector": "Technology",
        "industry": "Semiconductors",
        "country": "US",
        "website": "https://www.nvidia.com",
        "ticker": "NVDA",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Nvidia", "NVIDIA", "NVDA", "NASDAQ:NVDA"],
    },
    {
        "canonical_name": "Tesla, Inc.",
        "legal_name": "Tesla, Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Auto Manufacturers",
        "country": "US",
        "website": "https://www.tesla.com",
        "ticker": "TSLA",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Tesla", "Tesla Inc", "TSLA", "NASDAQ:TSLA"],
    },
    {
        "canonical_name": "Amazon.com, Inc.",
        "legal_name": "Amazon.com, Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Internet Retail",
        "country": "US",
        "website": "https://www.amazon.com",
        "ticker": "AMZN",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Amazon", "Amazon.com", "Amazon Inc", "AMZN", "NASDAQ:AMZN"],
    },
]


def seed_default_companies(db: Session) -> None:
    for item in DEFAULT_COMPANIES:
        company = _upsert_company(db, item)
        security = _upsert_security(db, company.id, item)
        _upsert_aliases(db, company.id, item, security.ticker, security.exchange)

    db.commit()


def _upsert_company(db: Session, item: dict) -> CompanyModel:
    now = utc_now()

    existing = db.execute(
        select(CompanyModel).where(
            CompanyModel.canonical_name == item["canonical_name"]
        )
    ).scalar_one_or_none()

    if existing is None:
        company = CompanyModel(
            canonical_name=item["canonical_name"],
            legal_name=item.get("legal_name"),
            sector=item.get("sector"),
            industry=item.get("industry"),
            country=item.get("country"),
            website=item.get("website"),
            is_active=True,
            inserted_at=now,
            updated_at=now,
        )
        db.add(company)
        db.flush()
        return company

    existing.legal_name = item.get("legal_name")
    existing.sector = item.get("sector")
    existing.industry = item.get("industry")
    existing.country = item.get("country")
    existing.website = item.get("website")
    existing.is_active = True
    existing.updated_at = now
    db.flush()
    return existing


def _upsert_security(db: Session, company_id: int, item: dict) -> SecurityModel:
    now = utc_now()
    ticker = item["ticker"].upper()
    exchange = item.get("exchange")

    existing = db.execute(
        select(SecurityModel).where(
            SecurityModel.ticker == ticker,
            SecurityModel.exchange == exchange,
        )
    ).scalar_one_or_none()

    if existing is None:
        security = SecurityModel(
            company_id=company_id,
            ticker=ticker,
            exchange=exchange,
            currency=item.get("currency", "USD"),
            security_type="equity",
            is_primary=True,
            inserted_at=now,
            updated_at=now,
        )
        db.add(security)
        db.flush()
        return security

    existing.company_id = company_id
    existing.currency = item.get("currency", "USD")
    existing.security_type = "equity"
    existing.is_primary = True
    existing.updated_at = now
    db.flush()
    return existing


def _upsert_aliases(
    db: Session,
    company_id: int,
    item: dict,
    ticker: str,
    exchange: str | None,
) -> None:
    aliases = set(item.get("aliases", []))
    aliases.add(item["canonical_name"])
    aliases.add(ticker)

    if exchange:
        aliases.add(f"{exchange}:{ticker}")

    for alias_value in aliases:
        alias_value = alias_value.strip()
        if not alias_value:
            continue

        existing = db.execute(
            select(CompanyAliasModel).where(
                CompanyAliasModel.alias == alias_value
            )
        ).scalar_one_or_none()

        if existing is None:
            db.add(
                CompanyAliasModel(
                    company_id=company_id,
                    alias=alias_value,
                    alias_type="ticker" if alias_value.upper() == ticker else "name",
                    inserted_at=utc_now(),
                )
            )
        else:
            existing.company_id = company_id