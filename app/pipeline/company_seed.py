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
    {
        "canonical_name": "Alphabet Inc.",
        "legal_name": "Alphabet Inc.",
        "sector": "Communication Services",
        "industry": "Internet Content & Information",
        "country": "US",
        "website": "https://abc.xyz",
        "ticker": "GOOGL",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Alphabet", "Google", "Google Inc", "GOOGL", "NASDAQ:GOOGL"],
    },
    {
        "canonical_name": "Meta Platforms, Inc.",
        "legal_name": "Meta Platforms, Inc.",
        "sector": "Communication Services",
        "industry": "Internet Content & Information",
        "country": "US",
        "website": "https://www.meta.com",
        "ticker": "META",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Meta", "Facebook", "Meta Platforms", "META", "NASDAQ:META"],
    },
    {
        "canonical_name": "Netflix, Inc.",
        "legal_name": "Netflix, Inc.",
        "sector": "Communication Services",
        "industry": "Entertainment",
        "country": "US",
        "website": "https://www.netflix.com",
        "ticker": "NFLX",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Netflix", "Netflix Inc", "NFLX", "NASDAQ:NFLX"],
    },
    {
        "canonical_name": "Advanced Micro Devices, Inc.",
        "legal_name": "Advanced Micro Devices, Inc.",
        "sector": "Technology",
        "industry": "Semiconductors",
        "country": "US",
        "website": "https://www.amd.com",
        "ticker": "AMD",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["AMD", "Advanced Micro Devices", "NASDAQ:AMD"],
    },
    {
        "canonical_name": "Intel Corporation",
        "legal_name": "Intel Corporation",
        "sector": "Technology",
        "industry": "Semiconductors",
        "country": "US",
        "website": "https://www.intel.com",
        "ticker": "INTC",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Intel", "Intel Corp", "INTC", "NASDAQ:INTC"],
    },
    {
        "canonical_name": "JPMorgan Chase & Co.",
        "legal_name": "JPMorgan Chase & Co.",
        "sector": "Financial Services",
        "industry": "Banks - Diversified",
        "country": "US",
        "website": "https://www.jpmorganchase.com",
        "ticker": "JPM",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["JPMorgan", "JP Morgan", "JPMorgan Chase", "JPM", "NYSE:JPM"],
    },
    {
        "canonical_name": "Bank of America Corporation",
        "legal_name": "Bank of America Corporation",
        "sector": "Financial Services",
        "industry": "Banks - Diversified",
        "country": "US",
        "website": "https://www.bankofamerica.com",
        "ticker": "BAC",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Bank of America", "BofA", "BAC", "NYSE:BAC"],
    },
    {
        "canonical_name": "The Goldman Sachs Group, Inc.",
        "legal_name": "The Goldman Sachs Group, Inc.",
        "sector": "Financial Services",
        "industry": "Capital Markets",
        "country": "US",
        "website": "https://www.goldmansachs.com",
        "ticker": "GS",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Goldman Sachs", "Goldman", "GS", "NYSE:GS"],
    },
    {
        "canonical_name": "Morgan Stanley",
        "legal_name": "Morgan Stanley",
        "sector": "Financial Services",
        "industry": "Capital Markets",
        "country": "US",
        "website": "https://www.morganstanley.com",
        "ticker": "MS",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Morgan Stanley", "MS", "NYSE:MS"],
    },
    {
        "canonical_name": "Visa Inc.",
        "legal_name": "Visa Inc.",
        "sector": "Financial Services",
        "industry": "Credit Services",
        "country": "US",
        "website": "https://www.visa.com",
        "ticker": "V",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Visa", "Visa Inc", "V", "NYSE:V"],
    },
    {
        "canonical_name": "Mastercard Incorporated",
        "legal_name": "Mastercard Incorporated",
        "sector": "Financial Services",
        "industry": "Credit Services",
        "country": "US",
        "website": "https://www.mastercard.com",
        "ticker": "MA",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Mastercard", "MasterCard", "MA", "NYSE:MA"],
    },
    {
        "canonical_name": "Walmart Inc.",
        "legal_name": "Walmart Inc.",
        "sector": "Consumer Defensive",
        "industry": "Discount Stores",
        "country": "US",
        "website": "https://www.walmart.com",
        "ticker": "WMT",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Walmart", "Wal-Mart", "WMT", "NYSE:WMT"],
    },
    {
        "canonical_name": "Costco Wholesale Corporation",
        "legal_name": "Costco Wholesale Corporation",
        "sector": "Consumer Defensive",
        "industry": "Discount Stores",
        "country": "US",
        "website": "https://www.costco.com",
        "ticker": "COST",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Costco", "Costco Wholesale", "COST", "NASDAQ:COST"],
    },
    {
        "canonical_name": "The Walt Disney Company",
        "legal_name": "The Walt Disney Company",
        "sector": "Communication Services",
        "industry": "Entertainment",
        "country": "US",
        "website": "https://www.disney.com",
        "ticker": "DIS",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Disney", "Walt Disney", "DIS", "NYSE:DIS"],
    },
    {
        "canonical_name": "The Coca-Cola Company",
        "legal_name": "The Coca-Cola Company",
        "sector": "Consumer Defensive",
        "industry": "Beverages - Non-Alcoholic",
        "country": "US",
        "website": "https://www.coca-colacompany.com",
        "ticker": "KO",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Coca-Cola", "Coca Cola", "Coke", "KO", "NYSE:KO"],
    },
    {
        "canonical_name": "PepsiCo, Inc.",
        "legal_name": "PepsiCo, Inc.",
        "sector": "Consumer Defensive",
        "industry": "Beverages - Non-Alcoholic",
        "country": "US",
        "website": "https://www.pepsico.com",
        "ticker": "PEP",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["PepsiCo", "Pepsi", "PEP", "NASDAQ:PEP"],
    },
    {
        "canonical_name": "NIKE, Inc.",
        "legal_name": "NIKE, Inc.",
        "sector": "Consumer Cyclical",
        "industry": "Footwear & Accessories",
        "country": "US",
        "website": "https://www.nike.com",
        "ticker": "NKE",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Nike", "NIKE", "NKE", "NYSE:NKE"],
    },
    {
        "canonical_name": "Salesforce, Inc.",
        "legal_name": "Salesforce, Inc.",
        "sector": "Technology",
        "industry": "Software - Application",
        "country": "US",
        "website": "https://www.salesforce.com",
        "ticker": "CRM",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Salesforce", "Salesforce.com", "CRM", "NYSE:CRM"],
    },
    {
        "canonical_name": "Oracle Corporation",
        "legal_name": "Oracle Corporation",
        "sector": "Technology",
        "industry": "Software - Infrastructure",
        "country": "US",
        "website": "https://www.oracle.com",
        "ticker": "ORCL",
        "exchange": "NYSE",
        "currency": "USD",
        "aliases": ["Oracle", "Oracle Corp", "ORCL", "NYSE:ORCL"],
    },
    {
        "canonical_name": "Broadcom Inc.",
        "legal_name": "Broadcom Inc.",
        "sector": "Technology",
        "industry": "Semiconductors",
        "country": "US",
        "website": "https://www.broadcom.com",
        "ticker": "AVGO",
        "exchange": "NASDAQ",
        "currency": "USD",
        "aliases": ["Broadcom", "Broadcom Inc", "AVGO", "NASDAQ:AVGO"],
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