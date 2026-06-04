from datetime import datetime, timezone
from typing import Iterator

from app.common.hashing import sha256_text
from app.infrastructure.http.client import get_json


class SecEdgarCollector:
    source_name = "sec_edgar"

    def __init__(
        self,
        cik: str,
        ticker: str,
        company_name: str,
        form_types: list[str] | None = None,
    ) -> None:
        self.cik = cik.zfill(10)
        self.ticker = ticker
        self.company_name = company_name
        self.form_types = form_types or ["10-K", "10-Q", "8-K"]

    @property
    def submissions_url(self) -> str:
        return f"https://data.sec.gov/submissions/CIK{self.cik}.json"

    def collect(self, limit: int = 10) -> Iterator[dict]:
        data = get_json(self.submissions_url)

        filings = data.get("filings", {}).get("recent", {})

        accession_numbers = filings.get("accessionNumber", [])
        filing_dates = filings.get("filingDate", [])
        report_dates = filings.get("reportDate", [])
        forms = filings.get("form", [])
        primary_documents = filings.get("primaryDocument", [])
        primary_doc_descriptions = filings.get("primaryDocDescription", [])

        count = 0

        for index, accession_number in enumerate(accession_numbers):
            form_type = forms[index]

            if form_type not in self.form_types:
                continue

            primary_document = primary_documents[index]
            filing_date = filing_dates[index]
            report_date = report_dates[index] if index < len(report_dates) else None
            description = (
                primary_doc_descriptions[index]
                if index < len(primary_doc_descriptions)
                else None
            )

            accession_no_dash = accession_number.replace("-", "")

            detail_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(self.cik)}/{accession_no_dash}/{primary_document}"
            )

            filing_page_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{int(self.cik)}/{accession_no_dash}/"
            )

            title = f"{self.company_name} {form_type} filing"

            content_hash = sha256_text(
                "|".join(
                    [
                        self.source_name,
                        accession_number,
                        self.company_name,
                        self.ticker,
                        form_type,
                        filing_date or "",
                        report_date or "",
                        primary_document or "",
                        detail_url,
                        description or "",
                    ]
                )
            )

            yield {
                "source": self.source_name,
                "report_id": accession_number,
                "company_name": self.company_name,
                "ticker": self.ticker,
                "title": title,
                "report_type": form_type,
                "published_at": self._parse_date(filing_date),
                "report_date": report_date,
                "authors": [],
                "detail_url": detail_url,
                "pdf_url": None,
                "pdf_local_path": None,
                "summary": description,
                "body_text": description or "",
                "content_hash": content_hash,
                "raw_json_url": self.submissions_url,
                "filing_page_url": filing_page_url,
            }

            count += 1
            if count >= limit:
                break

    def _parse_date(self, value: str | None) -> datetime | None:
        if not value:
            return None

        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)