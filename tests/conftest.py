from collections.abc import Generator

import pytest
from coolname import generate
from fastapi.testclient import TestClient
from httpx import BasicAuth
from pydantic_core import Url
from typer.testing import CliRunner

from capsule import app
from capsule.__main__ import cli as capsule_cli
from capsule.security.utils import RSAKeyPair, generate_rsa_keypair
from capsule.settings import CapsuleSettings, get_capsule_settings
from tests.utils import ap_actor


@pytest.fixture(autouse=True, scope="session")
def session_setup_and_teardown() -> Generator:
    runner = CliRunner()

    # setup
    result = runner.invoke(capsule_cli, ["syncdb"])
    assert result.exit_code == 0

    yield

    # teardown
    result = runner.invoke(capsule_cli, ["dropdb"])
    assert result.exit_code == 0


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def capsule_settings(rsa_keypair: tuple[str, str]) -> CapsuleSettings:
    settings = get_capsule_settings()
    settings.model_config["env_file"] = (".env", ".test.env")
    CapsuleSettings.__init__(settings)

    settings.private_key, settings.public_key = rsa_keypair

    return settings


@pytest.fixture
def logged_client(client: TestClient, capsule_settings: CapsuleSettings) -> TestClient:
    payload = {
        "client_name": "Client",
        "redirect_uris": "https://example.com",
    }

    response = client.post("/api/v1/apps", json=payload)

    app = response.json()
    auth = BasicAuth(username=capsule_settings.username, password="p4ssw0rd")
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


@pytest.fixture
def actor_and_keypair(rsa_keypair: RSAKeyPair) -> tuple[dict, RSAKeyPair]:
    return ap_actor("_".join(generate(2)), rsa_keypair.public_key), rsa_keypair
