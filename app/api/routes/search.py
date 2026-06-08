from datetime import datetime
from decimal import Decimal
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, literal, or_, select
from sqlalchemy.orm import Session

from app.api.response import success_response
from app.infrastructure.storage.models import (
    CompanyAliasModel,
    CompanyModel,
    NewsArticleModel,
    ResearchReportModel,
    SecurityModel,
)
from app.infrastructure.storage.postgres import get_db_session

router = APIRouter(prefix="/search", tags=["search"])


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


def _normalize_symbols(value) -> list[str]:
    """
    news_articles.symbols is stored as Text, but rows may contain JSON-like strings:
    - '["NVDA"]'
    - '[]'
    - 'NVDA'
    """
    if not value:
        return []

    if isinstance(value, list):
        return [str(item).upper() for item in value if item]

    raw = str(value).strip()

    if not raw or raw == "[]":
        return []

    try:
        parsed = json.loads(raw)

        if isinstance(parsed, list):
            return [str(item).upper() for item in parsed if item]

        if isinstance(parsed, str):
            return [parsed.upper()] if parsed else []
    except json.JSONDecodeError:
        pass

    cleaned = raw.strip("[]").replace('"', "").replace("'", "")
    values = [
        item.strip().upper()
        for item in cleaned.split(",")
        if item.strip()
    ]

    return values


def _news_vector():
    return func.to_tsvector(
        literal("english"),
        func.concat_ws(
            " ",
            func.coalesce(NewsArticleModel.title, ""),
            func.coalesce(NewsArticleModel.summary, ""),
            func.coalesce(NewsArticleModel.body_text, ""),
            func.coalesce(NewsArticleModel.symbols, ""),
        ),
    )


def _report_vector():
    return func.to_tsvector(
        literal("english"),
        func.concat_ws(
            " ",
            func.coalesce(ResearchReportModel.title, ""),
            func.coalesce(ResearchReportModel.summary, ""),
            func.coalesce(ResearchReportModel.body_text, ""),
            func.coalesce(ResearchReportModel.company_name, ""),
            func.coalesce(ResearchReportModel.ticker, ""),
            func.coalesce(ResearchReportModel.report_type, ""),
        ),
    )


def _company_to_result(company: CompanyModel, security: SecurityModel | None) -> dict:
    return {
        "type": "company",
        "id": company.id,
        "company_name": company.canonical_name,
        "legal_name": company.legal_name,
        "description": company.description,
        "sector": company.sector,
        "industry": company.industry,
        "country": company.country,
        "website": company.website,
        "ticker": security.ticker if security else None,
        "exchange": security.exchange if security else None,
        "currency": security.currency if security else None,
        "security_type": security.security_type if security else None,
    }


def _news_to_result(
        row: NewsArticleModel,
        relevance=None,
        matched_tickers: list[str] | None = None,
) -> dict:
    symbols = _normalize_symbols(row.symbols)
    display_symbols = symbols

    if not display_symbols and matched_tickers:
        text = " ".join(
            [
                row.title or "",
                row.summary or "",
                row.body_text or "",
                row.symbols or "",
            ]
        ).upper()

        display_symbols = [
            ticker
            for ticker in matched_tickers
            if ticker.upper() in text
        ]

    return {
        "type": "news",
        "id": row.id,
        "source": row.source,
        "article_id": row.article_id,
        "title": row.title,
        "url": row.url,
        "published_at": row.published_at,
        "symbols": display_symbols,
        "ticker": ", ".join(display_symbols) if display_symbols else None,
        "summary": row.summary,
        "relevance": _to_float(relevance) or 0,
    }


def _report_to_result(row: ResearchReportModel, relevance=None) -> dict:
    return {
        "type": "report",
        "id": row.id,
        "source": row.source,
        "report_id": row.report_id,
        "company_name": row.company_name,
        "ticker": row.ticker,
        "title": row.title,
        "report_type": row.report_type,
        "url": row.pdf_url or row.detail_url,
        "detail_url": row.detail_url,
        "pdf_url": row.pdf_url,
        "published_at": row.published_at,
        "summary": row.summary,
        "relevance": _to_float(relevance) or 0,
    }


