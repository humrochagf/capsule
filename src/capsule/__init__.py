from wheke import Wheke

from capsule.activitypub.pod import activitypub_pod

wheke = Wheke()
wheke.add_pod(activitypub_pod)

app = wheke.create_app()
