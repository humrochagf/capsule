from wheke import Pod

from capsule.activitypub.routes import router

activitypub_pod = Pod(
    "activitypub",
    router=router,
)
