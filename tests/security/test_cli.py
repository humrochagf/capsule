from pathlib import Path

from typer.testing import CliRunner

from capsule.__main__ import build_cli
from tests.utils import setup_testing_env


def test_hashpwd(tmp_path: Path) -> None:
    with setup_testing_env(tmp_path):
        cli = build_cli()

    runner = CliRunner()

    result = runner.invoke(cli, ["security", "hashpwd", "test"])
    assert result.exit_code == 0
    assert result.stdout.startswith("$2b$12$")


def test_keypair(tmp_path: Path) -> None:
    with setup_testing_env(tmp_path):
        cli = build_cli()

    runner = CliRunner()

    result = runner.invoke(cli, ["security", "keypair"])
    assert result.exit_code == 0

    assert "-----BEGIN PRIVATE KEY-----" in result.stdout
    assert "-----END PRIVATE KEY-----" in result.stdout

    assert "-----BEGIN PUBLIC KEY-----" in result.stdout
    assert "-----END PUBLIC KEY-----" in result.stdout
