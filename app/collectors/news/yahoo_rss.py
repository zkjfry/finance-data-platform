import xml.etree.ElementTree as ET
from typing import Iterable

from app.collectors.base import BaseCollector
from app.collectors.news.extractor import extract_article_fields
from app.collectors.news.parser import parse_article_html
from app.infrastructure.http.client import get_html


class YahooFinanceRssNewsCollector(BaseCollector):
    source_name = "yahoo_finance_rss"
    RSS_URL = "https://finance.yahoo.com/news/rssindex"

    def __init__(self, rss_url: str | None = None) -> None:
        self.rss_url = rss_url or self.RSS_URL

    def discover_article_urls(self) -> list[str]:
        return [item["url"] for item in self.discover_articles()]

    def discover_articles(self) -> list[dict]:
        xml_text = get_html(self.rss_url)
        root = ET.fromstring(xml_text)

        articles: list[dict] = []
        seen: set[str] = set()

        for item in root.findall(".//item"):
            link = item.findtext("link")
            if not link:
                continue

            url = link.strip()
            if url in seen:
                continue

            seen.add(url)

            articles.append(
                {
                    "url": url,
                    "rss_title": self._clean_xml_text(item.findtext("title")),
                    "rss_published_at": self._clean_xml_text(item.findtext("pubDate")),
                    "rss_summary": self._clean_xml_text(item.findtext("description")),
                }
            )

        return articles

    def collect(self, limit: int = 10) -> Iterable[dict]:
        articles = self.discover_articles()[:limit]

        for article in articles:
            html = get_html(article["url"])
            yield {
                "url": article["url"],
                "html": html,
                "rss_title": article.get("rss_title"),
                "rss_published_at": article.get("rss_published_at"),
                "rss_summary": article.get("rss_summary"),
            }

    def parse(self, raw: dict) -> dict:
        return parse_article_html(
            html=raw["html"],
            url=raw["url"],
            fallback_title=raw.get("rss_title"),
            fallback_published_at=raw.get("rss_published_at"),
            fallback_summary=raw.get("rss_summary"),
        )

    def extract(self, parsed: dict) -> dict:
        data = extract_article_fields(parsed)
        data["source"] = self.source_name
        return data

    def _clean_xml_text(self, value: str | None) -> str | None:
        if not value:
            return None

        value = value.strip()
        return value or None
