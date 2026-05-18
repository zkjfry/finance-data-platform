from pathlib import Path
import httpx

from config.settings import get_settings
from app.infrastructure.http.headers import default_headers


def download_file(url: str, output_path: str) -> str:
    settings = get_settings()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(
        timeout=settings.default_timeout_seconds,
        follow_redirects=True,
        headers=default_headers(),
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        path.write_bytes(response.content)

    return str(path)