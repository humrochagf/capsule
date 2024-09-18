from wheke import Pod, ServiceConfig

from .service import DatabaseService, database_service_factory

database_pod = Pod(
    "database",
    services=[ServiceConfig(DatabaseService, database_service_factory)],
)
