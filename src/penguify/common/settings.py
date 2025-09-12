from datetime import datetime, timezone

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_datestamp() -> str:
    """Return today's date in UTC (YYYY-MM-DD)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def default_label() -> str:
    """Return today's date in UTC (DD MMM)."""
    return datetime.now(timezone.utc).strftime("%d %b")


class Settings(BaseSettings):
    DATESTAMP: str = Field(default_factory=default_datestamp)
    DATE_LABEL: str = Field(default_factory=default_label)
    FETCH_TIMEOUT: int = 12
    TOP_STORY_COUNT: int = 9
    HN_STORIES_JSON_PATH: str = "hackernews.json"
    MODEL_NAME: str = ""
    IMAGE_GEN_INSTRUCTIONS: str = ""
    WAIT_BETWEEN_REQUESTS_SECONDS: int = 2
    IMAGE_HEIGHT: int = 256
    IMAGE_WIDTH: int = 256
    IMAGES_BASE_DIR: str = "./imgs"
    S3_BUCKET_NAME: str = ""
    MANIFEST_S3_KEY: str = "manifest.json"
    HEADERS: dict[str, str] = {"User-Agent": "Penguify/1.0 (https://github.com/benkulcsar/penguify)"}
    MIN_EXCERPT_LENGTH: int = 50


class ProductionSettings(Settings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")


production_settings = ProductionSettings()
