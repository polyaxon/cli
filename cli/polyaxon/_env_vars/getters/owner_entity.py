import sys

from clipped.formatting import Printer
from clipped.utils.strings import validate_slug

from polyaxon._constants.globals import DEFAULT
from polyaxon._env_vars.getters.user import get_local_owner
from polyaxon._utils.fqn_utils import get_entity_info
from polyaxon.exceptions import PolyaxonClientException, PolyaxonSchemaError


def resolve_entity_info(entity: str, entity_name: str, is_cli: bool = False):
    from polyaxon import settings

    if not entity:
        message = "Please provide a valid {}!".format(entity_name)
        if is_cli:
            Printer.error(message)
            sys.exit(1)
        else:
            raise PolyaxonClientException(message)

    owner, entity_value = get_entity_info(entity)

    if not owner:
        owner = get_local_owner(is_cli=is_cli)

    if not owner and (not settings.CLI_CONFIG or settings.CLI_CONFIG.is_community):
        owner = DEFAULT

    if not owner:
        owner = settings.AUTH_CONFIG.username if settings.AUTH_CONFIG else None

    if not all([owner, entity_value]):
        message = "Please provide a valid {}.".format(entity_name)
        if is_cli:
            Printer.error(message)
            sys.exit(1)
        else:
            raise PolyaxonClientException(message)
    if owner and not validate_slug(owner):
        raise PolyaxonSchemaError(
            "Received an invalid owner, received the value: `{}`".format(owner)
        )

    if entity_value and not validate_slug(entity_value):
        raise PolyaxonSchemaError(
            "Received an invalid {}, received the value: `{}`".format(
                entity_name, entity_value
            )
        )
    return owner, entity_value
