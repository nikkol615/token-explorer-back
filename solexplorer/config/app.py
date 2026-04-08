from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    app_title: str = "SolExplorer API"
    app_version: str = "0.1.0"
    app_description: str = "Solana token analysis and scoring service"
    dexscreener_base_url: str = "https://api.dexscreener.com"
    http_timeout: float = 10.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of application settings."""
    return Settings()


TAGS_METADATA: list[dict[str, str]] = [
    {
        "name": "Token Analysis",
        "description": "Endpoints for fetching and scoring Solana tokens.",
    },
]
