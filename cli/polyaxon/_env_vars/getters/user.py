import sys

from clipped.formatting import Printer
from polyaxon._constants.globals import DEFAULT
from polyaxon._env_vars.getters._context import _ContextSource, _get_cache_source
from polyaxon.exceptions import PolyaxonClientException


def get_local_owner(is_cli: bool = False):
    owner, _ = _get_local_owner_context(is_cli=is_cli)
    return owner


def _get_local_owner_context(is_cli: bool = False):
    from polyaxon import settings
    from polyaxon._managers.user import UserConfigManager

    owner = None
    source = _ContextSource("default")
    if UserConfigManager.is_initialized():
        try:
            user_config = UserConfigManager.get_config()
            owner = user_config.organization if user_config else None
        except TypeError:
            Printer.error(
                "Found an invalid user config or user config cache, "
                "if you are using Polyaxon CLI please run: "
                "`polyaxon config purge --cache-only`",
                sys_exit=True,
            )
        if owner:
            source = _get_cache_source(UserConfigManager)

    if not owner and (not settings.CLI_CONFIG or settings.CLI_CONFIG.is_community):
        owner = DEFAULT

    if not owner:
        error = "An context owner (user or organization) is required."
        if is_cli:
            Printer.error(error)
            sys.exit(1)
        else:
            raise PolyaxonClientException(error)
    return owner, source
