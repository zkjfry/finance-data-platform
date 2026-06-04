import json

from app.collectors.reports.sec_edgar_collector import SecEdgarCollector
from app.common.hashing import sha256_text
from app.common.time_utils import utc_now
from app.infrastructure.storage.postgres import get_db_session, init_db
from app.pipeline.crawl_run_logger import finish_crawl_run, start_crawl_run
from app.pipeline.dedup import is_duplicate_report
from app.pipeline.normalize_reports import normalize_research_report
from app.pipeline.state_tracker import update_crawl_state
from app.pipeline.upsert import insert_raw_document, upsert_research_report


def run_reports_crawl_once() -> dict:
    init_db()

    collector = SecEdgarCollector(
        cik="0000320193",
        ticker="AAPL",
        company_name="Apple Inc.",
        form_types=["10-K", "10-Q", "8-K"],
    )

    db = get_db_session()

    run = start_crawl_run(
        db=db,
        crawler_name="crawl_reports",
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
                raw_text = json.dumps(raw, ensure_ascii=False, default=str)
                raw_hash = sha256_text(raw_text)

                insert_raw_document(
                    db=db,
                    source=collector.source_name,
                    source_type="sec_filing_json",
                    url=raw["detail_url"],
                    content_type="application/json",
                    content_hash=raw_hash,
                    fetched_at=utc_now(),
                    local_path=None,
                    raw_text=raw_text,
                )

                normalized = normalize_research_report(raw)

                duplicated = is_duplicate_report(
                    db=db,
                    source=normalized.source,
                    report_id=normalized.report_id,
                    content_hash=normalized.content_hash,
                )

                if duplicated:
                    items_skipped += 1
                else:
                    upsert_research_report(db, normalized)
                    items_inserted += 1

                update_crawl_state(
                    db=db,
                    source=collector.source_name,
                    target_key=raw["detail_url"],
                    content_hash=normalized.content_hash,
                    status="success",
                )

                print(
                    f"[SEC REPORT] "
                    f"type={raw['report_type']} "
                    f"date={raw['published_at']} "
                    f"url={raw['detail_url']} "
                    f"duplicate={duplicated}"
                )

            except Exception as exc:
                items_failed += 1
                update_crawl_state(
                    db=db,
                    source=collector.source_name,
                    target_key=raw.get("detail_url", "unknown"),
                    content_hash=None,
                    status="failed",
                    error_message=str(exc),
                )
                print(f"[SEC REPORT ERROR] {exc}")

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
    result = run_reports_crawl_once()
    print(result)