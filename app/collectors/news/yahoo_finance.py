import re
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.collectors.news.extractor import extract_article_fields
from app.collectors.news.parser import parse_article_html
from app.infrastructure.http.client import get_html


YAHOO_ALLOWED_HOSTS = {"finance.yahoo.com", "www.finance.yahoo.com"}

YAHOO_BLOCKED_NEWS_PATHS = {
    "/news/",
    "/news/us/",
    "/news/politics/",
    "/news/world/",
    "/news/economy/",
    "/news/industries/",
    "/news/stock-market-news/",
    "/news/personal-finance/",
    "/news/crypto/",
    "/news/press-releases/",
}

YAHOO_ARTICLE_RE = re.compile(
    r"https://finance\.yahoo\.com/news/[a-zA-Z0-9][^\"'<>\s]*?\.html/?"
)


def normalize_yahoo_url(url: str) -> str:
    """
    Normalize Yahoo URL for stable deduplication.

    Examples:
    https://finance.yahoo.com/news/abc.html?guccounter=1
    -> https://finance.yahoo.com/news/abc.html

    https://finance.yahoo.com/news/abc.html/
    -> https://finance.yahoo.com/news/abc.html
    """
    parsed = urlparse(url)
    path = parsed.path

    if path.endswith(".html/"):
        path = path[:-1]

    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def is_valid_yahoo_article_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path

    if host not in YAHOO_ALLOWED_HOSTS:
        return False

    if not path.startswith("/news/"):
        return False

    if path in YAHOO_BLOCKED_NEWS_PATHS:
        return False

    slug = path.removeprefix("/news/").strip("/")
    if not slug:
        return False

    # Reject nested category/list pages.
    # But allow /news/article-title-123.html/
    if "/" in slug and not slug.endswith(".html/"):
        return False

    if not slug.endswith(".html") and not slug.endswith(".html/"):
        return False

    # Avoid generic Yahoo Finance pages with no article-like slug.
    article_slug = slug.removesuffix("/").removesuffix(".html")
    if len(article_slug) < 12:
        return False

    return True


class YahooFinanceNewsCollector(BaseCollector):
    source_name = "yahoo_finance_news"
    LIST_URL = "https://finance.yahoo.com/news/"

    def __init__(self, list_url: str | None = None) -> None:
        self.list_url = list_url or self.LIST_URL

    def discover_article_urls(self) -> list[str]:
        html = get_html(self.list_url)
        soup = BeautifulSoup(html, "lxml")

        urls: list[str] = []
        seen: set[str] = set()

        def add_url(candidate_url: str) -> None:
            normalized_url = normalize_yahoo_url(candidate_url)

            if not is_valid_yahoo_article_url(normalized_url):
                return

            if normalized_url in seen:
                return

            seen.add(normalized_url)
            urls.append(normalized_url)

        # Method 1: normal <a href="..."> discovery
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urljoin("https://finance.yahoo.com", href)
            add_url(full_url)

        # Method 2: regex discovery from embedded page data
        # Yahoo often stores more article URLs inside scripts / JSON blobs.
        for match in YAHOO_ARTICLE_RE.findall(html):
            add_url(match)

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