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
