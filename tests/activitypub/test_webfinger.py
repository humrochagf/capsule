from pathlib import Path

from fastapi import status
from fastapi.testclient import TestClient
from pydantic import HttpUrl

from capsule.settings import CapsuleSettings


def test_well_known_webfinger(
    client: TestClient, capsule_settings: CapsuleSettings
) -> None:
    capsule_settings.username = "testuser"
    capsule_settings.hostname = HttpUrl("https://example.com")

    acct = "acct:testuser@example.com"
    response = client.get(f"/.well-known/webfinger?resource={acct}")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Type"] == "application/jrd+json"
    assert response.json() == {
        "subject": "acct:testuser@example.com",
        "aliases": [
            "https://example.com/@testuser",
            "https://example.com/actors/testuser",
        ],
        "links": [
            {
                "rel": "http://webfinger.net/rel/profile-page",
                "type": "text/html",
                "href": "https://example.com/@testuser",
            },
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": "https://example.com/actors/testuser",
            },
        ],
    }


def test_well_known_webfinger_with_image(
    client: TestClient, capsule_settings: CapsuleSettings, tmp_path: Path
) -> None:
    capsule_settings.username = "testuser"
    capsule_settings.hostname = HttpUrl("https://example.com")

    profile_image = tmp_path / "test.jpg"
    profile_image.touch()
    capsule_settings.profile_image = profile_image

    acct = "acct:testuser@example.com"
    response = client.get(f"/.well-known/webfinger?resource={acct}")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Content-Type"] == "application/jrd+json"
    assert response.json() == {
        "subject": "acct:testuser@example.com",
        "aliases": [
            "https://example.com/@testuser",
            "https://example.com/actors/testuser",
        ],
        "links": [
            {
                "rel": "http://webfinger.net/rel/profile-page",
                "type": "text/html",
                "href": "https://example.com/@testuser",
            },
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": "https://example.com/actors/testuser",
            },
            {
                "rel": "http://webfinger.net/rel/avatar",
                "type": "image/jpeg",
                "href": "https://example.com/actors/testuser/icon",
            },
        ],
    }


def test_well_known_webfinger_not_found(
    client: TestClient, capsule_settings: CapsuleSettings
) -> None:
    acct = f"acct:notfound@{capsule_settings.hostname.host}"

    response = client.get(f"/.well-known/webfinger?resource={acct}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_well_known_webfinger_bad_resource(client: TestClient) -> None:
    response = client.get("/.well-known/webfinger")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
