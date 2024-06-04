import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pydantic_core import Url

from capsule.settings import Settings


@pytest.mark.parametrize("hostname", ["http://example.com", "https://example.com"])
def test_nodeinfo(
    client: TestClient, capsule_settings: Settings, hostname: str
) -> None:
    capsule_settings.hostname = Url(hostname)

    response = client.get("/ap/.well-known/nodeinfo")

    assert response.json() == {
        "links": [
            {
                "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                "href": f"{hostname}/nodeinfo/2.0/",
            }
        ],
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

    response = client.post("/ap/inbox", data=payload)

    assert response.status_code == status.HTTP_202_ACCEPTED
