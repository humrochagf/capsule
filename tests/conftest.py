from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from typer import Typer

from capsule import app
from capsule.__main__ import cli as capsule_cli
from capsule.settings import CapsuleSettings, get_capsule_settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def cli() -> Typer:
    return capsule_cli


@pytest.fixture
def capsule_settings() -> Generator[CapsuleSettings, None, None]:
    settings = get_capsule_settings()
    data = settings.model_dump()

    yield settings

    for key, value in data.items():
        setattr(settings, key, value)
