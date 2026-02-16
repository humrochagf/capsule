from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, HttpUrl
from pydantic_core import to_jsonable_python
from sqlalchemy import Dialect
from sqlmodel import JSON, Field, SQLModel, TypeDecorator

from capsule.types import DateTimeType
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


class ActivityType(TypeDecorator[Activity]):
    impl = JSON
    cache_ok = True
    python_type = Activity

    def process_bind_param(
        self,
        value: BaseModel | None,
        dialect: Dialect,  # noqa: ARG002
    ) -> dict | None:
        return to_jsonable_python(value) if value else None

    def process_result_value(
        self,
        value: dict | None,
        dialect: Dialect,  # noqa: ARG002
    ) -> Activity | None:
        return Activity(**value) if value else None


class InboxEntryStatus(StrEnum):
    created = "created"
    synced = "synced"
    error = "error"
    not_implemented = "not_implemented"


class InboxEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    status: InboxEntryStatus = InboxEntryStatus.created
    activity: Activity = Field(sa_type=ActivityType)
    created_at: datetime = Field(default_factory=utc_now, sa_type=DateTimeType)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTimeType,
        sa_column_kwargs={"onupdate": utc_now},
    )
