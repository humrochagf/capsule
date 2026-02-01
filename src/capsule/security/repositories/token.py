from sqlmodel import select
from wheke_sqlmodel import SQLModelRepository

from ..models import Token


class TokenRepository(SQLModelRepository):
    async def create_token(self, token: Token) -> None:
        async with self.db.session as session:
            session.add(token)
            await session.commit()
            await session.refresh(token)

    async def get_token(self, access_token: str) -> Token | None:
        async with self.db.session as session:
            stmt = select(Token).where(Token.token == access_token)
            return (await session.exec(stmt)).first()
