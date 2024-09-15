import asyncio

from rich.console import Console

from capsule import wheke
from capsule.activitypub.service import get_activitypub_service
from capsule.database.service import get_database_service

cli = wheke.create_cli()
console = Console(highlight=False)


@cli.command(short_help="Create collections and indexes")
def syncdb() -> None:
    console.print("Acquiring services to SyncDB...")

    activitypub = get_activitypub_service()
    console.print("ActivityPub service [green]acquired[/]")

    console.print("Syncing repositories...")

    asyncio.run(activitypub.setup_repositories())
    console.print("ActivityPub repositories [green]synced[/]")

    console.print("SyncDB completed!")


@cli.command(short_help="Drop the whole database")
def dropdb() -> None:
    console.print("Acquiring Database to drop...")
    console.print("[yellow]This is a destructible operation[/]")

    database = get_database_service()
    asyncio.run(database.drop_db())

    console.print("DropDB completed!")
