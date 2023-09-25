from functools import wraps
from typing import Dict, Optional

from clipped.formatting import Printer

from polyaxon.exceptions import handle_api_error


def handle_cli_error(
    e,
    message: Optional[str] = None,
    http_messages_mapping: Optional[Dict] = None,
    sys_exit: bool = False,
):
    handle_api_error(
        logger=Printer,
        e=e,
        message=message,
        http_messages_mapping=http_messages_mapping,
        sys_exit=sys_exit,
    )


def handle_command_not_in_ce():
    Printer.error(
        "You are running Polyaxon CE which does not support this command!",
        sys_exit=True,
    )


def is_in_ce():
    from polyaxon import settings

    return not settings.CLI_CONFIG or settings.CLI_CONFIG.is_community


def not_in_ce(fn):
    """Decorator to show an error when a command not available in CE"""

    @wraps(fn)
    def not_in_ce_wrapper(*args, **kwargs):
        if is_in_ce():
            handle_command_not_in_ce()
        return fn(*args, **kwargs)

    return not_in_ce_wrapper
