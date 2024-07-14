from pydantic import HttpUrl, MongoDsn
from pydantic_core import MultiHostUrl, Url
from pydantic_settings import SettingsConfigDict
from wheke import WhekeSettings, get_settings


class CapsuleSettings(WhekeSettings):
    project_name: str = "Capsule"
    hostname: HttpUrl = Url("http://localhost:8000")

    connection_string: MongoDsn = MultiHostUrl("mongodb://localhost:27017")
    database_name: str = "capsule"

    username: str = ""
    name: str = ""
    summary: str = ""
    public_key: str = ""
    private_key: str = ""

    model_config = SettingsConfigDict(
        env_prefix="capsule_", env_file=".env", env_file_encoding="utf-8"
    )


def get_capsule_settings() -> CapsuleSettings:
    return get_settings(CapsuleSettings)
