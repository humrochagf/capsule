from typer.testing import CliRunner

from capsule.__main__ import cli as capsule_cli


def test_hashpwd() -> None:
    runner = CliRunner()

    result = runner.invoke(capsule_cli, ["security", "hashpwd", "test"])
    assert result.exit_code == 0
    assert result.stdout.startswith("$2b$12$")


def test_keypair() -> None:
    runner = CliRunner()

    result = runner.invoke(capsule_cli, ["security", "keypair"])
    assert result.exit_code == 0

    assert "-----BEGIN PRIVATE KEY-----" in result.stdout
    assert "-----END PRIVATE KEY-----" in result.stdout

    assert "-----BEGIN PUBLIC KEY-----" in result.stdout
    assert "-----END PUBLIC KEY-----" in result.stdout
