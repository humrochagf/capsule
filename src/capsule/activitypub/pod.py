from wheke import Pod

from capsule.activitypub.routes import router
from capsule.activitypub.service import ActivityPubService, activitypub_service_factory

activitypub_pod = Pod(
    "activitypub",
    services=[(ActivityPubService, activitypub_service_factory)],
    router=router,
)
