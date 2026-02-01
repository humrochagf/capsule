from datetime import UTC, datetime

from pydantic import AnyUrl
from sqlalchemy import Dialect
from sqlmodel import DateTime, String, TypeDecorator


class UrlType(TypeDecorator[AnyUrl]):
    impl = String(2048)
    cache_ok = True
    python_type = AnyUrl

    def process_bind_param(
        self,
        value: AnyUrl | None,
        dialect: Dialect,  # noqa: ARG002
    ) -> str | None:
        return str(value) if value else None

    def process_result_value(
        self,
        value: str | None,
        dialect: Dialect,  # noqa: ARG002
    ) -> AnyUrl | None:
        return AnyUrl(value) if value else None



class DateTimeType(TypeDecorator[datetime]):
    impl = DateTime(timezone=True)
    cache_ok = True
    python_type = datetime

    def process_bind_param(
        self,
        value: datetime | None,
        dialect: Dialect,  # noqa: ARG002
    ) -> datetime | None:
        return value.astimezone(UTC) if value else None

    def process_result_value(
        self,
        value: datetime | None,
        dialect: Dialect,  # noqa: ARG002
    ) -> datetime | None:
        return value.replace(tzinfo=UTC) if value else None
