from wheke import Wheke

from capsule.activitypub.pod import activitypub_pod
from capsule.settings import CapsuleSettings

wheke = Wheke(CapsuleSettings)
wheke.add_pod(activitypub_pod)

app = wheke.create_app()
