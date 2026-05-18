from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "finance-data-platform"
    app_env: str = "local"
    log_level: str = "INFO"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "finance_data"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    raw_data_dir: str = "./data/raw"
    parsed_data_dir: str = "./data/parsed"

    default_timeout_seconds: int = 20
    scheduler_news_interval_minutes: int = 30
    scheduler_reports_interval_minutes: int = 120

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def sqlalchemy_database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()