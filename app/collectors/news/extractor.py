import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

from app.common.hashing import sha256_text
from app.common.utils import clean_text


COMPANY_SYMBOL_MAP = {
    "apple": "AAPL",
    "apple inc": "AAPL",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "alphabet": "GOOGL",
    "google": "GOOGL",
    "netflix": "NFLX",
    "berkshire": "BRK.B",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "goldman sachs": "GS",
    "bank of america": "BAC",
}

SYMBOL_PATTERNS = [
    re.compile(r"\(([A-Z]{1,5}(?:\.[A-Z])?)\)"),
    re.compile(r"\b(?:NASDAQ|NYSE|AMEX)\s*:\s*([A-Z]{1,5}(?:\.[A-Z])?)\b", re.I),
]


def parse_published_at(value: str | None) -> datetime | None:
    if not value:
        return None

    cleaned = clean_text(value)
    if not cleaned:
        return None

    try:
        parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        pass

    try:
        parsed = parsedate_to_datetime(cleaned)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return None


def normalize_authors(value: object) -> list[str]:
    if not value:
        return []

    raw_authors = value if isinstance(value, list) else [value]
    authors: list[str] = []

    for author in raw_authors:
        name = clean_text(str(author))
        if name and name not in authors:
            authors.append(name)

    return authors


def extract_symbols(title: str, body_text: str) -> list[str]:
    source_text = f"{title}\n{body_text}"
    lower_text = source_text.lower()
    symbols: set[str] = set()

    for company_name, symbol in COMPANY_SYMBOL_MAP.items():
        if re.search(rf"\b{re.escape(company_name)}\b", lower_text):
            symbols.add(symbol)

    for pattern in SYMBOL_PATTERNS:
        for match in pattern.findall(source_text):
            symbols.add(match.upper())

    return sorted(symbols)


def extract_article_fields(parsed: dict) -> dict:
    url = parsed["url"]
    title = clean_text(parsed.get("title") or "")
    body_text = clean_text(parsed.get("body_text") or "")
    summary = clean_text(parsed.get("summary") or "") or None

    content_hash = sha256_text(f"{title}\n{body_text}")

    path = urlparse(url).path.strip("/")
    article_id = path.replace("/", "_") or sha256_text(url)[:16]

    return {
        "article_id": article_id,
        "url": url,
        "title": title or "Untitled",
        "published_at": parse_published_at(parsed.get("published_at_raw")),
        "authors": normalize_authors(parsed.get("authors")),
        "symbols": extract_symbols(title, body_text),
        "summary": summary or (body_text[:300] if body_text else None),
        "body_text": body_text,
        "content_hash": content_hash,
    }