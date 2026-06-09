import json

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.domain.company_schemas import DocumentCompanyLink, MarketPrice
from app.domain.news_schemas import NewsArticle
from app.domain.report_schemas import ResearchReport
from app.infrastructure.storage.models import (
    DocumentCompanyLinkModel,
    MarketPriceModel,
    NewsArticleModel,
    RawDocumentModel,
    ResearchReportModel,
    SecurityModel,
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


def find_security_by_ticker(db: Session, ticker: str) -> SecurityModel | None:
    stmt = select(SecurityModel).where(SecurityModel.ticker == ticker.upper())
    return db.execute(stmt).scalar_one_or_none()


def upsert_market_price(db: Session, price: MarketPrice) -> MarketPriceModel:
    stmt = select(MarketPriceModel).where(
        MarketPriceModel.security_id == price.security_id,
        MarketPriceModel.price_date == price.price_date,
    )

    existing = db.execute(stmt).scalar_one_or_none()

    if existing is None:
        model = MarketPriceModel(
            security_id=price.security_id,
            price_date=price.price_date,
            open=price.open,
            high=price.high,
            low=price.low,
            close=price.close,
            adj_close=price.adj_close,
            volume=price.volume,
            source=price.source,
            inserted_at=price.inserted_at,
            updated_at=price.updated_at,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    existing.open = price.open
    existing.high = price.high
    existing.low = price.low
    existing.close = price.close
    existing.adj_close = price.adj_close
    existing.volume = price.volume
    existing.source = price.source
    existing.updated_at = price.updated_at

    db.commit()
    db.refresh(existing)
    return existing


def bulk_upsert_market_prices(
        db: Session,
        prices: list[MarketPrice],
) -> int:
    if not prices:
        return 0

    values = [
        {
            "security_id": price.security_id,
            "price_date": price.price_date,
            "open": price.open,
            "high": price.high,
            "low": price.low,
            "close": price.close,
            "adj_close": price.adj_close,
            "volume": price.volume,
            "source": price.source,
            "inserted_at": price.inserted_at,
            "updated_at": price.updated_at,
        }
        for price in prices
    ]

    stmt = insert(MarketPriceModel).values(values)

    update_columns = {
        "open": stmt.excluded.open,
        "high": stmt.excluded.high,
        "low": stmt.excluded.low,
        "close": stmt.excluded.close,
        "adj_close": stmt.excluded.adj_close,
        "volume": stmt.excluded.volume,
        "source": stmt.excluded.source,
        "updated_at": stmt.excluded.updated_at,
    }

    stmt = stmt.on_conflict_do_update(
        constraint="uq_market_prices_security_date",
        set_=update_columns,
    )

    db.execute(stmt)
    db.commit()

    return len(values)


def upsert_document_company_link(
        db: Session,
        link: DocumentCompanyLink,
) -> DocumentCompanyLinkModel:
    stmt = select(DocumentCompanyLinkModel).where(
        DocumentCompanyLinkModel.document_type == link.document_type,
        DocumentCompanyLinkModel.document_id == link.document_id,
        DocumentCompanyLinkModel.company_id == link.company_id,
    )

    existing = db.execute(stmt).scalar_one_or_none()

    if existing is None:
        model = DocumentCompanyLinkModel(
            document_type=link.document_type,
            document_id=link.document_id,
            company_id=link.company_id,
            security_id=link.security_id,
            ticker=link.ticker,
            match_method=link.match_method,
            evidence_text=link.evidence_text,
            review_status=link.review_status,
            confidence=link.confidence,
            inserted_at=link.inserted_at,
            updated_at=link.updated_at,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    # If the same document-company pair is matched again,
    # keep the stronger match.
    if link.confidence >= existing.confidence:
        existing.security_id = link.security_id
        existing.ticker = link.ticker
        existing.match_method = link.match_method
        existing.evidence_text = link.evidence_text
        existing.review_status = link.review_status
        existing.confidence = link.confidence

    existing.updated_at = link.updated_at

    db.commit()
    db.refresh(existing)
    return existing
