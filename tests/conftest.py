import secrets
from collections.abc import Generator
from pathlib import Path

import pytest
from coolname import generate
from fastapi.testclient import TestClient
from httpx import BasicAuth
from pydantic_core import Url
from typer.testing import CliRunner
from wheke_ladybug import LadybugSettings
from wheke_sqlmodel import SQLITE_DRIVER, SQLModelSettings

from capsule import build_app
from capsule.__main__ import build_cli
from capsule.__main__ import cli as capsule_cli
from capsule.security.utils import RSAKeyPair, generate_rsa_keypair
from capsule.settings import CapsuleSettings
from tests.utils import ap_actor

CAPSULE_USERNAME = "testuser"


@pytest.fixture
def client(capsule_settings: CapsuleSettings) -> Generator[TestClient]:
    runner = CliRunner()
    cli = build_cli(capsule_settings)

    # setup
    result = runner.invoke(cli, ["syncdb"])
    assert result.exit_code == 0

    with TestClient(build_app(capsule_settings)) as client:
        yield client

    # teardown
    result = runner.invoke(cli, ["dropdb"])
    assert result.exit_code == 0


@pytest.fixture
def capsule_settings(
    tmp_path: Path, rsa_keypair: tuple[str, str], pwd_and_hash: tuple[str, str]
) -> CapsuleSettings:
    sqlmodel_settings = SQLModelSettings(
        connection_string=f"{SQLITE_DRIVER}:///{tmp_path / 'test.db'}",
        echo_operations=True,
    )
    ladybug_settings = LadybugSettings(
        connection_string=f"{tmp_path / 'test.lbug'}",
    )
    settings = CapsuleSettings(
        username=CAPSULE_USERNAME,
        password=pwd_and_hash[1],
        features={
            sqlmodel_settings.__feature_name__: sqlmodel_settings.model_dump(),
            ladybug_settings.__feature_name__: ladybug_settings.model_dump(),
        },
    )

    settings.private_key, settings.public_key = rsa_keypair

    return settings


@pytest.fixture
def logged_client(
    client: TestClient, capsule_settings: CapsuleSettings, pwd_and_hash: tuple[str, str]
) -> TestClient:
    payload = {
        "client_name": "Client",
        "redirect_uris": "https://example.com",
    }

    response = client.post("/api/v1/apps", json=payload)

    app = response.json()
    auth = BasicAuth(username=capsule_settings.username, password=pwd_and_hash[0])
    payload = {
        "client_id": app["client_id"],
        "scope": app["scopes"],
        "redirect_uri": app["redirect_uris"],
        "response_type": "code",
    }

    response = client.post(
        "/oauth/authorize", auth=auth, data=payload, follow_redirects=False
    )

    code = ""
    for query_item in (Url(response.headers["location"]).query or "").split("&"):
        key, value = query_item.split("=")

        if key == "code":
            code = value

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": app["client_id"],
        "client_secret": app["client_secret"],
        "redirect_uri": "https://example.com",
    }

    response = client.post("/oauth/token", json=payload)
    token = response.json()["access_token"]

    client.headers["Authorization"] = f"Bearer {token}"

    return client


@pytest.fixture
def rsa_keypair() -> tuple[str, str]:
    return generate_rsa_keypair()


@pytest.fixture(scope="session")
def pwd_and_hash() -> tuple[str, str]:
    pwd = secrets.token_urlsafe()

    runner = CliRunner()

    result = runner.invoke(capsule_cli, ["security", "hashpwd", pwd])
    assert result.exit_code == 0

    return pwd, result.stdout.strip()


@pytest.fixture
def actor_and_keypair(rsa_keypair: RSAKeyPair) -> tuple[dict, RSAKeyPair]:
    return ap_actor("_".join(generate(2)), rsa_keypair.public_key), rsa_keypair
