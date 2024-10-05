from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import Response
from pydantic_core import Url
from respx import MockRouter

from capsule.__about__ import __version__
from capsule.security.utils import RSAKeyPair, SignedRequestAuth
from capsule.settings import CapsuleSettings

from .utils import ap_actor, ap_create_note, ap_delete_actor, ap_follow, ap_unfollow


@pytest.mark.parametrize("hostname", ["http://example.com", "https://example.com"])
def test_well_known_host_meta(
    client: TestClient, capsule_settings: CapsuleSettings, hostname: str
) -> None:
    capsule_settings.hostname = Url(hostname)

    response = client.get("/.well-known/host-meta")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers.get("content-type") == "application/xrd+xml"

    template = f"{hostname}/.well-known/webfinger?resource={{uri}}"

    assert (
        response.content
        == (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0">\n'
            f'  <Link rel="lrdd" template="{template}"/>\n'
            "</XRD>"
        ).encode()
    )


@pytest.mark.parametrize("hostname", ["http://example.com", "https://example.com"])
def test_well_known_nodeinfo(
    client: TestClient, capsule_settings: CapsuleSettings, hostname: str
) -> None:
    capsule_settings.hostname = Url(hostname)

    response = client.get("/.well-known/nodeinfo")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "links": [
            {
                "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                "href": f"{hostname}/nodeinfo/2.0",
            }
        ],
    }


def test_well_known_webfinger(
    client: TestClient, capsule_settings: CapsuleSettings
) -> None:
    capsule_settings.username = "testuser"
    capsule_settings.hostname = Url("https://example.com")

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
    capsule_settings.hostname = Url("https://example.com")

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


def test_nodeinfo(client: TestClient) -> None:
    response = client.get("/nodeinfo/2.0")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "version": "2.0",
        "software": {
            "name": "capsule",
            "version": __version__,
        },
        "protocols": ["activitypub"],
        "services": {
            "outbound": [],
            "inbound": [],
        },
        "usage": {
            "users": {
                "total": 1,
            },
            "localPosts": 0,
        },
        "openRegistrations": False,
        "metadata": {},
    }


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


