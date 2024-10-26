from fastapi import status
from fastapi.testclient import TestClient


def test_authorize_without_credentials(
    client: TestClient,
) -> None:
    response = client.get("/oauth/authorize")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
