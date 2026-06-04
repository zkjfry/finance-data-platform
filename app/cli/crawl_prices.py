from app.collectors.prices.yfinance_price import YFinancePriceCollector
from app.common.time_utils import utc_now
from app.domain.company_schemas import MarketPrice
from app.infrastructure.storage.postgres import get_db_session, init_db
from app.pipeline.crawl_run_logger import finish_crawl_run, start_crawl_run
from app.pipeline.source_registry import enabled_price_sources
from app.pipeline.state_tracker import update_crawl_state
from app.pipeline.upsert import find_security_by_ticker, upsert_market_price


def run_prices_crawl_once() -> dict:
    init_db()
    db = get_db_session()

    total_fetched = 0
    total_inserted = 0
    total_skipped = 0
    total_failed = 0
    source_results: list[dict] = []

    try:
        for source_config in enabled_price_sources():
            run = start_crawl_run(
                db=db,
                crawler_name="crawl_prices",
                source=source_config.name,
            )

            items_fetched = 0
            items_inserted = 0
            items_skipped = 0
            items_failed = 0
            final_status = "success"

            try:
                for ticker in source_config.tickers:
                    ticker = ticker.upper()
                    security = find_security_by_ticker(db, ticker)

                    if security is None:
                        items_failed += 1
                        update_crawl_state(
                            db=db,
                            source=source_config.name,
                            target_key=ticker,
                            content_hash=None,
                            status="failed",
                            error_message=f"Security not found for ticker: {ticker}",
                        )
                        print(f"[PRICE ERROR] ticker={ticker} error=security_not_found")
                        continue

                    try:
                        collector = YFinancePriceCollector(
                            ticker=ticker,
                            source_name=source_config.name,
                            period=source_config.period,
                            interval=source_config.interval,
                            start_date=source_config.start_date,
                            end_date=source_config.end_date,
                        )

                        raw_prices = collector.collect()
                        items_fetched += len(raw_prices)

                        for raw in raw_prices:
                            now = utc_now()
                            price = MarketPrice(
                                security_id=security.id,
                                price_date=raw["price_date"],
                                open=raw.get("open"),
                                high=raw.get("high"),
                                low=raw.get("low"),
                                close=raw.get("close"),
                                adj_close=raw.get("adj_close"),
                                volume=raw.get("volume"),
                                source=raw["source"],
                                inserted_at=now,
                                updated_at=now,
                            )
                            upsert_market_price(db, price)
                            items_inserted += 1

                        update_crawl_state(
                            db=db,
                            source=source_config.name,
                            target_key=ticker,
                            content_hash=None,
                            status="success",
                        )

                        print(
                            f"[PRICE] source={source_config.name} "
                            f"ticker={ticker} rows={len(raw_prices)}"
                        )

                    except Exception as exc:
                        items_failed += 1
                        update_crawl_state(
                            db=db,
                            source=source_config.name,
                            target_key=ticker,
                            content_hash=None,
                            status="failed",
                            error_message=str(exc),
                        )
                        print(f"[PRICE ERROR] ticker={ticker} error={exc}")

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
                    "source": source_config.name,
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
    result = run_prices_crawl_once()
    print(result)