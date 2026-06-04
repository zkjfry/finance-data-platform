from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from config.settings import get_settings
from app.infrastructure.storage.models import Base

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
]


def get_db_session() -> Session:
    return SessionLocal()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    create_indexes()


def create_indexes() -> None:
    with engine.begin() as conn:
        for statement in SEARCH_INDEX_STATEMENTS:
            conn.execute(text(statement))