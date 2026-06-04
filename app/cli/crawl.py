import argparse
import traceback

from app.cli.crawl_news import run_news_crawl_once
from app.cli.crawl_reports import run_reports_crawl_once


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run finance data crawlers")
    parser.add_argument(
        "--target",
        choices=["news", "reports", "all"],
        required=True,
        help="Crawler target to run",
    )

    args = parser.parse_args()

    if args.target == "news":
        result = _safe_run("news", run_news_crawl_once)
        print(result)

    elif args.target == "reports":
        result = _safe_run("reports", run_reports_crawl_once)
        print(result)

    elif args.target == "all":
        news_result = _safe_run("news", run_news_crawl_once)
        reports_result = _safe_run("reports", run_reports_crawl_once)

        print(
            {
                "news": news_result,
                "reports": reports_result,
            }
        )


if __name__ == "__main__":
    main()