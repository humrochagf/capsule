from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from respx import MockRouter

from capsule.security.utils import RSAKeyPair
from capsule.settings import CapsuleSettings
from tests.utils import ap_follow


def test_system_inbox_sync(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    actor_and_keypair: tuple[dict, RSAKeyPair],
    respx_mock: MockRouter,
) -> None:
    capsule_settings.username = "testuser"
    actor, _ = actor_and_keypair
    actor_username = actor["preferredUsername"]

    response = client.post("/system/inbox/cleanup", json={})
    assert response.status_code == status.HTTP_202_ACCEPTED

    mocked_response = Response(status_code=500)
    respx_mock.get(actor["id"]).mock(return_value=mocked_response)

    payload = ap_follow(actor_username, capsule_settings.username)

    response = client.post(f"/actors/{capsule_settings.username}/inbox", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

    mocked_response = Response(status_code=200, json=actor)
    respx_mock.get(actor["id"]).mock(return_value=mocked_response)
    mocked_response = Response(status_code=202)
    respx_mock.post(actor["inbox"]).mock(return_value=mocked_response)

    response = client.post("/system/inbox/sync?status=error", json={})
    assert response.status_code == status.HTTP_202_ACCEPTED
