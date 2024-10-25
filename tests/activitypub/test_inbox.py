from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from pydantic_core import Url
from respx import MockRouter

from capsule.security.utils import RSAKeyPair, SignedRequestAuth
from capsule.settings import CapsuleSettings
from tests.utils import ap_create_note


def test_inbox(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    actor_and_keypair: tuple[dict, RSAKeyPair],
    respx_mock: MockRouter,
) -> None:
    instance_username = capsule_settings.username
    instance_inbox = f"/actors/{instance_username}/inbox"
    actor, keys = actor_and_keypair
    actor_username = actor["preferredUsername"]

    mocked_response = Response(status_code=200, json=actor)
    respx_mock.get(actor["id"]).mock(return_value=mocked_response)

    payload = ap_create_note(
        actor_username, instance_username, "Hello for the first time :)"
    )

    response = client.post(instance_inbox, json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

    payload = ap_create_note(
        actor_username, instance_username, "Hello for the second time :)"
    )
    auth = SignedRequestAuth(
        public_key_id=Url(actor["publicKey"]["id"]),
        private_key=keys.private_key,
    )

    response = client.post(instance_inbox, json=payload, auth=auth)
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_inbox_bad_signature(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    actor_and_keypair: tuple[dict, RSAKeyPair],
    respx_mock: MockRouter,
) -> None:
    instance_username = capsule_settings.username
    instance_inbox = f"/actors/{instance_username}/inbox"
    actor, keys = actor_and_keypair
    actor_username = actor["preferredUsername"]

    mocked_response = Response(status_code=200, json=actor)
    respx_mock.get(actor["id"]).mock(return_value=mocked_response)

    payload = ap_create_note(
        actor_username, instance_username, "Hello for the first time :)"
    )

    response = client.post(instance_inbox, json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

    payload = ap_create_note(actor_username, instance_username, "Bad hello!")

    response = client.post(
        instance_inbox, json=payload, headers={"digest": "bad digest"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    auth = SignedRequestAuth(
        public_key_id=Url(actor["publicKey"]["id"]),
        private_key=keys.private_key,
    )
    request = client.build_request("post", instance_inbox, json=payload)
    auth.sign_request(request)

    bad_date = format_datetime(
        datetime.now(tz=timezone.utc) - timedelta(days=1),
        usegmt=True,
    )
    request.headers["date"] = bad_date

    response = client.send(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    request = client.build_request("post", instance_inbox, json=payload)
    auth.sign_request(request)
    del request.headers["signature"]

    response = client.send(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    request = client.build_request(
        "post",
        instance_inbox,
        json=payload,
    )
    auth.sign_request(request)
    request.headers["signature"] = "bad=signature"

    response = client.send(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    request = client.build_request(
        "post",
        instance_inbox,
        json=payload,
    )
    auth.sign_request(request)
    request.headers["signature"] = 'keyId="id",signature="...",algorithm="unknown"'

    response = client.send(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    request = client.build_request(
        "post",
        instance_inbox,
        json=payload,
    )
    auth.sign_request(request)
    request.headers["signature"] = 'keyId="id",signature="..."'

    response = client.send(request)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_inbox_not_found(client: TestClient) -> None:
    payload = ap_create_note("remoteactor", "notfound")

    response = client.post("/actors/notfound/inbox", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_inbox_request_without_actor(
    client: TestClient, capsule_settings: CapsuleSettings
) -> None:
    instance_username = capsule_settings.username

    payload = ap_create_note("remoteactor", instance_username)
    payload.pop("actor")

    response = client.post(f"/actors/{instance_username}/inbox", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_inbox_failed_to_fetch_actor(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    actor_and_keypair: tuple[dict, RSAKeyPair],
    respx_mock: MockRouter,
) -> None:
    instance_username = capsule_settings.username
    instance_inbox = f"/actors/{instance_username}/inbox"
    actor, _ = actor_and_keypair
    actor_username = actor["preferredUsername"]

    mocked_response = Response(status_code=500)
    respx_mock.get(actor["id"]).mock(return_value=mocked_response)

    payload = ap_create_note(actor_username, instance_username)

    response = client.post(instance_inbox, json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED
