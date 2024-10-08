import asyncio

from rich.console import Console

from . import wheke
from .activitypub.service import get_activitypub_service
from .api.service import get_api_service
from .database.service import get_database_service

cli = wheke.create_cli()
console = Console(highlight=False)


@cli.command(short_help="Create collections and indexes")
def syncdb() -> None:
    console.print("Acquiring services to SyncDB...")

    activitypub = get_activitypub_service()
    console.print("ActivityPub service [green]acquired[/]")

    api = get_api_service()
    console.print("API service [green]acquired[/]")

    console.print("Syncing repositories...")

    asyncio.run(activitypub.setup_repositories())
    console.print("ActivityPub repositories [green]synced[/]")

    asyncio.run(api.setup_repositories())
    console.print("API repositories [green]synced[/]")

    console.print("SyncDB completed!")


@cli.command(short_help="Drop the whole database")
def dropdb() -> None:
    console.print("Acquiring Database to drop...")
    console.print("[yellow]This is a destructible operation[/]")

    database = get_database_service()
    asyncio.run(database.drop_db())

    console.print("DropDB completed!")
