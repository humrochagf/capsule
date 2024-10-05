from collections.abc import Generator

import pytest
from coolname import generate
from fastapi.testclient import TestClient
from typer import Typer

from capsule import app
from capsule.__main__ import cli as capsule_cli
from capsule.security.utils import RSAKeyPair, generate_rsa_keypair
from capsule.settings import CapsuleSettings, get_capsule_settings
from tests.utils import ap_actor


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def cli() -> Typer:
    return capsule_cli


@pytest.fixture
def capsule_settings(
    rsa_keypair: tuple[str, str],
) -> Generator[CapsuleSettings, None, None]:
    settings = get_capsule_settings()
    data = settings.model_dump()

    settings.private_key, settings.public_key = rsa_keypair

    yield settings

    for key, value in data.items():
        setattr(settings, key, value)


@pytest.fixture
def rsa_keypair() -> tuple[str, str]:
    return generate_rsa_keypair()


@pytest.fixture
def actor_and_keypair(rsa_keypair: RSAKeyPair) -> tuple[dict, RSAKeyPair]:
    return ap_actor("_".join(generate(2)), rsa_keypair.public_key), rsa_keypair
