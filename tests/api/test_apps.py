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
