from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
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