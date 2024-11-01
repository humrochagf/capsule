from fastapi import status
from fastapi.testclient import TestClient
from httpx import BasicAuth

from capsule.settings import CapsuleSettings


def test_get_authorize(
    client: TestClient,
    capsule_settings: CapsuleSettings,
) -> None:
    payload = {
        "client_name": "Authorize Test",
        "redirect_uris": "urn:ietf:wg:oauth:2.0:oob",
    }

    response = client.post("/api/v1/apps", json=payload)
    assert response.status_code == status.HTTP_200_OK

    app = response.json()
    auth = BasicAuth(username=capsule_settings.username, password="p4ssw0rd")
    params = {
        "client_id": app["client_id"],
        "scope": app["scopes"],
        "redirect_uri": app["redirect_uris"],
        "response_type": "code",
    }

    response = client.get("/oauth/authorize", auth=auth, params=params)
    assert response.status_code == status.HTTP_200_OK


def test_get_authorize_bad_auth(
    client: TestClient,
    capsule_settings: CapsuleSettings,
) -> None:
    payload = {
        "client_name": "Bad Auth Test",
        "redirect_uris": "urn:ietf:wg:oauth:2.0:oob",
    }

    response = client.post("/api/v1/apps", json=payload)
    assert response.status_code == status.HTTP_200_OK

    app = response.json()
    auth = BasicAuth(username=capsule_settings.username, password="bad_auth")
    params = {
        "client_id": app["client_id"],
        "scope": app["scopes"],
        "redirect_uri": app["redirect_uris"],
        "response_type": "code",
    }

    response = client.get("/oauth/authorize", auth=auth, params=params)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_authorize_bad_scope(
    client: TestClient,
    capsule_settings: CapsuleSettings,
) -> None:
    payload = {
        "client_name": "Bad Scope Test",
        "redirect_uris": "urn:ietf:wg:oauth:2.0:oob",
    }

    response = client.post("/api/v1/apps", json=payload)
    assert response.status_code == status.HTTP_200_OK

    app = response.json()
    auth = BasicAuth(username=capsule_settings.username, password="p4ssw0rd")
    params = {
        "client_id": app["client_id"],
        "scope": "bad_scope",
        "redirect_uri": app["redirect_uris"],
        "response_type": "code",
    }

    response = client.get("/oauth/authorize", auth=auth, params=params)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_authorize_bad_redirect_uri(
    client: TestClient,
    capsule_settings: CapsuleSettings,
) -> None:
    payload = {
        "client_name": "Bad Redirect URI Test",
        "redirect_uris": "urn:ietf:wg:oauth:2.0:oob",
    }

    response = client.post("/api/v1/apps", json=payload)
    assert response.status_code == status.HTTP_200_OK

    app = response.json()
    auth = BasicAuth(username=capsule_settings.username, password="p4ssw0rd")
    params = {
        "client_id": app["client_id"],
        "scope": app["scopes"],
        "redirect_uri": "https://bad-redirect.com",
        "response_type": "code",
    }

    response = client.get("/oauth/authorize", auth=auth, params=params)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_authorize_no_client(
    client: TestClient,
    capsule_settings: CapsuleSettings,
) -> None:
    auth = BasicAuth(username=capsule_settings.username, password="p4ssw0rd")
    params = {
        "client_id": "not_found",
        "scope": "read",
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "response_type": "code",
    }

    response = client.get("/oauth/authorize", auth=auth, params=params)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
