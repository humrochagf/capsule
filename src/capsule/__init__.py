from fastapi import FastAPI
from typer import Typer
from wheke import Wheke
from wheke_sqlmodel import sqlmodel_pod

from .activitypub.pod import activitypub_pod
from .api.pod import api_pod
from .database.pod import database_pod
from .logging import configure_logger
from .security.pod import security_pod
from .settings import CapsuleSettings


def build_wheke(
    settings: CapsuleSettings | type[CapsuleSettings] = CapsuleSettings,
) -> Wheke:
    wheke = Wheke(settings)

    wheke.add_pod(sqlmodel_pod)
    wheke.add_pod(security_pod)
    wheke.add_pod(database_pod)
    wheke.add_pod(activitypub_pod)
    wheke.add_pod(api_pod)

    return wheke


def build_cli(
    settings: CapsuleSettings | type[CapsuleSettings] = CapsuleSettings,
) -> Typer:
    return build_wheke(settings).create_cli()


def build_app(
    settings: CapsuleSettings | type[CapsuleSettings] = CapsuleSettings,
) -> FastAPI:
    configure_logger()

    return build_wheke(settings).create_app()
