from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.infrastructure.http.client import get_html
from app.collectors.news.parser import parse_article_html
from app.collectors.news.extractor import extract_article_fields


class YahooFinanceNewsCollector(BaseCollector):
    source_name = "yahoo_finance_news"
    LIST_URL = "https://finance.yahoo.com/news/"

    def discover_article_urls(self) -> list[str]:
        html = get_html(self.LIST_URL)
        soup = BeautifulSoup(html, "lxml")

        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urljoin("https://finance.yahoo.com", href)

            if "/news/" not in full_url:
                continue

            if full_url.endswith("/news/"):
                continue

            if full_url in seen:
                continue

            seen.add(full_url)
            urls.append(full_url)

        return urls

    def collect(self, limit: int = 10) -> Iterable[dict]:
        article_urls = self.discover_article_urls()[:limit]

        for url in article_urls:
            html = get_html(url)
            yield {
                "url": url,
                "html": html,
            }

    def parse(self, raw: dict) -> dict:
        return parse_article_html(raw["html"], raw["url"])

    def extract(self, parsed: dict) -> dict:
        data = extract_article_fields(parsed)
        data["source"] = self.source_name
        return data