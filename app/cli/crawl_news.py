from app.collectors.news.yahoo_finance import YahooFinanceNewsCollector
from app.common.hashing import sha256_text
from app.common.time_utils import utc_now
from app.infrastructure.storage.postgres import get_db_session, init_db
from app.pipeline.dedup import is_duplicate_article
from app.pipeline.normalize_news import normalize_news_article
from app.pipeline.raw_archive import archive_raw_html
from app.pipeline.state_tracker import update_crawl_state
from app.pipeline.upsert import insert_raw_document, upsert_news_article


def run_news_crawl_once() -> None:
    init_db()
    collector = YahooFinanceNewsCollector()
    db = get_db_session()

    try:
        for raw in collector.collect(limit=10):
            try:
                raw_hash = sha256_text(raw["html"])

                raw_path = archive_raw_html(
                    source=collector.source_name,
                    url=raw["url"],
                    html=raw["html"],
                )

                insert_raw_document(
                    db=db,
                    source=collector.source_name,
                    source_type="news_html",
                    url=raw["url"],
                    content_type="text/html",
                    content_hash=raw_hash,
                    fetched_at=utc_now(),
                    local_path=raw_path,
                )

                parsed = collector.parse(raw)
                extracted = collector.extract(parsed)
                normalized = normalize_news_article(extracted)

                duplicated = is_duplicate_article(
                    db=db,
                    source=normalized.source,
                    article_id=normalized.article_id,
                    content_hash=normalized.content_hash,
                )

                if not duplicated:
                    upsert_news_article(db, normalized)

                update_crawl_state(
                    db=db,
                    source=collector.source_name,
                    target_key=raw["url"],
                    content_hash=normalized.content_hash,
                    status="success",
                )

                print(f"[NEWS] url={raw['url']} duplicate={duplicated}")

            except Exception as exc:
                update_crawl_state(
                    db=db,
                    source=collector.source_name,
                    target_key=raw.get("url", "unknown"),
                    content_hash=None,
                    status="failed",
                    error_message=str(exc),
                )
                print(f"[NEWS ERROR] {exc}")

    finally:
        db.close()


if __name__ == "__main__":
    run_news_crawl_once()