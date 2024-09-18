from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import cast

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from fastapi import Request
from wheke import get_service

from .exception import VerificationBadFormatError, VerificationError
from .models import HttpSignatureInfo
from .utils import calculate_sha_256_digest


class SecurityService:
    async def verify_request(self, request: Request, public_key: str) -> None:
        if "digest" in request.headers:
            expected_digest = calculate_sha_256_digest(await request.body())

            if request.headers["digest"] != expected_digest:
                msg = "Bad digest"
                raise VerificationBadFormatError(msg)

        if "date" in request.headers:
            expiration = parsedate_to_datetime(request.headers["date"]).astimezone(
                timezone.utc
            )

            if datetime.now(timezone.utc) - expiration > timedelta(seconds=60):
                msg = "Expired digest"
                raise VerificationBadFormatError(msg)

        if "signature" not in request.headers:
            msg = "Missing signature"
            raise VerificationBadFormatError(msg)

        try:
            signature_info = HttpSignatureInfo.from_compiled_signature(
                request.headers["signature"]
            )
        except (KeyError, ValueError) as exc:
            msg = "Bad signature"
            raise VerificationBadFormatError(msg) from exc

        if signature_info.algorithm not in ["rsa-sha256", "hs2019"]:
            msg = "Unknown signature algorithm"
            raise VerificationBadFormatError(msg)

        headers = {}

        for header in signature_info.headers:
            if header == "(request-target)":
                value = f"{request.method.lower()} {request.url.path}"
            else:
                value = request.headers[header]

            headers[header] = value

        data = "\n".join(f"{k}: {v}" for k, v in headers.items())

        self.verify_signature(signature_info.signature, data, public_key)

    def verify_signature(self, signature: bytes, data: str, public_key: str) -> None:
        pk_instance: RSAPublicKey = cast(
            RSAPublicKey,
            serialization.load_pem_public_key(public_key.encode("ascii")),
        )

        try:
            pk_instance.verify(
                signature, data.encode("utf8"), padding.PKCS1v15(), hashes.SHA256()
            )
        except InvalidSignature as exc:
            msg = "Invalid Signature"
            raise VerificationError(msg) from exc


def security_service_factory() -> SecurityService:
    return SecurityService()


def get_security_service() -> SecurityService:
    return get_service(SecurityService)
