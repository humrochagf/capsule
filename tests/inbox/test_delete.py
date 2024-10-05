from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from pydantic_core import Url
from respx import MockRouter

from capsule.security.utils import RSAKeyPair, SignedRequestAuth
from capsule.settings import CapsuleSettings
from tests.utils import ap_create_note, ap_delete_actor


def test_delete_actor(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    actor_and_keypair: tuple[dict, RSAKeyPair],
    respx_mock: MockRouter,
) -> None:
    instance_username = "testuser"
    instance_inbox = f"/actors/{instance_username}/inbox"
    capsule_settings.username = instance_username
    actor, keys = actor_and_keypair
    actor_username = actor["preferredUsername"]

    mocked_response = Response(status_code=200, json=actor)
    respx_mock.get(actor["id"]).mock(return_value=mocked_response)

    payload = ap_create_note(actor_username, instance_username)

    response = client.post(instance_inbox, json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

    payload = ap_delete_actor(actor_username)
    auth = SignedRequestAuth(
        public_key_id=Url(actor["publicKey"]["id"]),
        private_key=keys.private_key,
    )

    response = client.post(instance_inbox, json=payload, auth=auth)
    assert response.status_code == status.HTTP_202_ACCEPTED
