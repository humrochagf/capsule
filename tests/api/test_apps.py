from fastapi import status
from fastapi.testclient import TestClient


def test_create_app_json(
    client: TestClient,
) -> None:
    payload = {
        "client_name": "TestClientJson",
        "redirect_uris": "urn:ietf:wg:oauth:2.0:oob",
    }

    response = client.post("/api/v1/apps", json=payload)
    assert response.status_code == status.HTTP_200_OK


def test_create_app_data(
    client: TestClient,
) -> None:
    payload = {
        "client_name": "TestClientFormData",
        "redirect_uris": "urn:ietf:wg:oauth:2.0:oob",
    }

    response = client.post("/api/v1/apps", data=payload)
    assert response.status_code == status.HTTP_200_OK


def test_verify_credentials(
    logged_client: TestClient,
) -> None:
    response = logged_client.get("/api/v1/apps/verify_credentials")
    assert response.status_code == status.HTTP_200_OK


def test_verify_credentials_not_logged(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/apps/verify_credentials", headers={"Authorization": "Bearer bad_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
