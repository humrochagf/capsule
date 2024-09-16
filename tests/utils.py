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
        "id": f"https://{from_domain}/{from_actor}/activity/{uuid4()}",
        "to": [f"https://{to_domain}/actors/{to_domain}"],
        "actor": f"https://{from_domain}/{from_actor}/",
        "object": {
            "type": "Note",
            "id": f"https://{from_domain}/{from_actor}/posts/{uuid4()}",
            "attributedTo": f"https://{from_domain}/{from_actor}/",
            "to": [f"https://{to_domain}/actors/{to_actor}"],
            "content": note_content,
        },
    }
