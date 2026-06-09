import argparse
import sys
import traceback

from app.cli.crawl_news import run_news_crawl_once
from app.cli.crawl_prices import run_prices_crawl_once
from app.cli.crawl_reports import run_reports_crawl_once
from app.cli.link_companies import run_company_linking_once

FAILED_STATUSES = {"failed", "partial_success"}


def _safe_run(name: str, func):
    try:
        return func()
    except Exception as exc:
        return {
            "status": "failed",
            "target": name,
            "error_message": str(exc),
            "traceback": traceback.format_exc(),
        }


def _is_failed_result(result: dict) -> bool:
    return result.get("status") in FAILED_STATUSES


def main() -> None:
    parser = argparse.ArgumentParser(description="Run finance data platform jobs")
    parser.add_argument(
        "--target",
        choices=["news", "reports", "prices", "link_companies", "all"],
        required=True,
        help="Job target to run",
    )

    args = parser.parse_args()
    exit_code = 0

    if args.target == "news":
        result = _safe_run("news", run_news_crawl_once)
        print(result)
        if _is_failed_result(result):
            exit_code = 1

    elif args.target == "reports":
        result = _safe_run("reports", run_reports_crawl_once)
        print(result)
        if _is_failed_result(result):
            exit_code = 1

    elif args.target == "prices":
        result = _safe_run("prices", run_prices_crawl_once)
        print(result)
        if _is_failed_result(result):
            exit_code = 1

    elif args.target == "link_companies":
        result = _safe_run("link_companies", run_company_linking_once)
        print(result)
        if _is_failed_result(result):
            exit_code = 1

    elif args.target == "all":
        news_result = _safe_run("news", run_news_crawl_once)
        reports_result = _safe_run("reports", run_reports_crawl_once)
        prices_result = _safe_run("prices", run_prices_crawl_once)
        link_result = _safe_run("link_companies", run_company_linking_once)

        result = {
            "news": news_result,
            "reports": reports_result,
            "prices": prices_result,
            "link_companies": link_result,
        }

        print(result)

        if any(
                _is_failed_result(item)
                for item in result.values()
        ):
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
