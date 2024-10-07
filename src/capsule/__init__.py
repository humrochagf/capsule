from wheke import Wheke

from .activitypub.pod import activitypub_pod
from .api.pod import api_pod
from .database.pod import database_pod
from .logging import configure_logger
from .security.pod import security_pod
from .settings import CapsuleSettings

configure_logger()

wheke = Wheke(CapsuleSettings)

wheke.add_pod(security_pod)
wheke.add_pod(database_pod)
wheke.add_pod(activitypub_pod)
wheke.add_pod(api_pod)

app = wheke.create_app()
