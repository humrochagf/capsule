import typer
from rich.console import Console

from capsule.security.services.auth import get_auth_service

cli = typer.Typer(short_help="Security commands")
console = Console(highlight=False)


@cli.command()
def hashpwd(password: str) -> None:
    console.print(get_auth_service().get_password_hash(password))
