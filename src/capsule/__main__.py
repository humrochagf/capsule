import anyio
import uvicorn
from rich.console import Console
from svcs import Container
from typer import Context
from wheke import get_container

from . import build_app, build_cli
from .activitypub.service import get_activitypub_service
from .database.service import get_database_service

cli = build_cli()
console = Console(highlight=False)


async def _syncdb(container: Container) -> None:
    console.print("Acquiring services to SyncDB...")

    activitypub = get_activitypub_service(container)
    console.print("ActivityPub service [green]acquired[/]")

    console.print("Syncing repositories...")

    await activitypub.create_tables()
    console.print("ActivityPub repositories [green]synced[/]")

    console.print("SyncDB completed!")


async def _dropdb(container: Container) -> None:
    console.print("Acquiring services to DropDB...")
    console.print("[yellow]This is a destructible operation[/]")

    database = get_database_service(container)
    console.print("Database service [green]acquired[/]")

    activitypub = get_activitypub_service(container)
    console.print("ActivityPub service [green]acquired[/]")

    console.print("Dropping repositories...")

    await database.drop_db()

    await activitypub.drop_tables()
    console.print("ActivityPub repositories [green]dropped[/]")

    console.print("DropDB completed!")


@cli.command(short_help="Create collections and indexes")
def syncdb(ctx: Context) -> None:
    container = get_container(ctx)
    anyio.run(_syncdb, container)


@cli.command(short_help="Drop the whole database")
def dropdb(ctx: Context) -> None:
    container = get_container(ctx)
    anyio.run(_dropdb, container)


@cli.command(short_help="Start http server")
def start_server() -> None:  # pragma: no cover
    config = uvicorn.Config(
        build_app,
        host="0.0.0.0",
        port=9292,
        log_level="info",
        workers=3,
        factory=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )

    server = uvicorn.Server(config)

    console.print("Starting server...")

    anyio.run(server.serve)
