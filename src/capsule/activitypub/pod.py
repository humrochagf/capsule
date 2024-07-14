from wheke import Pod, ServiceConfig

from .routes import router
from .service import ActivityPubService, activitypub_service_factory

activitypub_pod = Pod(
    "activitypub",
    services=[ServiceConfig(ActivityPubService, activitypub_service_factory)],
    router=router,
)
