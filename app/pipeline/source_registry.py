from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field


CONFIG_PATH = Path("config/sources.yaml")


class NewsSourceConfig(BaseModel):
    name: str
    type: Literal["yahoo_finance", "yahoo_rss"]
    enabled: bool = True
    list_url: str | None = None
    rss_url: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class ReportSourceConfig(BaseModel):
    name: str
    type: Literal["sec_edgar"]
    enabled: bool = True
    cik: str
    ticker: str
    company_name: str
    form_types: list[str] = Field(default_factory=lambda: ["10-K", "10-Q", "8-K"])
    limit: int = Field(default=10, ge=1, le=100)


class SourceRegistry(BaseModel):
    news: list[NewsSourceConfig] = Field(default_factory=list)
    reports: list[ReportSourceConfig] = Field(default_factory=list)


def load_source_registry(path: str | Path = CONFIG_PATH) -> SourceRegistry:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Source registry not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        raw: dict[str, Any] = yaml.safe_load(file) or {}

    return SourceRegistry.model_validate(raw)


def enabled_news_sources(registry: SourceRegistry | None = None) -> list[NewsSourceConfig]:
    registry = registry or load_source_registry()
    return [source for source in registry.news if source.enabled]


def enabled_report_sources(registry: SourceRegistry | None = None) -> list[ReportSourceConfig]:
    registry = registry or load_source_registry()
    return [source for source in registry.reports if source.enabled]