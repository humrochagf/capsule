from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from capsule.utils import utc_now

from .utils import generate_token


class Token(BaseModel):
    app_id: UUID
    scopes: str
    token: str = Field(default_factory=generate_token)

    created_at: datetime = Field(default_factory=utc_now)
