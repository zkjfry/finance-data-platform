import httpx
from config.settings import get_settings
from app.infrastructure.http.headers import default_headers
from app.common.exceptions import FetchError


def get_html(url: str) -> str:
    settings = get_settings()

    try:
        with httpx.Client(
            timeout=settings.default_timeout_seconds,
            follow_redirects=True,
            headers=default_headers(),
        ) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as exc:
        raise FetchError(f"Failed to fetch url={url}: {exc}") from exc