import httpx

from app.common.exceptions import FetchError


DEFAULT_HEADERS = {
    "User-Agent": "finance-data-platform/0.1 contact: jeffreychen0826@gmail.com",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_html(url: str, timeout: float = 20.0) -> str:
    try:
        with httpx.Client(
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text

    except httpx.HTTPError as exc:
        raise FetchError(f"Failed to fetch url={url}: {exc}") from exc


def get_json(url: str, timeout: float = 20.0) -> dict:
    try:
        with httpx.Client(
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPError as exc:
        raise FetchError(f"Failed to fetch url={url}: {exc}") from exc