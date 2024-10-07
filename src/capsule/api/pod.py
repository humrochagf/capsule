from wheke import Pod, ServiceConfig

from .routes import router
from .service import APIService, api_service_factory

api_pod = Pod(
    "api",
    router=router,
    services=[ServiceConfig(APIService, api_service_factory)],
)
