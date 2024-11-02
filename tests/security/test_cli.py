from typer.testing import CliRunner

from capsule.__main__ import cli as capsule_cli


def test_hashpwd() -> None:
    runner = CliRunner()

    result = runner.invoke(capsule_cli, ["security", "hashpwd", "test"])
    assert result.exit_code == 0
    assert result.stdout.startswith("$2b$12$")