def _detect_company_matches(db: Session, search_text: str):
    """
    Match company identity only:
    - company canonical name
    - legal name
    - ticker
    - alias

    Do NOT include sector / industry here.
    """
    keyword_like = f"%{search_text}%"

    return db.execute(
        select(CompanyModel, SecurityModel, CompanyAliasModel)
            .join(
            SecurityModel,
            (SecurityModel.company_id == CompanyModel.id)
            & (SecurityModel.is_primary.is_(True)),
            isouter=True,
        )
            .outerjoin(
            CompanyAliasModel,
            CompanyAliasModel.company_id == CompanyModel.id,
        )
            .where(
            or_(
                CompanyModel.canonical_name.ilike(keyword_like),
                CompanyModel.legal_name.ilike(keyword_like),
                SecurityModel.ticker.ilike(keyword_like),
                CompanyAliasModel.alias.ilike(keyword_like),
            )
        )
            .order_by(CompanyModel.canonical_name.asc())
    ).all()


def _detect_sector_matches(db: Session, search_text: str):
    """
    Match category intent:
    - sector
    - industry
    """
    keyword_like = f"%{search_text}%"

    return db.execute(
        select(CompanyModel, SecurityModel)
            .join(
            SecurityModel,
            (SecurityModel.company_id == CompanyModel.id)
            & (SecurityModel.is_primary.is_(True)),
            isouter=True,
        )
            .where(
            or_(
                CompanyModel.sector.ilike(keyword_like),
                CompanyModel.industry.ilike(keyword_like),
            )
        )
            .order_by(CompanyModel.canonical_name.asc())
    ).all()


def _dedupe_company_rows_with_alias(rows) -> list[tuple[CompanyModel, SecurityModel | None, CompanyAliasModel | None]]:
    seen_company_ids: set[int] = set()
    results = []

    for company, security, alias in rows:
        if company.id in seen_company_ids:
            continue

        seen_company_ids.add(company.id)
        results.append((company, security, alias))

    return results


def _dedupe_sector_rows(rows) -> list[tuple[CompanyModel, SecurityModel | None]]:
    seen_company_ids: set[int] = set()
    results = []

    for company, security in rows:
        if company.id in seen_company_ids:
            continue

        seen_company_ids.add(company.id)
        results.append((company, security))

    return results


def _is_exact_company_match(
        search_text: str,
        company: CompanyModel,
        security: SecurityModel | None,
        alias: CompanyAliasModel | None,
) -> bool:
    normalized_query = search_text.strip().lower()

    candidates = [
        company.canonical_name,
        company.legal_name,
        security.ticker if security else None,
        alias.alias if alias else None,
    ]

    normalized_candidates = {
        str(item).strip().lower()
        for item in candidates
        if item
    }

    return normalized_query in normalized_candidates


def _detect_search_intent(db: Session, search_text: str) -> dict:
    """
    Search intent rules:

    1. If query exactly matches a company/ticker/alias, treat as company intent.
       Example:
       - nvda
       - nvidia
       - NVIDIA Corporation

    2. If query partially matches company/ticker/alias, treat as company intent.
       Example:
       - nvid
       - micro

    3. If no company match but sector/industry matches, treat as sector intent.
       Example:
       - technology
       - semiconductors

    4. Otherwise, general intent.
    """
    company_rows = _detect_company_matches(db, search_text)
    sector_rows = _detect_sector_matches(db, search_text)

    exact_company_rows = [
        row
        for row in company_rows
        if _is_exact_company_match(
            search_text=search_text,
            company=row[0],
            security=row[1],
            alias=row[2],
        )
    ]

    if exact_company_rows:
        return {
            "intent": "company",
            "company_rows": _dedupe_company_rows_with_alias(exact_company_rows),
            "sector_rows": [],
        }

    if company_rows:
        return {
            "intent": "company",
            "company_rows": _dedupe_company_rows_with_alias(company_rows),
            "sector_rows": [],
        }

    if sector_rows:
        return {
            "intent": "sector",
            "company_rows": [],
            "sector_rows": _dedupe_sector_rows(sector_rows),
        }

    return {
        "intent": "general",
        "company_rows": [],
        "sector_rows": [],
    }