def test_actor_inbox(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    respx_mock: MockRouter,
    rsa_keypair: tuple[str, str],
) -> None:
    capsule_settings.username = "testuser"
    private_key, public_key = rsa_keypair
    remote_actor = ap_actor("remoteactor", public_key)

    mocked_response = Response(status_code=200, json=remote_actor)
    respx_mock.get(remote_actor["id"]).mock(return_value=mocked_response)

    payload = ap_create_note("remoteactor", "testuser", "Hello for the first time :)")

    response = client.post("/actors/testuser/inbox", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

    payload = ap_create_note("remoteactor", "testuser", "Hello for the second time :)")
    auth = SignedRequestAuth(
        public_key_id=Url(remote_actor["publicKey"]["id"]),
        private_key=private_key,
    )

    response = client.post("/actors/testuser/inbox", json=payload, auth=auth)
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_inbox_delete_actor(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    respx_mock: MockRouter,
    rsa_keypair: tuple[str, str],
) -> None:
    capsule_settings.username = "testuser"
    private_key, public_key = rsa_keypair
    remote_actor = ap_actor("deleteactor", public_key)

    mocked_response = Response(status_code=200, json=remote_actor)
    respx_mock.get(remote_actor["id"]).mock(return_value=mocked_response)

    payload = ap_create_note("deleteactor", "testuser")

    response = client.post("/actors/testuser/inbox", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

    payload = ap_delete_actor("deleteactor")
    auth = SignedRequestAuth(
        public_key_id=Url(remote_actor["publicKey"]["id"]),
        private_key=private_key,
    )

    response = client.post("/actors/testuser/inbox", json=payload, auth=auth)
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_actor_inbox_bad_signature(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    respx_mock: MockRouter,
    rsa_keypair: tuple[str, str],
) -> None:
    capsule_settings.username = "testuser"
    private_key, public_key = rsa_keypair
    remote_actor = ap_actor("remoteactor2", public_key)

    mocked_response = Response(status_code=200, json=remote_actor)
    respx_mock.get(remote_actor["id"]).mock(return_value=mocked_response)

    payload = ap_create_note("remoteactor2", "testuser", "Hello for the first time :)")

    response = client.post("/actors/testuser/inbox", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED

    payload = ap_create_note("remoteactor2", "testuser", "Bad hello!")

    response = client.post(
        "/actors/testuser/inbox",
        json=payload,
        headers={"digest": "bad digest"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    auth = SignedRequestAuth(
        public_key_id=Url(remote_actor["publicKey"]["id"]),
        private_key=private_key,
    )
    request = client.build_request(
        "post",
        "/actors/testuser/inbox",
        json=payload,
    )
    auth.sign_request(request)

    bad_date = format_datetime(
        datetime.now(tz=timezone.utc) - timedelta(days=1),
        usegmt=True,
    )
    request.headers["date"] = bad_date

    response = client.send(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    request = client.build_request(
        "post",
        "/actors/testuser/inbox",
        json=payload,
    )
    auth.sign_request(request)
    del request.headers["signature"]

    response = client.send(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    request = client.build_request(
        "post",
        "/actors/testuser/inbox",
        json=payload,
    )
    auth.sign_request(request)
    request.headers["signature"] = "bad=signature"

    response = client.send(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    request = client.build_request(
        "post",
        "/actors/testuser/inbox",
        json=payload,
    )
    auth.sign_request(request)
    request.headers["signature"] = 'keyId="id",signature="...",algorithm="unknown"'

    response = client.send(request)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    request = client.build_request(
        "post",
        "/actors/testuser/inbox",
        json=payload,
    )
    auth.sign_request(request)
    request.headers["signature"] = 'keyId="id",signature="..."'

    response = client.send(request)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_actor_inbox_not_found(client: TestClient) -> None:
    payload = ap_create_note("remoteactor", "testuser")

    response = client.post("/actors/notfound/inbox", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_actor_inbox_request_without_actor(
    client: TestClient, capsule_settings: CapsuleSettings
) -> None:
    capsule_settings.username = "testuser"

    payload = ap_create_note("remoteactor", "testuser")
    payload.pop("actor")

    response = client.post("/actors/testuser/inbox", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_actor_inbox_follow(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    respx_mock: MockRouter,
    rsa_keypair: tuple[str, str],
) -> None:
    capsule_settings.username = "testuser"
    private_key, public_key = rsa_keypair
    remote_actor = ap_actor("followactor", public_key)

    mocked_actor_response = Response(status_code=200, json=remote_actor)
    respx_mock.get(remote_actor["id"]).mock(return_value=mocked_actor_response)

    mocked_inbox_response = Response(status_code=202)
    respx_mock.post(remote_actor["inbox"]).mock(return_value=mocked_inbox_response)

    follow = ap_follow("followactor", "testuser")

    response = client.post("/actors/testuser/inbox", json=follow)
    assert response.status_code == status.HTTP_202_ACCEPTED

    unfollow = ap_unfollow("followactor", follow)
    auth = SignedRequestAuth(
        public_key_id=Url(remote_actor["publicKey"]["id"]),
        private_key=private_key,
    )

    response = client.post("/actors/testuser/inbox", json=unfollow, auth=auth)
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_actor_inbox_follow_failed_to_accept(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    respx_mock: MockRouter,
    rsa_keypair: tuple[str, str],
) -> None:
    capsule_settings.username = "testuser"
    _, public_key = rsa_keypair
    remote_actor = ap_actor("followerroractor", public_key)

    mocked_actor_response = Response(status_code=200, json=remote_actor)
    respx_mock.get(remote_actor["id"]).mock(return_value=mocked_actor_response)

    mocked_inbox_response = Response(status_code=500)
    respx_mock.post(remote_actor["inbox"]).mock(return_value=mocked_inbox_response)

    payload = ap_follow("followerroractor", "testuser")

    response = client.post("/actors/testuser/inbox", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_inbox_failed_to_fetch_actor(
    client: TestClient,
    capsule_settings: CapsuleSettings,
    respx_mock: MockRouter,
    rsa_keypair: tuple[str, str],
) -> None:
    capsule_settings.username = "testuser"
    _, public_key = rsa_keypair
    remote_actor = ap_actor("failedfetchactor", public_key)

    mocked_response = Response(status_code=500)
    respx_mock.get(remote_actor["id"]).mock(return_value=mocked_response)

    payload = ap_create_note("failedfetchactor", "testuser")

    response = client.post("/actors/testuser/inbox", json=payload)
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_actor_outbox(client: TestClient, capsule_settings: CapsuleSettings) -> None:
    capsule_settings.username = "testuser"

    response = client.get("/actors/testuser/outbox")

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "OrderedCollection",
        "totalItems": 0,
        "orderedItems": [],
    }


def test_actor_outbox_not_found(client: TestClient) -> None:
    response = client.get("/actors/notfound/outbox")

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


def test_system_sync_failed(
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
