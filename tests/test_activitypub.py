import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pydantic_core import Url

from capsule.__about__ import __version__
from capsule.settings import CapsuleSettings


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
def test_user_actor(
    client: TestClient, capsule_settings: CapsuleSettings, url: str, accept: str
) -> None:
    capsule_settings.username = "testuser"
    capsule_settings.hostname = Url("https://example.com")
    capsule_settings.name = "Test Name"
    capsule_settings.summary = "Test Summary"

    response = client.get(url, headers={"Accept": accept})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": "https://example.com/actors/testuser",
        "type": "Person",
        "name": "Test Name",
        "preferredUsername": "testuser",
        "summary": "Test Summary",
        "inbox": "https://example.com/actors/testuser/inbox",
        "outbox": "https://example.com/actors/testuser/outbox",
        "followers": "https://example.com/actors/testuser/followers",
        "following": "https://example.com/actors/testuser/following",
    }


def test_user_actor_not_found(client: TestClient) -> None:
    response = client.get("/actors/notfound")

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_inbox(client: TestClient, capsule_settings: CapsuleSettings) -> None:
    capsule_settings.username = "testuser"

    payload = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Create",
        "id": "https://social.example/alyssa/posts/a29a6843-9feb-4c74-a7f7-081b9c9201d3",
        "to": ["https://example.com/actors/testuser"],
        "actor": "https://social.example/alyssa/",
        "object": {
            "type": "Note",
            "id": "https://social.example/alyssa/posts/49e2d03d-b53a-4c4c-a95c-94a6abf45a19",
            "attributedTo": "https://social.example/alyssa/",
            "to": ["https://example.com/actors/testuser"],
            "content": "Say, did you finish reading that book I lent you?",
        },
    }

    response = client.post("/actors/testuser/inbox", data=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED


def test_user_inbox_not_found(client: TestClient) -> None:
    payload = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Create",
        "id": "https://social.example/alyssa/posts/a29a6843-9feb-4c74-a7f7-081b9c9201d3",
        "to": ["https://example.com/actors/testuser"],
        "actor": "https://social.example/alyssa/",
        "object": {
            "type": "Note",
            "id": "https://social.example/alyssa/posts/49e2d03d-b53a-4c4c-a95c-94a6abf45a19",
            "attributedTo": "https://social.example/alyssa/",
            "to": ["https://example.com/actors/testuser"],
            "content": "Say, did you finish reading that book I lent you?",
        },
    }

    response = client.post("/actors/notfound/inbox", data=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND
