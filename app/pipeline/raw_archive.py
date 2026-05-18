from pathlib import Path
from urllib.parse import urlparse

from config.settings import get_settings
from app.common.hashing import sha256_text
from app.common.time_utils import utc_now


def archive_raw_html(source: str, url: str, html: str) -> str:
    settings = get_settings()

    path = urlparse(url).path.strip("/").replace("/", "_")
    url_id = path or sha256_text(url)[:16]

    timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    base_dir = Path(settings.raw_data_dir) / source
    base_dir.mkdir(parents=True, exist_ok=True)

    file_path = base_dir / f"{timestamp}_{url_id}.html"
    file_path.write_text(html, encoding="utf-8")

    return str(file_path)