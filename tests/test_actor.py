from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pydantic_core import Url

from capsule.settings import CapsuleSettings


@pytest.mark.parametrize("url", ["/actors/testuser", "@testuser"])
@pytest.mark.parametrize(
    "accept", ["application/ld", "application/json", "application/activity+json"]
)
def test_actor(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    url: str,
    accept: str,
    tmp_path: Path,
) -> None:
    capsule_settings.username = "testuser"
    capsule_settings.hostname = Url("https://example.com")
    capsule_settings.name = "Test Name"
    capsule_settings.summary = "Test Summary"
    capsule_settings.public_key = (
        "-----BEGIN PUBLIC KEY-----...-----END PUBLIC KEY-----"
    )

    profile_image = tmp_path / "test.jpg"
    profile_image.touch()
    capsule_settings.profile_image = profile_image

    response = client.get(url, headers={"Accept": accept})

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Type"] == "application/activity+json"
    assert response.json() == {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
            {
                "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
            },
        ],
        "id": "https://example.com/actors/testuser",
        "type": "Person",
        "name": "Test Name",
        "preferredUsername": "testuser",
        "summary": "Test Summary",
        "inbox": "https://example.com/actors/testuser/inbox",
        "outbox": "https://example.com/actors/testuser/outbox",
        "manuallyApprovesFollowers": False,
        "publicKey": {
            "id": "https://example.com/actors/testuser#main-key",
            "owner": "https://example.com/actors/testuser",
            "publicKeyPem": "-----BEGIN PUBLIC KEY-----...-----END PUBLIC KEY-----",
        },
        "icon": {
            "type": "Image",
            "mediaType": "image/jpeg",
            "url": "https://example.com/actors/testuser/icon",
        },
    }


def test_actor_not_found(client: TestClient) -> None:
    response = client.get("/actors/notfound")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_actor_icon(
    client: TestClient, capsule_settings: CapsuleSettings, tmp_path: Path
) -> None:
    capsule_settings.username = "testuser"

    profile_image = tmp_path / "test.jpg"
    profile_image.touch()
    capsule_settings.profile_image = profile_image

    response = client.get("/actors/testuser/icon")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Type"] == "image/jpeg"


def test_actor_icon_not_found(
    client: TestClient, capsule_settings: CapsuleSettings
) -> None:
    capsule_settings.username = "testuser"

    response = client.get("/actors/testuser/icon")
    assert response.status_code == status.HTTP_404_NOT_FOUND
