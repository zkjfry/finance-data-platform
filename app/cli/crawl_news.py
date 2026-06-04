from app.collectors.news.yahoo_finance import YahooFinanceNewsCollector
from app.collectors.news.yahoo_rss import YahooFinanceRssNewsCollector
from app.common.hashing import sha256_text
from app.common.time_utils import utc_now
from app.infrastructure.storage.postgres import get_db_session, init_db
from app.pipeline.crawl_run_logger import finish_crawl_run, start_crawl_run
from app.pipeline.dedup import is_duplicate_article
from app.pipeline.normalize_news import normalize_news_article
from app.pipeline.raw_archive import archive_raw_html
from app.pipeline.source_registry import enabled_news_sources
from app.pipeline.state_tracker import update_crawl_state
from app.pipeline.upsert import insert_raw_document, upsert_news_article


def _build_news_collector(source_config):
    if source_config.type == "yahoo_finance":
        collector = YahooFinanceNewsCollector(list_url=source_config.list_url)
        collector.source_name = source_config.name
        return collector

    if source_config.type == "yahoo_rss":
        collector = YahooFinanceRssNewsCollector(rss_url=source_config.rss_url)
        collector.source_name = source_config.name
        return collector

    raise ValueError(f"Unsupported news source type: {source_config.type}")


def run_news_crawl_once() -> dict:
    init_db()
    db = get_db_session()

    total_fetched = 0
    total_inserted = 0
    total_skipped = 0
    total_failed = 0
    source_results: list[dict] = []

    try:
        for source_config in enabled_news_sources():
            collector = _build_news_collector(source_config)
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
                    raw_items = list(collector.collect(limit=source_config.limit))
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

                        print(f"[NEWS] source={collector.source_name} url={raw['url']} duplicate={duplicated}")

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
                        print(f"[NEWS ERROR] source={collector.source_name} error={exc}")

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

            total_fetched += items_fetched
            total_inserted += items_inserted
            total_skipped += items_skipped
            total_failed += items_failed
            source_results.append(
                {
                    "source": collector.source_name,
                    "status": final_status,
                    "items_fetched": items_fetched,
                    "items_inserted": items_inserted,
                    "items_skipped": items_skipped,
                    "items_failed": items_failed,
                }
            )

        overall_status = "success" if total_failed == 0 else "partial_success"
        return {
            "status": overall_status,
            "items_fetched": total_fetched,
            "items_inserted": total_inserted,
            "items_skipped": total_skipped,
            "items_failed": total_failed,
            "sources": source_results,
        }

    finally:
        db.close()


if __name__ == "__main__":
    result = run_news_crawl_once()
    print(result)