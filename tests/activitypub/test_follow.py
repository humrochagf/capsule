from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from pydantic import HttpUrl
from respx import MockRouter

from capsule.security.utils import RSAKeyPair, SignedRequestAuth
from capsule.settings import CapsuleSettings
from tests.utils import ap_follow, ap_unfollow


def test_follow_and_unfollow(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    actor_and_keypair: tuple[dict, RSAKeyPair],
    respx_mock: MockRouter,
) -> None:
    instance_username = capsule_settings.username
    instance_inbox = f"/actors/{instance_username}/inbox"
    actor, keys = actor_and_keypair
    actor_username = actor["preferredUsername"]

    mocked_actor_response = Response(status_code=200, json=actor)
    respx_mock.get(actor["id"]).mock(return_value=mocked_actor_response)
    mocked_inbox_response = Response(status_code=202)
    respx_mock.post(actor["inbox"]).mock(return_value=mocked_inbox_response)

    follow = ap_follow(actor_username, instance_username)

    response = client.post(instance_inbox, json=follow)
    assert response.status_code == status.HTTP_202_ACCEPTED

    unfollow = ap_unfollow(actor_username, follow)
    auth = SignedRequestAuth(
        public_key_id=HttpUrl(actor["publicKey"]["id"]),
        private_key=keys.private_key,
    )

    response = client.post(instance_inbox, json=unfollow, auth=auth)
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_accept_follow_failed(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    actor_and_keypair: tuple[dict, RSAKeyPair],
    respx_mock: MockRouter,
) -> None:
    instance_username = capsule_settings.username
    instance_inbox = f"/actors/{instance_username}/inbox"
    actor, _ = actor_and_keypair
    actor_username = actor["preferredUsername"]

    mocked_actor_response = Response(status_code=200, json=actor)
    respx_mock.get(actor["id"]).mock(return_value=mocked_actor_response)
    mocked_inbox_response = Response(status_code=500)
    respx_mock.post(actor["inbox"]).mock(return_value=mocked_inbox_response)

    payload = ap_follow(actor_username, instance_username)

    response = client.post(instance_inbox, json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED
