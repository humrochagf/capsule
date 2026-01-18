import typer
from rich.console import Console
from wheke import get_container

from capsule.security.services.auth import get_auth_service

cli = typer.Typer(short_help="Security commands")
console = Console(highlight=False)


@cli.command()
def hashpwd(ctx: typer.Context, password: str) -> None:
    container = get_container(ctx)

    console.print(get_auth_service(container).get_password_hash(password))
