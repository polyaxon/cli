from vents.config import AppConfig
from vents.settings import create_app

from polyaxon._config.parser import ConfigParser
from polyaxon._contexts import paths as ctx_paths
from polyaxon.exceptions import PolyaxonConnectionError
from polyaxon.logger import logger

CONNECTION_CONFIG = create_app(
    config=AppConfig(
        project_name="Polyaxon",
        project_url="https://polyaxon.com/",
        project_icon="https://cdn.polyaxon.com/static/v1/images/logo_small.png",
        env_prefix="POLYAXON",
        context_path=ctx_paths.CONTEXT_ROOT,
        logger=logger,
        exception=PolyaxonConnectionError,
        config_parser=ConfigParser,
    )
)

from polyaxon._connections.kinds import V1ConnectionKind
from polyaxon._connections.schemas import (
    V1BucketConnection,
    V1ClaimConnection,
    V1Connection,
    V1ConnectionResource,
    V1GitConnection,
    V1HostConnection,
    V1HostPathConnection,
)
