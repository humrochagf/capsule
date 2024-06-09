from pydantic import HttpUrl
from pydantic_core import Url
from pydantic_settings import SettingsConfigDict
from wheke import WhekeSettings, get_settings


class CapsuleSettings(WhekeSettings):
    project_name: str = "Capsule"
    hostname: HttpUrl = Url("http://localhost:8000")
    username: str = ""

    model_config = SettingsConfigDict(
        env_prefix="capsule_", env_file=".env", env_file_encoding="utf-8"
    )


def get_capsule_settings() -> CapsuleSettings:
    return get_settings(CapsuleSettings)
