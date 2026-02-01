from sqlmodel import select
from wheke_sqlmodel import SQLModelService

from ..models import App


class AppRepository:
    db: SQLModelService

    def __init__(self, sqlmodel_service: SQLModelService) -> None:
        self.db = sqlmodel_service

    async def create_app(self, app: App) -> None:
        async with self.db.session as session:
            session.add(app)
            await session.commit()
            await session.refresh(app)

    async def get_app(self, client_id: str) -> App | None:
        async with self.db.session as session:
            stmt = select(App).where(App.client_id == client_id)
            return (await session.exec(stmt)).first()
