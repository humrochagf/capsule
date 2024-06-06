from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from capsule import app
from capsule.settings import CapsuleSettings, get_capsule_settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def capsule_settings() -> Generator[CapsuleSettings, None, None]:
    settings = get_capsule_settings()
    data = settings.model_dump()

    yield settings

    for key, value in data.items():
        setattr(settings, key, value)
