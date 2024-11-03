from typing import Annotated

import httpx
from fastapi import Depends
from pydantic import FilePath, HttpUrl, MongoDsn
from pydantic_core import MultiHostUrl, Url
from pydantic_settings import SettingsConfigDict
from wheke import WhekeSettings, get_settings

from .__about__ import __version__


class CapsuleSettings(WhekeSettings):
    project_name: str = "Capsule"
    hostname: HttpUrl = Url("http://localhost:8000")

    connection_string: MongoDsn = MultiHostUrl("mongodb://localhost:27017")
    database_name: str = "capsule"

    username: str = ""
    password: str = ""
    name: str = ""
    summary: str = ""
    profile_image: FilePath | None = None

    public_key: str = ""
    private_key: str = ""

    model_config = SettingsConfigDict(
        env_prefix="capsule_", env_file=".env", env_file_encoding="utf-8"
    )

    @property
    def profile_url(self) -> str:
        return f"{self.hostname}@{self.username}"

    @property
    def actor_url(self) -> str:
        return f"{self.hostname}actors/{self.username}"

    @property
    def public_key_id(self) -> str:
        return f"{self.actor_url}#main-key"

    @property
    def user_agent(self):
        return (
            f"python-httpx/{httpx.__version__} "
            f"({self.project_name}/{__version__}; +{self.hostname})"
        )


def get_capsule_settings() -> CapsuleSettings:
    return get_settings(CapsuleSettings)


CapsuleSettingsInjection = Annotated[CapsuleSettings, Depends(get_capsule_settings)]
