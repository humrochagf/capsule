from datetime import datetime
from enum import Enum
from typing import Any

from bson.objectid import ObjectId
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from capsule.utils import utc_now


class Activity(BaseModel):
    id: HttpUrl
    actor: HttpUrl
    type: str
    object: Any

    model_config = ConfigDict(extra="allow")

    @property
    def object_type(self) -> str | None:
        if isinstance(self.object, dict):
            return self.object.get("type", None)
        return None


class InboxEntryStatus(str, Enum):
    created = "created"
    synced = "synced"
    error = "error"
    not_implemented = "not_implemented"


class InboxEntry(BaseModel):
    id: ObjectId | None = Field(alias="_id", default=None, exclude=True)
    status: InboxEntryStatus = InboxEntryStatus.created
    activity: Activity
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(arbitrary_types_allowed=True)
