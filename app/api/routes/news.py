from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, literal, or_, select
from sqlalchemy.orm import Session

from app.api.response import pagination_meta, success_response
from app.infrastructure.storage.postgres import get_db_session
from app.infrastructure.storage.models import NewsArticleModel

import json

router = APIRouter(prefix="/news", tags=["news"])


def db_dependency():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _news_to_dict(row: NewsArticleModel, relevance: float | None = None) -> dict:
    result = {
        "id": row.id,
        "source": row.source,
        "article_id": row.article_id,
        "url": row.url,
        "title": row.title,
        "published_at": row.published_at,
        "symbols": _json_list(row.symbols),
        "authors": _json_list(row.authors),
        "summary": row.summary,
        "body_text": row.body_text,
        "updated_at": row.updated_at,
    }

    if relevance is not None:
        result["relevance"] = float(relevance)

    return result


def _news_search_vector():
    searchable_text = func.concat_ws(
        " ",
        func.coalesce(NewsArticleModel.title, ""),
        func.coalesce(NewsArticleModel.summary, ""),
        func.coalesce(NewsArticleModel.body_text, ""),
        func.coalesce(NewsArticleModel.symbols, ""),
    )

    return func.to_tsvector(literal("english"), searchable_text)


@router.get("/search")
@router.get("")
def search_news(
        keyword: str | None = Query(default=None),
        source: str | None = Query(default=None),
        symbol: str | None = Query(default=None),
        start_date: datetime | None = Query(default=None),
        end_date: datetime | None = Query(default=None),
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        db: Session = Depends(db_dependency),
) -> dict:
    stmt = select(NewsArticleModel)

    if keyword:
        ts_query = func.websearch_to_tsquery(literal("english"), keyword)
        search_vector = _news_search_vector()
        relevance = func.ts_rank_cd(search_vector, ts_query).label("relevance")

        stmt = select(NewsArticleModel, relevance)

        keyword_like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                search_vector.op("@@")(ts_query),
                NewsArticleModel.title.ilike(keyword_like),
                NewsArticleModel.summary.ilike(keyword_like),
                NewsArticleModel.body_text.ilike(keyword_like),
                NewsArticleModel.symbols.ilike(keyword_like),
            )
        )
    else:
        relevance = None

    if source:
        stmt = stmt.where(NewsArticleModel.source == source)

    if symbol:
        stmt = stmt.where(NewsArticleModel.symbols.ilike(f"%{symbol}%"))

    if start_date:
        stmt = stmt.where(NewsArticleModel.published_at >= start_date)

    if end_date:
        stmt = stmt.where(NewsArticleModel.published_at <= end_date)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    if keyword:
        stmt = stmt.order_by(
            relevance.desc(),
            NewsArticleModel.published_at.desc().nullslast(),
            NewsArticleModel.updated_at.desc(),
        )
    else:
        stmt = stmt.order_by(
            NewsArticleModel.published_at.desc().nullslast(),
            NewsArticleModel.updated_at.desc(),
        )

    rows = db.execute(stmt.limit(limit).offset(offset)).all()

    if keyword:
        data = [_news_to_dict(row[0], row[1]) for row in rows]
    else:
        data = [_news_to_dict(row[0]) for row in rows]

    return success_response(
        data=data,
        meta=pagination_meta(limit=limit, offset=offset, total=total),
    )


@router.get("/latest")
def latest_news(
        limit: int = Query(default=20, ge=1, le=100),
        db: Session = Depends(db_dependency),
) -> dict:
    stmt = (
        select(NewsArticleModel)
            .order_by(NewsArticleModel.updated_at.desc())
            .limit(limit)
    )

    rows = db.execute(stmt).scalars().all()
    data = [_news_to_dict(row) for row in rows]

    return success_response(data=data, meta={"limit": limit})
