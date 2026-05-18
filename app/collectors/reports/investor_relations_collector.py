from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from app.collectors.reports.base_report_collector import BaseReportCollector
from app.infrastructure.http.client import get_html
from app.common.hashing import sha256_text
from app.common.utils import clean_text


class InvestorRelationsReportCollector(BaseReportCollector):
    source_name = "investor_relations_reports"

    def __init__(self, list_url: str, base_url: str | None = None):
        self.list_url = list_url
        self.base_url = base_url or self._infer_base_url(list_url)

    def _infer_base_url(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def discover_reports(self, limit: int = 20) -> list[dict]:
        html = get_html(self.list_url)
        soup = BeautifulSoup(html, "lxml")

        reports = []
        seen = set()

        keywords = [
            "annual report",
            "quarterly",
            "10-k",
            "10-q",
            "filing",
            "pdf",
            "report",
        ]

        for a in soup.find_all("a", href=True):
            text = clean_text(a.get_text())
            href = a["href"].strip()
            full_url = urljoin(self.base_url, href)

            text_lower = text.lower()
            href_lower = full_url.lower()

            if not any(k in text_lower or k in href_lower for k in keywords):
                continue

            if full_url in seen:
                continue

            seen.add(full_url)

            reports.append(
                {
                    "title_hint": text or "Untitled report",
                    "detail_url": full_url,
                }
            )

            if len(reports) >= limit:
                break

        return reports

    def fetch_detail(self, item: dict) -> dict:
        detail_url = item["detail_url"]

        if detail_url.lower().endswith(".pdf"):
            return {
                "title_hint": item["title_hint"],
                "detail_url": detail_url,
                "pdf_url": detail_url,
                "detail_html": None,
            }

        html = get_html(detail_url)

        return {
            "title_hint": item["title_hint"],
            "detail_url": detail_url,
            "pdf_url": self._extract_pdf_url(html, detail_url),
            "detail_html": html,
        }

    def _extract_pdf_url(self, html: str, detail_url: str) -> str | None:
        soup = BeautifulSoup(html, "lxml")

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urljoin(detail_url, href)

            if full_url.lower().endswith(".pdf"):
                return full_url

        return None

    def extract(self, raw: dict) -> dict:
        title = raw["title_hint"]
        body_text = None

        if raw.get("detail_html"):
            soup = BeautifulSoup(raw["detail_html"], "lxml")

            h1 = soup.find("h1")
            if h1:
                extracted_title = clean_text(h1.get_text())
                if extracted_title:
                    title = extracted_title

            paragraphs = []
            for p in soup.find_all("p"):
                text = clean_text(p.get_text())
                if text:
                    paragraphs.append(text)

            if paragraphs:
                body_text = "\n".join(paragraphs)

        stable_key = raw.get("pdf_url") or raw["detail_url"]
        report_id = sha256_text(stable_key)[:24]

        content_hash = sha256_text(
            f"{title}\n{raw.get('detail_url')}\n{raw.get('pdf_url')}\n{body_text or ''}"
        )

        return {
            "source": self.source_name,
            "report_id": report_id,
            "company_name": None,
            "ticker": None,
            "title": title,
            "report_type": None,
            "published_at": None,
            "authors": [],
            "detail_url": raw.get("detail_url"),
            "pdf_url": raw.get("pdf_url"),
            "pdf_local_path": None,
            "summary": body_text[:500] if body_text else None,
            "body_text": body_text,
            "content_hash": content_hash,
        }