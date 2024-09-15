from pydantic import BaseModel


class HttpSignatureInfo(BaseModel):
    algorithm: str
    headers: list[str]
    signature: bytes
    keyid: str
