from enum import Enum
from typing import Annotated

from fastapi import Form
from pydantic import AnyUrl


class AuthorizationForm:
    client_id: str
    scope: str
    redirect_uri: AnyUrl
    response_type: str


class GrantType(str, Enum):
    authorization_code = "authorization_code"
    client_credentials = "client_credentials"


class OAuth2AuthorizationCodeForm:
    grant_type: GrantType
    code: str
    client_id: str
    client_secret: str
    redirect_uri: AnyUrl
    code_verifier: str
    scope: str

    def __init__(
        self,
        *,
        grant_type: Annotated[GrantType, Form()],
        code: Annotated[str, Form()],
        client_id: Annotated[str, Form()],
        client_secret: Annotated[str, Form()],
        redirect_uri: Annotated[AnyUrl, Form()],
        code_verifier: Annotated[str, Form()] = "",
        scope: Annotated[str, Form()] = "",
    ) -> None:
        self.grant_type = grant_type
        self.code = code
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.code_verifier = code_verifier
        self.scopes = scope.split()
