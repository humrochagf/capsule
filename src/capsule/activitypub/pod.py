from wheke import Pod, ServiceConfig

from capsule.activitypub.routes import router
from capsule.activitypub.service import ActivityPubService, activitypub_service_factory

activitypub_pod = Pod(
    "activitypub",
    services=[ServiceConfig(ActivityPubService, activitypub_service_factory)],
    router=router,
)
