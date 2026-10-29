from functools import lru_cache

from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration; values may be supplied by a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    urja_base_url: HttpUrl = "https://urja-ops.flockenergy.tech"
    urja_email: str
    urja_password: SecretStr
    urja_search_path: str = "/portal/meters/search"
    urja_geo_path_template: str = "/portal/meters/{meter_id}/geo"
    urja_energy_path_template: str = "/portal/meters/{meter_id}/energy"
    request_timeout_seconds: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()

