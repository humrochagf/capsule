import pytest
from fastapi.testclient import TestClient
from pydantic_core import Url

from capsule.settings import Settings


@pytest.mark.parametrize("hostname", ["http://example.com", "https://example.com"])
def test_well_known_nodeinfo(
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
