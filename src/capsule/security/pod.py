from wheke import Pod, ServiceConfig

from .cli import cli
from .routes import router
from .services import (
    AuthService,
    SignatureService,
    auth_service_factory,
    signature_service_factory,
)

security_pod = Pod(
    "security",
    services=[
        ServiceConfig(AuthService, auth_service_factory),
        ServiceConfig(SignatureService, signature_service_factory),
    ],
    router=router,
    cli=cli,
)
