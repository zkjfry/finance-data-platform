from app.collectors.news.yahoo_finance import YahooFinanceNewsCollector
from app.common.hashing import sha256_text
from app.common.time_utils import utc_now
from app.infrastructure.storage.postgres import get_db_session, init_db
from app.pipeline.crawl_run_logger import finish_crawl_run, start_crawl_run
from app.pipeline.dedup import is_duplicate_article
from app.pipeline.normalize_news import normalize_news_article
from app.pipeline.raw_archive import archive_raw_html
from app.pipeline.state_tracker import update_crawl_state
from app.pipeline.upsert import insert_raw_document, upsert_news_article


def run_news_crawl_once() -> dict:
    init_db()
    collector = YahooFinanceNewsCollector()
    db = get_db_session()

    run = start_crawl_run(
        db=db,
        crawler_name="crawl_news",
        source=collector.source_name,
    )

    items_fetched = 0
    items_inserted = 0
    items_skipped = 0
    items_failed = 0
    fatal_error = None

    try:
        try:
            raw_items = list(collector.collect(limit=10))
            items_fetched = len(raw_items)
        except Exception as exc:
            fatal_error = str(exc)
            finish_crawl_run(
                db=db,
                run=run,
                status="failed",
                items_fetched=0,
                items_inserted=0,
                items_skipped=0,
                items_failed=1,
                error_message=fatal_error,
            )
            raise

        for raw in raw_items:
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

                if duplicated:
                    items_skipped += 1
                else:
                    upsert_news_article(db, normalized)
                    items_inserted += 1

                update_crawl_state(
                    db=db,
                    source=collector.source_name,
                    target_key=raw["url"],
                    content_hash=normalized.content_hash,
                    status="success",
                )

                print(f"[NEWS] url={raw['url']} duplicate={duplicated}")

            except Exception as exc:
                items_failed += 1
                update_crawl_state(
                    db=db,
                    source=collector.source_name,
                    target_key=raw.get("url", "unknown"),
                    content_hash=None,
                    status="failed",
                    error_message=str(exc),
                )
                print(f"[NEWS ERROR] {exc}")

        final_status = "success" if items_failed == 0 else "partial_success"

        finish_crawl_run(
            db=db,
            run=run,
            status=final_status,
            items_fetched=items_fetched,
            items_inserted=items_inserted,
            items_skipped=items_skipped,
            items_failed=items_failed,
        )

        return {
            "status": final_status,
            "items_fetched": items_fetched,
            "items_inserted": items_inserted,
            "items_skipped": items_skipped,
            "items_failed": items_failed,
        }

    except Exception as exc:
        if fatal_error is None:
            finish_crawl_run(
                db=db,
                run=run,
                status="failed",
                items_fetched=items_fetched,
                items_inserted=items_inserted,
                items_skipped=items_skipped,
                items_failed=items_failed + 1,
                error_message=str(exc),
            )
        raise

    finally:
        db.close()


if __name__ == "__main__":
    result = run_news_crawl_once()
    print(result)