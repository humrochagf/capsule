import base64
from collections import namedtuple
from collections.abc import Generator
from datetime import datetime, timezone
from email.utils import format_datetime
from typing import cast

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    generate_private_key,
)
from httpx import Auth, Request, Response
from pydantic import HttpUrl

from .models import HttpSignatureInfo

RSAKeyPair = namedtuple("RSAKeyPair", ["private_key", "public_key"])


def calculate_sha_256_digest(data: bytes) -> str:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)

    return "SHA-256=" + base64.b64encode(digest.finalize()).decode("ascii")


def generate_rsa_keypair() -> RSAKeyPair:
    private_key = generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    private_key_serialized = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")

    public_key_serialized = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
    )

    return RSAKeyPair(private_key_serialized, public_key_serialized)


class SignedRequestAuth(Auth):
    public_key_id: HttpUrl
    private_key: str

    def __init__(self, public_key_id: HttpUrl, private_key: str) -> None:
        self.public_key_id = public_key_id
        self.private_key = private_key

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        self.sign_request(request)
        yield request

    def sign_request(self, request: Request) -> None:
        request.headers["(request-target)"] = (
            f"{request.method.lower()} {request.url.path}"
        )
        request.headers["Host"] = request.url.host
        request.headers["Date"] = format_datetime(
            datetime.now(tz=timezone.utc),
            usegmt=True,
        )
        request.headers["Content-Type"] = request.headers.get(
            "Content-Type", "application/activity+json"
        )

        headers_to_sign = ["(request-target)", "Host", "Date", "Content-Type"]

        if request.content is not None:
            request.headers["Digest"] = calculate_sha_256_digest(request.content)
            headers_to_sign.append("Digest")

        data_to_sign = "\n".join(
            f"{header.lower()}: {request.headers[header]}" for header in headers_to_sign
        ).encode("utf8")
        private_key_instance: RSAPrivateKey = cast(
            RSAPrivateKey,
            serialization.load_pem_private_key(
                self.private_key.encode("ascii"), password=None
            ),
        )
        signature = private_key_instance.sign(
            data_to_sign, padding.PKCS1v15(), hashes.SHA256()
        )

        signature_info = HttpSignatureInfo(
            keyid=str(self.public_key_id),
            headers=headers_to_sign,
            signature=signature,
            algorithm="rsa-sha256",
        )

        request.headers["Signature"] = signature_info.compiled_signature

        del request.headers["(request-target)"]
