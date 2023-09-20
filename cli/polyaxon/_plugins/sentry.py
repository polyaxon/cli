import logging

from typing import Dict, Optional

logger = logging.getLogger("polyaxon.cli")


def set_raven_client(options: Optional[Dict] = None) -> bool:
    from polyaxon import pkg, settings
    from polyaxon._services.values import PolyaxonServices

    cli_config = settings.CLI_CONFIG
    options = options or {}
    environment = options.get("environment")
    dsn = options.get("dsn")
    sample_rate = options.get("sample_rate", 0)
    if cli_config and cli_config.log_handler and cli_config.log_handler.decoded_dsn:
        dsn = dsn or cli_config.log_handler.decoded_dsn
        environment = environment or cli_config.log_handler.environment

    if dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            release=pkg.VERSION,
            environment=environment,
            server_name=PolyaxonServices.get_service_name(),
            sample_rate=sample_rate,
        )
        return True

    return False
