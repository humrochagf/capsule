from sqlalchemy.dialects.sqlite import insert
from sqlmodel import select
from wheke_sqlmodel import SQLModelRepository

from ..models import Authorization


class AuthorizationRepository(SQLModelRepository):
    async def upsert_authorization(self, authorization: Authorization) -> None:
        async with self.db.session as session:
            update_data = authorization.model_dump(
                exclude={"client_id", "created_at"},
            )
            stmt = insert(Authorization).values(authorization.model_dump())
            stmt = stmt.on_conflict_do_update(
                index_elements=["client_id"],
                set_=update_data,
            )
            await session.exec(stmt)
            await session.commit()

    async def get_authorization(self, code: str) -> Authorization | None:
        async with self.db.session as session:
            stmt = select(Authorization).where(Authorization.code == code)
            return (await session.exec(stmt)).first()
