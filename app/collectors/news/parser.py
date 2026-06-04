import json
from typing import Any

from bs4 import BeautifulSoup

from app.common.utils import clean_text


def _json_loads_safe(value: str | None) -> dict[str, Any] | list[Any] | None:
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _find_json_ld_values(soup: BeautifulSoup) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []

    for script in soup.find_all("script", type="application/ld+json"):
        parsed = _json_loads_safe(script.string)
        if isinstance(parsed, dict):
            values.append(parsed)
        elif isinstance(parsed, list):
            values.extend(item for item in parsed if isinstance(item, dict))

    return values


def _extract_authors_from_json_ld(json_ld_values: list[dict[str, Any]]) -> list[str]:
    authors: list[str] = []

    for item in json_ld_values:
        raw_author = item.get("author")
        if not raw_author:
            continue

        raw_authors = raw_author if isinstance(raw_author, list) else [raw_author]
        for author in raw_authors:
            if isinstance(author, dict):
                name = clean_text(str(author.get("name") or ""))
            else:
                name = clean_text(str(author))

            if name and name not in authors:
                authors.append(name)

    return authors


def _extract_published_at_from_json_ld(json_ld_values: list[dict[str, Any]]) -> str | None:
    for item in json_ld_values:
        for key in ("datePublished", "dateModified"):
            value = item.get(key)
            if value:
                return str(value)
    return None


def _extract_summary_from_json_ld(json_ld_values: list[dict[str, Any]]) -> str | None:
    for item in json_ld_values:
        value = item.get("description")
        if value:
            return clean_text(str(value))
    return None


def _extract_meta_content(
        soup: BeautifulSoup,
        *,
        property_name: str | None = None,
        name: str | None = None,
) -> str | None:
    if property_name:
        tag = soup.find("meta", attrs={"property": property_name})
        if tag and tag.get("content"):
            return clean_text(tag["content"])

    if name:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return clean_text(tag["content"])

    return None


def parse_article_html(
        html: str,
        url: str,
        fallback_title: str | None = None,
        fallback_published_at: str | None = None,
        fallback_summary: str | None = None,
) -> dict:
    soup = BeautifulSoup(html, "lxml")
    json_ld_values = _find_json_ld_values(soup)

    title = None

    title_tag = soup.find("h1")
    if title_tag:
        title = clean_text(title_tag.get_text())

    if not title or title == "Yahoo Finance":
        title = _extract_meta_content(soup, property_name="og:title")

    if not title or title == "Yahoo Finance":
        title = _extract_meta_content(soup, name="twitter:title")

    if not title or title == "Yahoo Finance":
        title = clean_text(fallback_title or "")

    if not title:
        fallback_title_tag = soup.find("title")
        title = clean_text(fallback_title_tag.get_text()) if fallback_title_tag else None

    body_parts: list[str] = []

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

    published_at = _extract_published_at_from_json_ld(json_ld_values)
    if not published_at:
        meta_time = soup.find("time")
        if meta_time:
            published_at = meta_time.get("datetime") or clean_text(meta_time.get_text())

    if not published_at:
        published_at = fallback_published_at

    authors = _extract_authors_from_json_ld(json_ld_values)
    summary = _extract_summary_from_json_ld(json_ld_values)
    if not summary:
        summary = clean_text(fallback_summary or "") or None

    return {
        "url": url,
        "title": title,
        "published_at_raw": published_at,
        "authors": authors,
        "summary": summary,
        "body_text": "\n".join(body_parts) if body_parts else None,
    }
