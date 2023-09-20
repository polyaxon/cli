import sys
import uuid

from typing import Optional

from clipped.formatting import Printer
from clipped.utils.enums import get_enum_value
from clipped.utils.tz import now
from clipped.utils.versions import clean_version_for_compatibility
from urllib3.exceptions import HTTPError

from polyaxon import pkg
from polyaxon._cli.errors import handle_cli_error
from polyaxon._constants.globals import NO_AUTH
from polyaxon._managers.auth import AuthConfigManager
from polyaxon._managers.cli import CliConfigManager
from polyaxon._managers.user import UserConfigManager
from polyaxon._schemas.client import ClientConfig
from polyaxon._schemas.installation import V1Installation
from polyaxon._services.values import PolyaxonServices
from polyaxon.client import PolyaxonClient
from polyaxon.exceptions import ApiException


def session_expired():
    AuthConfigManager.purge()
    UserConfigManager.purge()
    CliConfigManager.purge()
    Printer.print("Session has expired, please try again!")
    sys.exit(1)


def get_server_installation(polyaxon_client=None):
    polyaxon_client = polyaxon_client or PolyaxonClient(ClientConfig(retries=0))
    try:
        return polyaxon_client.versions_v1.get_installation(_request_timeout=5)
    except ApiException as e:
        if e.status == 403:
            session_expired()
        handle_cli_error(e, message="Could not get server version.")
    except HTTPError:
        Printer.error(
            "Could not connect to remote server to fetch installation version.",
        )


def get_installation_key(key: str) -> str:
    if not key:
        installation = CliConfigManager.get_value("installation") or V1Installation()
        key = installation.key or uuid.uuid4().hex
        installation.key = key
        if not CliConfigManager.is_initialized():
            CliConfigManager.reset(installation=installation)
    return key


def get_compatibility(
    key: str,
    service: str,
    version: str,
    is_cli: bool = True,
    set_config: bool = True,
    polyaxon_client: Optional[PolyaxonClient] = None,
):
    key = get_installation_key(key)
    try:
        version = clean_version_for_compatibility(version)
    except Exception as e:
        if set_config:
            CliConfigManager.reset(last_check=now())
        if is_cli:
            handle_cli_error(
                e,
                message="Could not parse the version {}.".format(version),
            )
    config = (
        ClientConfig.patch_from(polyaxon_client.config, token=None, retries=0)
        if polyaxon_client and polyaxon_client.config
        else ClientConfig(use_cloud_host=True, verify_ssl=False, retries=0)
    )
    polyaxon_client = PolyaxonClient(config=config, token=NO_AUTH)
    try:
        return polyaxon_client.versions_v1.get_compatibility(
            uuid=key,
            service=get_enum_value(service),
            version=version,
            _request_timeout=1,
        )
    except ApiException as e:
        if e.status == 403 and is_cli:
            Printer.error("Could not reach the compatibility API.")
            return
        if set_config:
            CliConfigManager.reset(last_check=now())
        if is_cli:
            handle_cli_error(
                e,
                message="Could not reach the compatibility API.",
            )
    except HTTPError:
        if set_config:
            CliConfigManager.reset(last_check=now())
        if is_cli:
            Printer.error(
                "Could not connect to remote server to fetch compatibility versions.",
            )
    except Exception as e:
        if set_config:
            CliConfigManager.reset(last_check=now())
        if is_cli:
            Printer.error(
                "Unexpected error %s, "
                "could not connect to remote server to fetch compatibility versions."
                % e,
            )


def get_log_handler(polyaxon_client=None):
    polyaxon_client = polyaxon_client or PolyaxonClient()
    try:
        return polyaxon_client.versions_v1.get_log_handler()
    except ApiException as e:
        if e.status == 403:
            session_expired()
        CliConfigManager.reset(last_check=now())
        handle_cli_error(e, message="Could not get cli version.")
    except HTTPError:
        CliConfigManager.reset(last_check=now())
        Printer.error("Could not connect to remote server to fetch log handler.")


def set_versions_config(
    polyaxon_client=None,
    set_installation: bool = True,
    set_compatibility: bool = True,
    set_handler: bool = False,
    service=PolyaxonServices.CLI,
    version=pkg.VERSION,
    key: Optional[str] = None,
    is_cli: bool = True,
):
    from polyaxon import settings

    polyaxon_client = polyaxon_client or PolyaxonClient(
        ClientConfig.patch_from(settings.CLIENT_CONFIG, retries=0)
    )
    server_installation = None
    if set_installation:
        server_installation = get_server_installation(polyaxon_client=polyaxon_client)
        if not key and server_installation and server_installation.key:
            key = server_installation.key
    compatibility = None
    if set_compatibility:
        compatibility = get_compatibility(
            key=key,
            service=service,
            version=version,
            is_cli=is_cli,
            polyaxon_client=polyaxon_client if polyaxon_client.config.token else None,
        )
    log_handler = None
    if set_handler:
        log_handler = get_log_handler(polyaxon_client=polyaxon_client)
    return CliConfigManager.reset(
        last_check=now(),
        current_version=version,
        installation=server_installation.to_dict() if server_installation else {},
        compatibility=compatibility.to_dict() if compatibility else {},
        log_handler=log_handler.to_dict() if log_handler else {},
    )


def ensure_cli_config():
    from polyaxon import settings

    if not settings.CLI_CONFIG or not settings.CLI_CONFIG.installation:
        settings.CLI_CONFIG = set_versions_config(set_compatibility=False)
