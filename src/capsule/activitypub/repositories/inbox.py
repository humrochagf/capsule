from collections.abc import AsyncGenerator

from sqlmodel import col, delete, select
from wheke_sqlmodel import SQLModelRepository

from capsule.activitypub.models import InboxEntry, InboxEntryStatus


class InboxRepository(SQLModelRepository):
    async def create_entry(self, entry: InboxEntry) -> InboxEntry:
        async with self.db.session as session:
            session.add(entry)
            await session.commit()
            await session.refresh(entry)

        return entry

    async def list_entries(
        self, status: InboxEntryStatus
    ) -> AsyncGenerator[InboxEntry]:
        async with self.db.session as session:
            stmt = select(InboxEntry).where(InboxEntry.status == status)
            for entry in await session.exec(stmt):
                yield entry

    async def update_entries_state(self, ids: list, status: InboxEntryStatus) -> None:
        async with self.db.session as session:
            stmt = select(InboxEntry).where(col(InboxEntry.id).in_(ids))
            for entry in await session.exec(stmt):
                entry.status = status
                session.add(entry)

            await session.commit()

    async def delete_entries(self) -> None:
        async with self.db.session as session:
            stmt = delete(InboxEntry)
            await session.exec(stmt)
            await session.commit()