def _expand_search_terms_from_company_rows(
        search_text: str,
        company_rows,
) -> tuple[list[str], list[str]]:
    """
    Expand only from company identity fields.

    Example:
    nvidia -> nvidia, NVDA, NVIDIA, NVIDIA Corporation, NASDAQ:NVDA

    Important:
    Do NOT add sector / industry here.
    """
    terms: set[str] = {search_text}
    tickers: set[str] = set()

    for company, security, alias in company_rows:
        if company.canonical_name:
            terms.add(company.canonical_name)

        if company.legal_name:
            terms.add(company.legal_name)

        if security and security.ticker:
            terms.add(security.ticker)
            tickers.add(security.ticker.upper())

            if security.exchange:
                terms.add(f"{security.exchange}:{security.ticker}")

        if alias and alias.alias:
            terms.add(alias.alias)

    clean_terms = sorted(
        {
            term.strip()
            for term in terms
            if term and term.strip()
        },
        key=lambda item: (len(item), item.lower()),
    )

    clean_tickers = sorted(tickers)

    return clean_terms, clean_tickers


def _build_company_results_from_intent(
        db: Session,
        search_text: str,
        intent_info: dict,
        limit: int,
) -> list[dict]:
    intent = intent_info["intent"]

    if intent == "company":
        results = []

        for company, security, _alias in intent_info["company_rows"]:
            results.append(_company_to_result(company, security))

            if len(results) >= limit:
                break

        return results

    if intent == "sector":
        results = []

        for company, security in intent_info["sector_rows"]:
            results.append(_company_to_result(company, security))

            if len(results) >= limit:
                break

        return results

    keyword_like = f"%{search_text}%"

    rows = db.execute(
        select(CompanyModel, SecurityModel)
            .join(
            SecurityModel,
            (SecurityModel.company_id == CompanyModel.id)
            & (SecurityModel.is_primary.is_(True)),
            isouter=True,
        )
            .where(
            or_(
                CompanyModel.canonical_name.ilike(keyword_like),
                CompanyModel.legal_name.ilike(keyword_like),
                CompanyModel.description.ilike(keyword_like),
                CompanyModel.sector.ilike(keyword_like),
                CompanyModel.industry.ilike(keyword_like),
                SecurityModel.ticker.ilike(keyword_like),
            )
        )
            .order_by(CompanyModel.canonical_name.asc())
            .limit(limit)
    ).all()

    return [
        _company_to_result(company, security)
        for company, security in rows
    ]


def _build_keyword_filters(terms: list[str]) -> list[str]:
    return [
        f"%{term}%"
        for term in terms
        if term and term.strip()
    ]


