from app.common.time_utils import utc_now
from app.domain.report_schemas import ResearchReport


def normalize_research_report(source_record: dict) -> ResearchReport:
    now = utc_now()

    return ResearchReport(
        source=source_record["source"],
        report_id=source_record["report_id"],
        company_name=source_record.get("company_name"),
        ticker=source_record.get("ticker"),
        title=source_record["title"],
        report_type=source_record.get("report_type"),
        published_at=source_record.get("published_at"),
        authors=source_record.get("authors", []),
        detail_url=source_record.get("detail_url"),
        pdf_url=source_record.get("pdf_url"),
        pdf_local_path=source_record.get("pdf_local_path"),
        summary=source_record.get("summary"),
        body_text=source_record.get("body_text"),
        content_hash=source_record["content_hash"],
        inserted_at=now,
        updated_at=now,
    )