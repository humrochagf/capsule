from wheke import Pod

from .routes import router

activitypub_pod = Pod(
    "activitypub",
    router=router,
)
