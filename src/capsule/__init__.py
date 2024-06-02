from wheke import Wheke

from .activitypub.pod import activitypub_pod

wheke = Wheke()
wheke.add_pod(activitypub_pod)

app = wheke.create_app()
