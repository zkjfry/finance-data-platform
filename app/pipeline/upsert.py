import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.news_schemas import NewsArticle
from app.domain.report_schemas import ResearchReport
from app.infrastructure.storage.models import (
    NewsArticleModel,
    ResearchReportModel,
    RawDocumentModel,
)


def upsert_news_article(db: Session, article: NewsArticle) -> NewsArticleModel:
    stmt = select(NewsArticleModel).where(
        NewsArticleModel.source == article.source,
        NewsArticleModel.article_id == article.article_id,
    )

    existing = db.execute(stmt).scalar_one_or_none()

    if existing is None:
        model = NewsArticleModel(
            source=article.source,
            article_id=article.article_id,
            url=article.url,
            title=article.title,
            published_at=article.published_at,
            symbols=json.dumps(article.symbols),
            authors=json.dumps(article.authors),
            summary=article.summary,
            body_text=article.body_text,
            content_hash=article.content_hash,
            inserted_at=article.inserted_at,
            updated_at=article.updated_at,
        )

        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    existing.url = article.url
    existing.title = article.title
    existing.published_at = article.published_at
    existing.symbols = json.dumps(article.symbols)
    existing.authors = json.dumps(article.authors)
    existing.summary = article.summary
    existing.body_text = article.body_text
    existing.content_hash = article.content_hash
    existing.updated_at = article.updated_at

    db.commit()
    db.refresh(existing)
    return existing


def upsert_research_report(db: Session, report: ResearchReport) -> ResearchReportModel:
    stmt = select(ResearchReportModel).where(
        ResearchReportModel.source == report.source,
        ResearchReportModel.report_id == report.report_id,
    )

    existing = db.execute(stmt).scalar_one_or_none()

    if existing is None:
        model = ResearchReportModel(
            source=report.source,
            report_id=report.report_id,
            company_name=report.company_name,
            ticker=report.ticker,
            title=report.title,
            report_type=report.report_type,
            published_at=report.published_at,
            authors=json.dumps(report.authors),
            detail_url=report.detail_url,
            pdf_url=report.pdf_url,
            pdf_local_path=report.pdf_local_path,
            summary=report.summary,
            body_text=report.body_text,
            content_hash=report.content_hash,
            inserted_at=report.inserted_at,
            updated_at=report.updated_at,
        )

        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    existing.company_name = report.company_name
    existing.ticker = report.ticker
    existing.title = report.title
    existing.report_type = report.report_type
    existing.published_at = report.published_at
    existing.authors = json.dumps(report.authors)
    existing.detail_url = report.detail_url
    existing.pdf_url = report.pdf_url
    existing.pdf_local_path = report.pdf_local_path
    existing.summary = report.summary
    existing.body_text = report.body_text
    existing.content_hash = report.content_hash
    existing.updated_at = report.updated_at

    db.commit()
    db.refresh(existing)
    return existing


def insert_raw_document(
    db: Session,
    source: str,
    source_type: str,
    url: str,
    content_type: str,
    content_hash: str,
    fetched_at,
    local_path: str | None = None,
    raw_text: str | None = None,
) -> RawDocumentModel:
    model = RawDocumentModel(
        source=source,
        source_type=source_type,
        url=url,
        content_type=content_type,
        content_hash=content_hash,
        fetched_at=fetched_at,
        local_path=local_path,
        raw_text=raw_text,
    )

    db.add(model)
    db.commit()
    db.refresh(model)
    return model