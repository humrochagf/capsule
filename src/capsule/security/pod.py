from wheke import Pod, ServiceConfig

from .service import SecurityService, security_service_factory

security_pod = Pod(
    "security",
    services=[ServiceConfig(SecurityService, security_service_factory)],
)
