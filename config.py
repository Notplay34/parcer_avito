"""Configuration from environment."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    database_url: str
    check_interval: int = 60
    max_searches: int = 20
    block_duration_seconds: int = 600


settings = Settings()
