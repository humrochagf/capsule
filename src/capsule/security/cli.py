from rich.console import Console
from typer import Context, Typer
from wheke import get_container

from .services.auth import get_auth_service
from .utils import generate_rsa_keypair

cli = Typer(short_help="Security commands")
console = Console(highlight=False)


@cli.command()
def hashpwd(ctx: Context, password: str) -> None:
    container = get_container(ctx)

    console.print(get_auth_service(container).get_password_hash(password))


@cli.command()
def keypair() -> None:
    key_pair = generate_rsa_keypair()
    console.print(
        key_pair.private_key,
        key_pair.public_key,
        sep="",
        end="",
    )
