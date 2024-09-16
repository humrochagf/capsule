from uuid import uuid4


def ap_create_note(
    from_actor: str,
    to_actor: str,
    note_content: str = "Hello World",
    from_domain: str = "social.example",
    to_domain: str = "example.com",
) -> dict:
    return {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Create",
        "id": f"https://{from_domain}/actors/{from_actor}/activity/{uuid4()}",
        "to": [f"https://{to_domain}/actors/{to_domain}"],
        "actor": f"https://{from_domain}/actors/{from_actor}",
        "object": {
            "type": "Note",
            "id": f"https://{from_domain}/actors/{from_actor}/posts/{uuid4()}",
            "attributedTo": f"https://{from_domain}/actors/{from_actor}",
            "to": [f"https://{to_domain}/actors/{to_actor}"],
            "content": note_content,
        },
    }


def ap_actor(username: str, public_key: str, domain: str = "social.example") -> dict:
    return {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
        ],
        "id": f"https://{domain}/actors/{username}",
        "type": "Person",
        "name": f"{username.capitalize()} Name",
        "preferredUsername": username,
        "summary": f"{username.capitalize()} Summary",
        "inbox": f"https://{domain}/actors/{username}/inbox",
        "outbox": f"https://{domain}/actors/{username}/outbox",
        "publicKey": {
            "id": f"https://{domain}/actors/{username}#main-key",
            "owner": f"https://{domain}/actors/{username}",
            "publicKeyPem": public_key,
        },
        "icon": {
            "type": "Image",
            "mediaType": "image/jpeg",
            "url": f"https://{domain}/actors/{username}/icon",
        },
    }