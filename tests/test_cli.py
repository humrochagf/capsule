from typer import Typer
from typer.testing import CliRunner

runner = CliRunner()


def test_syncdb(cli: Typer) -> None:
    result = runner.invoke(cli, ["syncdb"])

    assert result.exit_code == 0


def test_dropdb(cli: Typer) -> None:
    result = runner.invoke(cli, ["dropdb"])

    assert result.exit_code == 0
