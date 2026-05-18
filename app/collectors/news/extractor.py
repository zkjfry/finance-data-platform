from urllib.parse import urlparse

from app.common.hashing import sha256_text
from app.common.utils import clean_text


def extract_article_fields(parsed: dict) -> dict:
    url = parsed["url"]
    title = clean_text(parsed.get("title") or "")
    body_text = clean_text(parsed.get("body_text") or "")

    content_hash = sha256_text(f"{title}\n{body_text}")

    path = urlparse(url).path.strip("/")
    article_id = path.replace("/", "_") or sha256_text(url)[:16]

    return {
        "article_id": article_id,
        "url": url,
        "title": title or "Untitled",
        "published_at": None,
        "authors": [],
        "symbols": [],
        "summary": body_text[:300] if body_text else None,
        "body_text": body_text,
        "content_hash": content_hash,
    }