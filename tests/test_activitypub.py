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
    capsule_settings.username = "test"
    capsule_settings.hostname = Url("https://example.com")

    acct = "acct:test@example.com"
    response = client.get(f"/.well-known/webfinger?resource={acct}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "subject": "acct:test@example.com",
        "aliases": ["https://example.com/@test", "https://example.com/users/test"],
        "links": [
            {
                "rel": "http://webfinger.net/rel/profile-page",
                "type": "text/html",
                "href": "https://example.com/@test",
            },
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": "https://example.com/users/test",
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


def test_inbox(client: TestClient) -> None:
    payload = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Person",
        "id": "https://social.example/alyssa/",
        "name": "Alyssa P. Hacker",
        "preferredUsername": "alyssa",
        "summary": "Lisp enthusiast hailing from MIT",
        "inbox": "https://social.example/alyssa/inbox/",
        "outbox": "https://social.example/alyssa/outbox/",
        "followers": "https://social.example/alyssa/followers/",
        "following": "https://social.example/alyssa/following/",
        "liked": "https://social.example/alyssa/liked/",
    }

    response = client.post("/inbox", data=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
