import anyio
import uvicorn
from rich.console import Console
from svcs import Container
from typer import Context, Typer
from wheke import get_container
from wheke_sqlmodel import get_sqlmodel_service

from . import build_app, build_wheke
from .activitypub.service import get_activitypub_service
from .settings import CapsuleSettings

console = Console(highlight=False)


async def _syncdb(container: Container) -> None:
    console.print("Acquiring services to SyncDB...")

    sqlmodel = get_sqlmodel_service(container)
    activitypub = get_activitypub_service(container)

    console.print("Syncing repositories...")

    await sqlmodel.create_db()
    await activitypub.create_tables()

    await activitypub.ensure_main_actor()

    console.print("SyncDB completed!")


async def _dropdb(container: Container) -> None:
    console.print("Acquiring services to DropDB...")
    console.print("[yellow]This is a destructible operation[/]")

    activitypub = get_activitypub_service(container)
    sqlmodel = get_sqlmodel_service(container)

    console.print("Dropping repositories...")

    await activitypub.drop_tables()
    await sqlmodel.drop_db()

    console.print("DropDB completed!")


async def _start_server() -> None:  # pragma: no cover
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

    await server.serve()


def build_cli(
    settings: CapsuleSettings | type[CapsuleSettings] = CapsuleSettings,
) -> Typer:
    cli = build_wheke(settings).create_cli()

    @cli.command(short_help="Create the databases")
    def syncdb(ctx: Context) -> None:
        container = get_container(ctx)
        anyio.run(_syncdb, container)

    @cli.command(short_help="Drop the databases")
    def dropdb(ctx: Context) -> None:
        container = get_container(ctx)
        anyio.run(_dropdb, container)

    @cli.command(short_help="Start http server")
    def start_server() -> None:  # pragma: no cover
        anyio.run(_start_server)

    return cli


cli = build_cli()
