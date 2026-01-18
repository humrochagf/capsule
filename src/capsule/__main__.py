import asyncio

import uvicorn
from rich.console import Console
from typer import Context
from wheke import get_container

from . import build_app, build_cli
from .activitypub.service import get_activitypub_service
from .database.service import get_database_service
from .security.services import get_auth_service

cli = build_cli()
console = Console(highlight=False)


async def _syncdb(ctx: Context) -> None:
    console.print("Acquiring services to SyncDB...")

    with get_container(ctx) as container:
        activitypub = get_activitypub_service(container)
        console.print("ActivityPub service [green]acquired[/]")

        auth = get_auth_service(container)
        console.print("Auth service [green]acquired[/]")

        console.print("Syncing repositories...")

        await activitypub.setup_repositories()
        console.print("ActivityPub repositories [green]synced[/]")

        await auth.setup_repositories()
        console.print("Auth repositories [green]synced[/]")

    console.print("SyncDB completed!")


@cli.command(short_help="Create collections and indexes")
def syncdb(ctx: Context) -> None:
    asyncio.run(_syncdb(ctx))


@cli.command(short_help="Drop the whole database")
def dropdb(ctx: Context) -> None:
    container = get_container(ctx)

    console.print("Acquiring Database to drop...")
    console.print("[yellow]This is a destructible operation[/]")

    database = get_database_service(container)
    asyncio.run(database.drop_db())

    console.print("DropDB completed!")


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

    asyncio.run(server.serve())
