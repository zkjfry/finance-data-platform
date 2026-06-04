from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.storage.models import Base
from config.settings import get_settings

settings = get_settings()

engine = create_engine(
    settings.sqlalchemy_database_url,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


SEARCH_INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles (published_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles (source)",
    "CREATE INDEX IF NOT EXISTS idx_news_articles_updated_at ON news_articles (updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_news_articles_content_hash ON news_articles (content_hash)",
    "CREATE INDEX IF NOT EXISTS idx_news_articles_symbols ON news_articles (symbols)",
    """
    CREATE INDEX IF NOT EXISTS idx_news_articles_fts ON news_articles USING GIN (
        to_tsvector(
            'english',
            coalesce(title, '') || ' ' ||
            coalesce(summary, '') || ' ' ||
            coalesce(body_text, '') || ' ' ||
            coalesce(symbols, '')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_research_reports_published_at ON research_reports (published_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_research_reports_source ON research_reports (source)",
    "CREATE INDEX IF NOT EXISTS idx_research_reports_ticker ON research_reports (ticker)",
    "CREATE INDEX IF NOT EXISTS idx_research_reports_company_name ON research_reports (company_name)",
    "CREATE INDEX IF NOT EXISTS idx_research_reports_updated_at ON research_reports (updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_research_reports_content_hash ON research_reports (content_hash)",
    """
    CREATE INDEX IF NOT EXISTS idx_research_reports_fts ON research_reports USING GIN (
        to_tsvector(
            'english',
            coalesce(title, '') || ' ' ||
            coalesce(summary, '') || ' ' ||
            coalesce(body_text, '') || ' ' ||
            coalesce(company_name, '') || ' ' ||
            coalesce(ticker, '') || ' ' ||
            coalesce(report_type, '')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_crawl_runs_source ON crawl_runs (source)",
    "CREATE INDEX IF NOT EXISTS idx_crawl_runs_status ON crawl_runs (status)",
    "CREATE INDEX IF NOT EXISTS idx_crawl_runs_started_at ON crawl_runs (started_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_companies_canonical_name ON companies (canonical_name)",
    "CREATE INDEX IF NOT EXISTS idx_company_aliases_alias ON company_aliases (alias)",
    "CREATE INDEX IF NOT EXISTS idx_securities_ticker ON securities (ticker)",
    "CREATE INDEX IF NOT EXISTS idx_securities_company_id ON securities (company_id)",
    "CREATE INDEX IF NOT EXISTS idx_market_prices_security_date ON market_prices (security_id, price_date DESC)",
    "CREATE INDEX IF NOT EXISTS idx_market_prices_source ON market_prices (source)",
]


def get_db_session() -> Session:
    return SessionLocal()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    create_indexes()
    seed_reference_data()


def create_indexes() -> None:
    with engine.begin() as conn:
        for statement in SEARCH_INDEX_STATEMENTS:
            conn.execute(text(statement))


def seed_reference_data() -> None:
    from app.pipeline.company_seed import seed_default_companies

    db = get_db_session()
    try:
        seed_default_companies(db)
    finally:
        db.close()