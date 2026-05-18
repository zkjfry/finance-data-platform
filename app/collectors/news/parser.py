from bs4 import BeautifulSoup
from app.common.utils import clean_text


def parse_article_html(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    title = None
    title_tag = soup.find("h1")

    if title_tag:
        title = clean_text(title_tag.get_text())
    else:
        fallback_title = soup.find("title")
        title = clean_text(fallback_title.get_text()) if fallback_title else None

    body_parts = []

    article = soup.find("article")
    if article:
        for p in article.find_all("p"):
            text = clean_text(p.get_text())
            if text:
                body_parts.append(text)

    if not body_parts:
        for p in soup.find_all("p"):
            text = clean_text(p.get_text())
            if text:
                body_parts.append(text)

    published_at = None
    meta_time = soup.find("time")
    if meta_time:
        published_at = meta_time.get("datetime") or clean_text(meta_time.get_text())

    return {
        "url": url,
        "title": title,
        "published_at_raw": published_at,
        "body_text": "\n".join(body_parts) if body_parts else None,
    }