@router.get("")
def global_search(
        q: str | None = Query(default=None),
        keyword: str | None = Query(default=None),
        source: str | None = Query(default=None),
        ticker: str | None = Query(default=None),
        start_date: datetime | None = Query(default=None),
        end_date: datetime | None = Query(default=None),
        limit: int = Query(default=8, ge=1, le=50),
        db: Session = Depends(db_dependency),
) -> dict:
    search_text = (q or keyword or "").strip()

    if not search_text:
        raise HTTPException(status_code=400, detail="Search keyword is required.")

    intent_info = _detect_search_intent(db, search_text)
    intent = intent_info["intent"]

    if intent == "company":
        expanded_terms, matched_tickers = _expand_search_terms_from_company_rows(
            search_text=search_text,
            company_rows=intent_info["company_rows"],
        )
    else:
        expanded_terms = [search_text]
        matched_tickers = []

    keyword_filters = _build_keyword_filters(expanded_terms)

    # --------------------
    # Companies
    # --------------------
    companies = _build_company_results_from_intent(
        db=db,
        search_text=search_text,
        intent_info=intent_info,
        limit=limit,
    )

    # --------------------
    # News
    # --------------------
    ts_query = func.websearch_to_tsquery(literal("english"), search_text)
    news_relevance = func.ts_rank_cd(_news_vector(), ts_query).label("relevance")

    news_conditions = [_news_vector().op("@@")(ts_query)]

    for pattern in keyword_filters:
        news_conditions.extend(
            [
                NewsArticleModel.title.ilike(pattern),
                NewsArticleModel.summary.ilike(pattern),
                NewsArticleModel.body_text.ilike(pattern),
                NewsArticleModel.symbols.ilike(pattern),
            ]
        )

    news_stmt = select(NewsArticleModel, news_relevance).where(
        or_(*news_conditions)
    )

    if source:
        news_stmt = news_stmt.where(NewsArticleModel.source == source)

    if ticker:
        news_stmt = news_stmt.where(NewsArticleModel.symbols.ilike(f"%{ticker}%"))

    if start_date:
        news_stmt = news_stmt.where(NewsArticleModel.published_at >= start_date)

    if end_date:
        news_stmt = news_stmt.where(NewsArticleModel.published_at <= end_date)

    news_stmt = (
        news_stmt
            .order_by(
            news_relevance.desc(),
            NewsArticleModel.published_at.desc().nullslast(),
        )
            .limit(limit)
    )

    news = [
        _news_to_result(row, relevance, matched_tickers)
        for row, relevance in db.execute(news_stmt).all()
    ]

    # --------------------
    # Reports
    # --------------------
    report_relevance = func.ts_rank_cd(_report_vector(), ts_query).label("relevance")

    report_conditions = [_report_vector().op("@@")(ts_query)]

    for pattern in keyword_filters:
        report_conditions.extend(
            [
                ResearchReportModel.title.ilike(pattern),
                ResearchReportModel.summary.ilike(pattern),
                ResearchReportModel.body_text.ilike(pattern),
                ResearchReportModel.company_name.ilike(pattern),
                ResearchReportModel.ticker.ilike(pattern),
                ResearchReportModel.report_type.ilike(pattern),
            ]
        )

    report_stmt = select(ResearchReportModel, report_relevance).where(
        or_(*report_conditions)
    )

    if source:
        report_stmt = report_stmt.where(ResearchReportModel.source == source)

    if ticker:
        report_stmt = report_stmt.where(
            ResearchReportModel.ticker.ilike(f"%{ticker}%")
        )

    if start_date:
        report_stmt = report_stmt.where(
            ResearchReportModel.published_at >= start_date
        )

    if end_date:
        report_stmt = report_stmt.where(
            ResearchReportModel.published_at <= end_date
        )

    report_stmt = (
        report_stmt
            .order_by(
            report_relevance.desc(),
            ResearchReportModel.published_at.desc().nullslast(),
        )
            .limit(limit)
    )

    reports = [
        _report_to_result(row, relevance)
        for row, relevance in db.execute(report_stmt).all()
    ]

    return success_response(
        data={
            "keyword": search_text,
            "intent": intent,
            "expanded_terms": expanded_terms,
            "matched_tickers": matched_tickers,
            "companies": companies,
            "news": news,
            "reports": reports,
            "total": len(companies) + len(news) + len(reports),
        },
        meta={
            "keyword": search_text,
            "intent": intent,
            "expanded_terms": expanded_terms,
            "matched_tickers": matched_tickers,
            "limit": limit,
            "counts": {
                "companies": len(companies),
                "news": len(news),
                "reports": len(reports),
            },
        },
    )
