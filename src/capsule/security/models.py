from base64 import b64decode, b64encode

from pydantic import BaseModel


class HttpSignatureInfo(BaseModel):
    algorithm: str
    headers: list[str]
    signature: bytes
    keyid: str

    @property
    def headers_str(self) -> str:
        return " ".join(header.lower() for header in self.headers)

    @property
    def compiled_signature(self) -> str:
        return (
            f'keyId="{self.keyid}"'
            f',headers="{self.headers_str}"'
            f',signature="{b64encode(self.signature).decode("ascii")}"'
            f',algorithm="{self.algorithm}"'
        )

    @classmethod
    def from_compiled_signature(cls, signature: str) -> "HttpSignatureInfo":
        parts = {}

        for part in signature.split(","):
            key, value = part.split("=", 1)
            value = value.strip('"')
            parts[key.lower()] = value

        return HttpSignatureInfo(
            headers=parts["headers"].split(),
            signature=b64decode(parts["signature"]),
            algorithm=parts["algorithm"],
            keyid=parts["keyid"],
        )
