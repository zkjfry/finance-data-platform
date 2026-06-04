from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RawDocumentModel(Base):
    __tablename__ = "raw_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(128), nullable=False)
    source_type = Column(String(128), nullable=False)
    url = Column(Text, nullable=False)
    content_type = Column(String(64), nullable=False)
    content_hash = Column(String(128), nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)
    local_path = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)


class NewsArticleModel(Base):
    __tablename__ = "news_articles"
    __table_args__ = (
        UniqueConstraint("source", "article_id", name="uq_news_source_article_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(128), nullable=False)
    article_id = Column(String(256), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    symbols = Column(Text, nullable=True)
    authors = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    content_hash = Column(String(128), nullable=False)
    inserted_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class ResearchReportModel(Base):
    __tablename__ = "research_reports"
    __table_args__ = (
        UniqueConstraint("source", "report_id", name="uq_reports_source_report_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(128), nullable=False)
    report_id = Column(String(256), nullable=False)
    company_name = Column(String(256), nullable=True)
    ticker = Column(String(64), nullable=True)
    title = Column(Text, nullable=False)
    report_type = Column(String(128), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    authors = Column(Text, nullable=True)
    detail_url = Column(Text, nullable=True)
    pdf_url = Column(Text, nullable=True)
    pdf_local_path = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    content_hash = Column(String(128), nullable=False)
    inserted_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class CrawlStateModel(Base):
    __tablename__ = "crawl_state"
    __table_args__ = (
        UniqueConstraint("source", "target_key", name="uq_crawl_state_source_target"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(128), nullable=False)
    target_key = Column(String(256), nullable=False)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_content_hash = Column(String(128), nullable=True)
    status = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)


class CrawlRunModel(Base):
    __tablename__ = "crawl_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crawler_name = Column(String(128), nullable=False)
    source = Column(String(128), nullable=False)
    status = Column(String(64), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    items_fetched = Column(Integer, nullable=False, default=0)
    items_inserted = Column(Integer, nullable=False, default=0)
    items_skipped = Column(Integer, nullable=False, default=0)
    items_failed = Column(Integer, nullable=False, default=0)

    error_message = Column(Text, nullable=True)


class CompanyModel(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("canonical_name", name="uq_companies_canonical_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_name = Column(String(256), nullable=False)
    legal_name = Column(String(256), nullable=True)
    description = Column(Text, nullable=True)
    sector = Column(String(128), nullable=True)
    industry = Column(String(128), nullable=True)
    country = Column(String(64), nullable=True)
    website = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    inserted_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class SecurityModel(Base):
    __tablename__ = "securities"
    __table_args__ = (
        UniqueConstraint("ticker", "exchange", name="uq_securities_ticker_exchange"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    ticker = Column(String(64), nullable=False)
    exchange = Column(String(64), nullable=True)
    currency = Column(String(16), nullable=True)
    security_type = Column(String(64), nullable=False, default="equity")
    is_primary = Column(Boolean, nullable=False, default=True)
    inserted_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class CompanyAliasModel(Base):
    __tablename__ = "company_aliases"
    __table_args__ = (
        UniqueConstraint("alias", name="uq_company_aliases_alias"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    alias = Column(String(256), nullable=False)
    alias_type = Column(String(64), nullable=False, default="name")
    inserted_at = Column(DateTime(timezone=True), nullable=False)


class MarketPriceModel(Base):
    __tablename__ = "market_prices"
    __table_args__ = (
        UniqueConstraint("security_id", "price_date", name="uq_market_prices_security_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    security_id = Column(Integer, ForeignKey("securities.id"), nullable=False)
    price_date = Column(Date, nullable=False)
    open = Column(Numeric(18, 6), nullable=True)
    high = Column(Numeric(18, 6), nullable=True)
    low = Column(Numeric(18, 6), nullable=True)
    close = Column(Numeric(18, 6), nullable=True)
    adj_close = Column(Numeric(18, 6), nullable=True)
    volume = Column(BigInteger, nullable=True)
    source = Column(String(128), nullable=False)
    inserted_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

class DocumentCompanyLinkModel(Base):
    __tablename__ = "document_company_links"
    __table_args__ = (
        UniqueConstraint(
            "document_type",
            "document_id",
            "company_id",
            name="uq_document_company_link_document_company",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # "news" or "report"
    document_type = Column(String(32), nullable=False)

    # news_articles.id or research_reports.id
    document_id = Column(Integer, nullable=False)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    security_id = Column(Integer, ForeignKey("securities.id"), nullable=True)

    ticker = Column(String(64), nullable=True)

    # ticker / company_name / alias / body_alias / manual / etc.
    match_method = Column(String(64), nullable=False)

    # Short text explaining why this link was created.
    evidence_text = Column(Text, nullable=True)

    # accepted / pending / rejected
    review_status = Column(String(32), nullable=False, default="pending")

    # 0.0000 - 1.0000
    confidence = Column(Numeric(5, 4), nullable=False)

    inserted_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)