from fastapi import status
from fastapi.testclient import TestClient

from capsule.settings import CapsuleSettings


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