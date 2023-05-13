from typing import Dict, Optional

from polyaxon.exceptions import handle_api_error
from polyaxon.logger import logger


def handle_client_error(
    e,
    message: Optional[str] = None,
    http_messages_mapping: Optional[Dict] = None,
    sys_exit: bool = False,
):
    handle_api_error(
        e=e,
        logger=logger,
        message=message,
        http_messages_mapping=http_messages_mapping,
        sys_exit=sys_exit,
    )
