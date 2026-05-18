from app.domain.news_schemas import NewsArticle
from app.common.time_utils import utc_now


def normalize_news_article(source_record: dict) -> NewsArticle:
    now = utc_now()

    return NewsArticle(
        source=source_record["source"],
        article_id=source_record["article_id"],
        url=source_record["url"],
        title=source_record["title"],
        published_at=source_record.get("published_at"),
        symbols=source_record.get("symbols", []),
        authors=source_record.get("authors", []),
        summary=source_record.get("summary"),
        body_text=source_record.get("body_text"),
        content_hash=source_record["content_hash"],
        inserted_at=now,
        updated_at=now,
    )