from pathlib import Path

from app.collectors.reports.investor_relations_collector import InvestorRelationsReportCollector
from app.common.hashing import sha256_text
from app.common.time_utils import utc_now
from app.infrastructure.files.downloader import download_file
from app.infrastructure.pdf.pdf_reader import extract_pdf_text
from app.infrastructure.storage.postgres import get_db_session, init_db
from app.pipeline.dedup import is_duplicate_report
from app.pipeline.normalize_reports import normalize_research_report
from app.pipeline.raw_archive import archive_raw_html
from app.pipeline.state_tracker import update_crawl_state
from app.pipeline.upsert import insert_raw_document, upsert_research_report


def run_reports_crawl_once() -> None:
    init_db()

    collector = InvestorRelationsReportCollector(
        list_url="https://investor.apple.com/sec-filings/default.aspx"
    )

    db = get_db_session()

    try:
        for raw in collector.collect(limit=10):
            try:
                if raw.get("detail_html"):
                    raw_hash = sha256_text(raw["detail_html"])

                    raw_path = archive_raw_html(
                        source=collector.source_name,
                        url=raw["detail_url"],
                        html=raw["detail_html"],
                    )

                    insert_raw_document(
                        db=db,
                        source=collector.source_name,
                        source_type="report_detail_html",
                        url=raw["detail_url"],
                        content_type="text/html",
                        content_hash=raw_hash,
                        fetched_at=utc_now(),
                        local_path=raw_path,
                    )

                extracted = collector.extract(raw)

                pdf_url = extracted.get("pdf_url")
                if pdf_url:
                    filename = extracted["report_id"] + ".pdf"
                    local_pdf = str(Path("data/raw/reports") / filename)

                    download_file(pdf_url, local_pdf)
                    extracted["pdf_local_path"] = local_pdf

                    try:
                        pdf_text = extract_pdf_text(local_pdf)
                        if pdf_text:
                            extracted["body_text"] = pdf_text
                            extracted["summary"] = pdf_text[:500]
                    except Exception as exc:
                        print(f"[REPORT PDF WARN] {exc}")

                normalized = normalize_research_report(extracted)

                duplicated = is_duplicate_report(
                    db=db,
                    source=normalized.source,
                    report_id=normalized.report_id,
                    content_hash=normalized.content_hash,
                )

                if not duplicated:
                    upsert_research_report(db, normalized)

                update_crawl_state(
                    db=db,
                    source=collector.source_name,
                    target_key=raw["detail_url"],
                    content_hash=normalized.content_hash,
                    status="success",
                )

                print(f"[REPORT] url={raw['detail_url']} duplicate={duplicated}")

            except Exception as exc:
                update_crawl_state(
                    db=db,
                    source=collector.source_name,
                    target_key=raw.get("detail_url", "unknown"),
                    content_hash=None,
                    status="failed",
                    error_message=str(exc),
                )
                print(f"[REPORT ERROR] {exc}")

    finally:
        db.close()


if __name__ == "__main__":
    run_reports_crawl_once()