from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_domain: Url = Url("http://example.com")

    model_config = SettingsConfigDict(
        env_prefix="capsule_", env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()
