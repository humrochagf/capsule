from sqlmodel import select
from wheke_sqlmodel import SQLModelService

from ..models import Token


class TokenRepository:
    db: SQLModelService

    def __init__(self, sqlmodel_service: SQLModelService) -> None:
        self.db = sqlmodel_service

    async def create_token(self, token: Token) -> None:
        async with self.db.session as session:
            session.add(token)
            await session.commit()
            await session.refresh(token)

    async def get_token(self, access_token: str) -> Token | None:
        async with self.db.session as session:
            stmt = select(Token).where(Token.token == access_token)
            return (await session.exec(stmt)).first()
